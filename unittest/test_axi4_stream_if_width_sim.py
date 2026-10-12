#!/usr/bin/env python3
"""Simulation test for interfaces/axi4_stream/axi4_stream_if.sv sideband widths.

Builds unittest/fixtures/axi4_stream_if_width_tb.sv with Verilator
`--binary --timing` in a temporary directory and runs it. The bench checks
that tkeep and tstrb have one bit per tdata byte.
For logic [3:0][7:0], $size and $bits differ on every simulator.
The module-local struct reproduces a VCS W-2024.09-SP2 $size bug; only VCS fails it.
It ends with TB_PASS on stdout and an exit code of 0; anything else is a
failure, reported with the full build and run output.
"""

import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

AXI4_STREAM_IF_SV = os.path.join(base_dir, 'interfaces', 'axi4_stream', 'axi4_stream_if.sv')
TB_SV = os.path.join(test_dir, 'fixtures', 'axi4_stream_if_width_tb.sv')


def run_tb():
    """Builds and runs the testbench, raising with the full build/run output
    on any failure."""
    with tempfile.TemporaryDirectory() as tmp:
        obj_dir = os.path.join(tmp, 'obj')
        cmd = ['verilator', '--binary', '--timing', '-j', '4', '--top-module',
               'axi4_stream_if_width_tb', '-Mdir', obj_dir,
               AXI4_STREAM_IF_SV, TB_SV]
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

        run_cmd = [os.path.join(obj_dir, 'Vaxi4_stream_if_width_tb')]
        try:
            run = subprocess.run(run_cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"run timed out after 600s: {' '.join(run_cmd)}")
        if run.returncode != 0 or 'TB_PASS' not in run.stdout:
            raise AssertionError(
                f"run failed (exit {run.returncode}):\n"
                f"build:\n{build.stdout}{build.stderr}\n"
                f"run:\n{run.stdout}{run.stderr}")
        print(run.stdout, end='')


def main():
    print("=" * 72)
    print("axi4_stream_if tkeep/tstrb width simulation")
    print("=" * 72)
    try:
        run_tb()
    except Exception as exc:
        print(f"FAIL: axi4_stream_if sideband widths: {exc}")
        print("RESULT: axi4_stream_if width simulation check failed")
        return 1
    print("PASS: axi4_stream_if sideband widths")
    print("RESULT: axi4_stream_if width simulation check passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
