#!/usr/bin/env python3
"""Simulation tests for common/systemVerilog/memory_dp.sv.

Builds unittest/fixtures/memory_dp_ports_tb.sv with Verilator
`--binary --timing` and runs it at several port A / port B clock ratios, in a
temporary directory per ratio. The bench runs every PORTA_READ_ONLY /
PORTB_WRITE_ONLY combination against the plain dual-port memory and ends with
TB_PASS on stdout and an exit code of 0; anything else is a failure, reported
with the full build and run output.
"""

import os
import subprocess
import sys
import tempfile
import time

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

MEMORY_DP_SV = os.path.join(base_dir, 'common', 'systemVerilog', 'memory_dp.sv')
MEMORY_IF_DIR = os.path.join(base_dir, 'interfaces', 'memory')
TB_SV = os.path.join(test_dir, 'fixtures', 'memory_dp_ports_tb.sv')

# (port A half period, port B half period)
CLOCK_RATIOS = ((5, 7), (7, 3), (5, 5))


def _run_case(label, fn):
    try:
        fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"PASS: {label}")
    return True


def run_one(a_half, b_half):
    """Builds and runs the testbench at one clock ratio, raising with the
    full build/run output on any failure."""
    with tempfile.TemporaryDirectory() as tmp:
        obj_dir = os.path.join(tmp, 'obj')
        cmd = ['verilator', '--binary', '--timing', '-j', '4', '--top-module',
               'memory_dp_ports_tb', '-Mdir', obj_dir, '+libext+.sv',
               '-y', MEMORY_IF_DIR, f'+incdir+{MEMORY_IF_DIR}',
               # u_rw and u_bw have a write path on each port, each on its
               # own clock, which Verilator reports as MULTIDRIVEN on the
               # array whether or not the bench writes both ports at once.
               '-Wno-MULTIDRIVEN',
               f'-GA_HALF_PERIOD={a_half}', f'-GB_HALF_PERIOD={b_half}',
               MEMORY_DP_SV, TB_SV]
        # Timed binaries built through Verilator's ccache wrapper in a fresh
        # temporary directory abort at startup; build without the cache.
        build_env = dict(os.environ, CCACHE_DISABLE='1')
        try:
            build = subprocess.run(cmd, capture_output=True, text=True,
                                   env=build_env, timeout=600)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"build timed out after 600s: {' '.join(cmd)}")
        if build.returncode != 0:
            raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")

        run_cmd = [os.path.join(obj_dir, 'Vmemory_dp_ports_tb')]
        try:
            run = subprocess.run(run_cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"run timed out after 600s: {' '.join(run_cmd)}")
        if run.returncode != 0 or 'TB_PASS' not in run.stdout:
            raise AssertionError(
                f"run failed (exit {run.returncode}):\n"
                f"build:\n{build.stdout}{build.stderr}\n"
                f"run:\n{run.stdout}{run.stderr}")


def main():
    print("=" * 72)
    print("memory_dp port access simulation")
    print("=" * 72)

    start = time.time()
    ok = [_run_case(f"clock ratio clkA={a_half}/clkB={b_half}",
                    lambda a_half=a_half, b_half=b_half: run_one(a_half, b_half))
          for a_half, b_half in CLOCK_RATIOS]
    print()
    print(f"wall time: {time.time() - start:.1f}s")
    if all(ok):
        print("RESULT: all memory_dp port access simulation checks passed")
        return 0
    print(f"RESULT: {ok.count(False)} of {len(ok)} memory_dp port access "
          f"simulation checks failed")
    return 1


if __name__ == '__main__':
    sys.exit(main())
