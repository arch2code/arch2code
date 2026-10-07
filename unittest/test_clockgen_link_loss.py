#!/usr/bin/env python3
"""Regression for the generated Verilator wrapper's `clock_gen` function
(`templates/systemc/module_hdl_wrapper.py`) in lockstep co-simulation.

Before the fix, once the process-wide lockstep gate closed, `clock_gen`
looped on `socketSyncWaitClockEdge()` forever and never re-checked gating.
When a Python peer drops its sync-link connection, `free_run_after_link_loss()`
(`common/systemc/socketSync.cpp`) turns gating off and notifies the wait event
only once, so a pre-fix wrapper's clock stops advancing for good while
`sc_time` itself keeps advancing. The fix re-checks `socketSyncTimeGated()`
after every edge wait and falls back to free-running `wait(half)` once gating
ends.

`unittest/fixtures/clockgen-link-loss` is a trimmed copy of the
`axiSocketSlave` example: an AXI producer/socket pair drives the process-wide
lockstep gate, and a `dummyVl` block (the only `hasVl` block, plain `clk`/
`rst_n`, no data ports) is the `--vlInst` substituted DUT whose `clock_gen`
thread is under test. The `axiSocketSlave.py` sidecar drops its sync-link
socket after `CLOCKGEN_LINK_LOSS_AFTER_QUANTA` quanta; the test then counts
`dummyVl`'s traced `clk` transitions (`--vlTrace`, a plain VerilatedVcdSc
dump) after that timestamp. A frozen clock (the pre-fix defect) yields zero;
a live one yields hundreds within the run's `--scTimeLimit`.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'clockgen-link-loss')

# The AXI sequence completes on its own well before --scTimeLimit; dropping
# the link after just 1 quantum keeps it interrupted mid-sequence, so the run
# always ends via the time limit rather than a clean test-complete.
LINK_LOSS_AFTER_QUANTA = 1
SC_TIME_LIMIT_US = 2

# A run interrupted this way always exits 1 (the interrupted AXI sequence
# trips a final() Q_ASSERT); anything else is a crash or an unrelated
# failure, not the condition this test measures.
EXPECTED_EXIT_CODE = 1

# A healthy run logs close to one edge per half period (~999 here); the
# pre-fix defect logs exactly zero. The threshold only needs to sit well
# clear of zero to catch the defect, with headroom for scheduling jitter.
MIN_POST_LOSS_TOGGLES = 100

DROP_LINE_RE = re.compile(
    r"dropping sync link after \d+ quanta \(sc_time_ns=(\d+)\)")

# VCD timescale unit -> multiplier onto picoseconds.
_TIMESCALE_UNITS_TO_PS = {'fs': 0.001, 'ps': 1, 'ns': 1000, 'us': 1000000}


def copy_fixture(project):
    shutil.copytree(
        FIXTURE, project,
        ignore=shutil.ignore_patterns('*.db', '*.db-*', '.gen', 'build'))


def env():
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    return e


def make(target, project, e, cwd=None, extra=()):
    cmd = ['make', '-C', cwd or project, f'REPO_ROOT={project}',
           f'A2C_ROOT={base_dir}', '-j8']
    cmd.extend(extra)
    cmd.append(target)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=e)


def require_make(target, project, e, cwd=None, extra=()):
    result = make(target, project, e, cwd=cwd, extra=extra)
    if result.returncode != 0:
        raise RuntimeError(
            f"make {target} failed:\n{result.stdout}\n{result.stderr}")
    return result


def _clk_id_and_timescale_ps(vcd_path):
    """The single-bit VCD identifier bound to a `clk` signal (the wrapper and
    its nested `dut` scope both declare one, aliased to the same identifier)
    and the file's timescale, converted to picoseconds."""
    clk_id = None
    scale_ps = None
    with open(vcd_path) as f:
        for line in f:
            if clk_id is None:
                m = re.match(r'\s*\$var wire 1 (\S+) clk \$end', line)
                if m:
                    clk_id = m.group(1)
            if scale_ps is None:
                m = re.match(r'\s*\$timescale\s+(\d+)\s*(\w+)\s*\$end', line)
                if m:
                    scale_ps = int(m.group(1)) * _TIMESCALE_UNITS_TO_PS[m.group(2)]
            if line.strip() == '$enddefinitions $end':
                break
    if clk_id is None:
        raise RuntimeError(f"{vcd_path}: no single-bit 'clk' $var found")
    if scale_ps is None:
        raise RuntimeError(f"{vcd_path}: no $timescale found")
    return clk_id, scale_ps


def _count_post_loss_clk_toggles(vcd_path, link_loss_ps):
    clk_id, scale_ps = _clk_id_and_timescale_ps(vcd_path)
    toggle_re = re.compile(r'^[01]' + re.escape(clk_id) + r'$')
    t = 0
    count = 0
    with open(vcd_path) as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('#'):
                t = int(line[1:]) * scale_ps
                continue
            if toggle_re.match(line) and t > link_loss_ps:
                count += 1
    return count


def _run():
    e = env()
    tmp = tempfile.mkdtemp(prefix='clockgen_link_loss_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'axiSocketSlave')
        copy_fixture(project)

        require_make('db', project, e)
        require_make('newmodule', project, e)
        require_make('gen', project, e)

        rundir = os.path.join(project, 'rundir')
        require_make('all', project, e, cwd=rundir,
                      extra=['VL_DUT=1', 'CCACHE_DISABLE=1'])

        binPath = os.path.join(rundir, 'build', 'run')
        if not os.path.exists(binPath):
            print(f"FAIL: build did not produce {binPath}")
            return False

        runEnv = e.copy()
        runEnv['PYTHONPATH'] = os.path.join(base_dir, 'pysrc')
        runEnv['CLOCKGEN_LINK_LOSS_AFTER_QUANTA'] = str(LINK_LOSS_AFTER_QUANTA)
        result = subprocess.run(
            ['./run', 'axiSocket', '--vlInst', 'axiSocketSlave_tb.u_dummyVl',
             '--vlTrace', '--scTimeLimit', str(SC_TIME_LIMIT_US)],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.join(rundir, 'build'), env=runEnv)

        if result.returncode != EXPECTED_EXIT_CODE:
            print(f"FAIL: run exited {result.returncode}, expected "
                  f"{EXPECTED_EXIT_CODE}; stdout:\n{result.stdout}\n"
                  f"stderr:\n{result.stderr}")
            return False

        match = DROP_LINE_RE.search(result.stdout)
        if not match:
            print("FAIL: sidecar never logged its sync-link drop; "
                  f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            return False
        link_loss_ps = int(match.group(1)) * 1000

        vcdPath = os.path.join(rundir, 'build', 'simx.vcd')
        if not os.path.exists(vcdPath):
            print(f"FAIL: run did not produce {vcdPath}")
            return False
        toggles = _count_post_loss_clk_toggles(vcdPath, link_loss_ps)

        if toggles < MIN_POST_LOSS_TOGGLES:
            print(f"FAIL: dummyVl's clk logged only {toggles} edge(s) after "
                  f"the sync-link drop at {link_loss_ps}ps (need >= "
                  f"{MIN_POST_LOSS_TOGGLES}); clock_gen froze the clock "
                  f"instead of falling back to free-running, reproducing the "
                  f"pre-fix defect")
            return False

        print(f"PASS: dummyVl's clk logged {toggles} edges after the "
              f"sync-link drop at {link_loss_ps}ps, so clock_gen fell back "
              f"to free-running instead of freezing")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
