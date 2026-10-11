#!/usr/bin/env python3
"""VL_TIMING=1 builds, links and runs a Verilated top whose RTL has a delay.

`unittest/fixtures/vl-timing` has one Verilated leaf, `vltSrc`. Its RTL waits
2ns in an initial block, stamps `$time` and then pushes the stamp to a model
checker, which asserts it is 2000ps. The delay ends before the first clock
edge at 5ns, so no input clock edge arrives while it is pending. Verilator
before 5.053 hides those edges from a --sc model.

Checks:
- lint takes the switch: with VL_TIMING=1 it passes, without it Verilator
  rejects the delay (STMTDLY);
- `make VL_DUT=1 VL_TIMING=1` links with no EXTRA_VL_LIB_OBJS, and the
  library carries the timing runtime built in the shared vl_dummy Mdir;
- the build warns about the Verilator version exactly when it is below 5.053;
- the model run and the Verilated run both read back the 2000ps stamp;
- a repeat build with the same setting verilates nothing and relinks nothing;
- VL_TIMING=0 re-verilates with --no-timing, and the Verilated leaf, its delay
  now ignored, stamps 0.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _make_helpers import shell_make_env
from _tmp_helpers import remove_tree


FIXTURE = os.path.join(test_dir, 'fixtures', 'vl-timing')
BUILD_JOBS = '8'
VL_INST = 'tb.vltTop.uSrc'
STAMP_LINE = 'received stamp {}'
LIBRARY = 'libvlTimingvl_s_wrap.a'
VERSION_WARNING = 'VL_TIMING=1 with Verilator'
FIXED_VERSION = (5, 53)


def make(project, *args, directory=None):
    cmd = ['make', '-C', directory or project, f'-j{BUILD_JOBS}',
           f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}', *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                          env=shell_make_env())


def require(result, what):
    if result.returncode != 0:
        raise RuntimeError(f"{what} failed (rc={result.returncode}):\n"
                           f"{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def run(rundir, *args):
    return subprocess.run(['./run', 'vltTop', *args], capture_output=True,
                          text=True, timeout=300, cwd=os.path.join(rundir, 'build'))


def verilator_version():
    # `Verilator 5.052 2026-09-05 rev v5.052` -> (5, 52)
    word = subprocess.run(['verilator', '--version'], capture_output=True,
                          text=True, check=True).stdout.split()[1]
    return tuple(int(part) for part in word.split('.'))


def verilate_lines(output):
    return [line for line in output.splitlines() if line.startswith('verilator ')]


def main():
    failures = []

    def check(ok, message, detail=''):
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        if not ok:
            failures.append(message)
            if detail:
                print(detail)

    tmp = tempfile.mkdtemp(prefix='vl_timing_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'vl-timing')
        shutil.copytree(FIXTURE, project, ignore=shutil.ignore_patterns(
            '*.db', '*.db-*', '.gen', 'build', 'compile_commands.json'))
        for target in ('db', 'newmodule', 'gen'):
            require(make(project, target), f"make {target}")
        rtl = os.path.join(project, 'rtl')
        rundir = os.path.join(project, 'rundir')

        lint = make(project, 'lint', 'VL_TIMING=1', directory=rtl)
        out = lint.stdout + lint.stderr
        check(lint.returncode == 0 and 'verilator  --timing --lint-only' in out,
              "VL_TIMING=1 lints with --timing and accepts the delay", out)
        lint = make(project, 'lint', 'VL_TIMING=', directory=rtl)
        out = lint.stdout + lint.stderr
        check(lint.returncode != 0 and '%Warning-STMTDLY' in out,
              "lint without VL_TIMING rejects the delay", out)

        out = require(make(project, 'all', 'VL_DUT=1', 'VL_TIMING=1', directory=rundir),
                      "make all VL_DUT=1 VL_TIMING=1")
        verilates = verilate_lines(out)
        check(verilates and all(' --timing ' in v for v in verilates),
              f"every verilate runs with --timing ({len(verilates)} verilates)", out)
        version = verilator_version()
        warns = version < FIXED_VERSION
        check((VERSION_WARNING in out) == warns,
              f"Verilator {version} {'warns' if warns else 'does not warn'} under VL_TIMING=1", out)
        members = subprocess.run(['ar', 't', os.path.join(rundir, 'build', 'vl', LIBRARY)],
                                 capture_output=True, text=True).stdout.split()
        check('verilated_timing.o' in members,
              "the Verilator library carries verilated_timing.o", ' '.join(members))
        check('ADDMOD obj_dir/vl_dummy/verilated_timing.o' in out,
              "verilated_timing.o comes from the shared vl_dummy Mdir", out)

        model = run(rundir)
        check(model.returncode == 0 and STAMP_LINE.format(2000) in model.stdout,
              "the model run reads back the 2000ps stamp", model.stdout + model.stderr)
        verilated = run(rundir, '--vlInst', VL_INST)
        check(verilated.returncode == 0 and STAMP_LINE.format(2000) in verilated.stdout,
              "the Verilated run reads back the 2000ps stamp its RTL delay produced",
              verilated.stdout + verilated.stderr)

        out = require(make(project, 'all', 'VL_DUT=1', 'VL_TIMING=1', directory=rundir),
                      "repeat make all VL_DUT=1 VL_TIMING=1")
        check(not verilate_lines(out) and 'ar -M' not in out and ' -o ' not in out,
              "a repeat build with VL_TIMING=1 verilates, archives and links nothing", out)

        out = require(make(project, 'all', 'VL_DUT=1', 'VL_TIMING=0', directory=rundir),
                      "make all VL_DUT=1 VL_TIMING=0")
        verilates = verilate_lines(out)
        check(verilates and all(' --no-timing ' in v for v in verilates)
              and 'verilated_timing.o' not in out and VERSION_WARNING not in out,
              f"VL_TIMING=0 re-verilates every top with --no-timing ({len(verilates)} verilates)",
              out)
        verilated = run(rundir, '--vlInst', VL_INST)
        check(verilated.returncode != 0 and STAMP_LINE.format(0) in verilated.stdout,
              "without --timing the Verilated leaf ignores its delay and stamps 0",
              verilated.stdout + verilated.stderr)
    finally:
        remove_tree(tmp)

    if failures:
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print("\nAll VL_TIMING checks passed")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
