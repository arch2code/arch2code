#!/usr/bin/env python3
"""Simulation tests for common/systemVerilog/memory_reg_bridge.sv.

Builds unittest/fixtures/memory_reg_bridge_tb.sv with Verilator
`--binary --timing` and runs it under every reset style and clock ratio the
bridge has to work under, in a temporary directory per configuration. Each
run's self-checking scenarios end with TB_PASS on stdout and an exit code of
0; anything else is a failure, reported with the full build and run output.

Same style as test_clock_reset_emission.py. Every check is that the
simulation binary reached TB_PASS, so there are no _expect/_refute helpers.
_run_case prints the PASS/FAIL line and main() prints the RESULT summary.
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time
from collections import namedtuple

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

FLOPS_SV = os.path.join(base_dir, 'common', 'systemVerilog', 'flops.sv')
ASSERTS_SVH = os.path.join(base_dir, 'common', 'systemVerilog', 'asserts.svh')
BRIDGE_SV = os.path.join(base_dir, 'common', 'systemVerilog', 'memory_reg_bridge.sv')
MEMORY_SP_SV = os.path.join(base_dir, 'common', 'systemVerilog', 'memory_sp.sv')
MEMORY_IF_DIR = os.path.join(base_dir, 'interfaces', 'memory')
COMMON_DIR = os.path.dirname(FLOPS_SV)
TB_SV = os.path.join(test_dir, 'fixtures', 'memory_reg_bridge_tb.sv')

ResetStyle = namedtuple('ResetStyle', ['label', 'defines', 'run_reset_scenarios'])

RESET_STYLES = (
    ResetStyle('the default sync style', [], True),
    ResetStyle('A2C_RESET_ASYNC', ['A2C_RESET_ASYNC'], True),
    ResetStyle('A2C_RESET_NONE', ['A2C_RESET_NONE'], False),
)

# Unpacked in RESET_STYLES's own order so the non-integer and jitter lists
# can pick a style by name instead of repeating the RESET_STYLES literals.
_DEFAULT_STYLE, _ASYNC_STYLE, _NONE_STYLE = RESET_STYLES

# (bus half period, mem half period) clock ratios.
CLOCK_RATIOS = ((1, 3), (2, 2), (3, 1))

# Config carries the ResetStyle itself, so a config's label, defines and
# no_reset (not style.run_reset_scenarios) all derive from cfg.style in one
# place (run_one, main()) rather than being copied into each Config.
Config = namedtuple('Config', ['style', 'bus_half', 'mem_half', 'mem_phase',
                                'jitter'])

# Every configuration the base suite runs: the nine integer-ratio
# configurations at mem_phase=0, plus two diagnostic configurations at the
# symmetric clock ratio with the memory clock's first edge phase-shifted by
# one time unit (mem_phase=1), one per reset style whose reset scenarios
# actually run. A2C_RESET_NONE skips the scenarios mem_phase affects, so it
# is not worth a second run.
_INTEGER_RATIO_CONFIGS = tuple(
    Config(rs, bus_half, mem_half, 0, False)
    for rs in RESET_STYLES
    for bus_half, mem_half in CLOCK_RATIOS
) + tuple(
    Config(rs, 2, 2, 1, False)
    for rs in RESET_STYLES
    if rs.run_reset_scenarios
)

# Two non-integer clock ratios, default reset style, memory clock phase-
# shifted the same way the mem_phase=1 diagnostics above are.
NONINTEGER_RATIO_CONFIGS = tuple(
    Config(_DEFAULT_STYLE, bus_half, mem_half, 1, False)
    for bus_half, mem_half in ((3, 7), (7, 3))
)

# Jitter configurations: A2C_CDC_JITTER exercises the one-cycle-hold model
# from the header comment across the three integer clock ratios in the
# default style, once in A2C_RESET_ASYNC at the symmetric ratio, once more at
# a non-integer ratio in the default style, and once more at each of the two
# most lopsided integer ratios (bus 1/mem 5 and bus 5/mem 1), phase-shifted
# the same way the mem_phase=1 diagnostics above are.
JITTER_CONFIGS = (
    Config(_DEFAULT_STYLE, 1, 3, 0, True),
    Config(_DEFAULT_STYLE, 2, 2, 0, True),
    Config(_DEFAULT_STYLE, 3, 1, 0, True),
    Config(_ASYNC_STYLE, 2, 2, 0, True),
    Config(_DEFAULT_STYLE, 3, 7, 0, True),
    Config(_DEFAULT_STYLE, 1, 5, 1, True),
    Config(_DEFAULT_STYLE, 5, 1, 1, True),
)

CONFIGS = _INTEGER_RATIO_CONFIGS + NONINTEGER_RATIO_CONFIGS + JITTER_CONFIGS


def _run_case(label, fn):
    """Runs fn(), prints the PASS/FAIL line, and returns (ok, stdout or
    None). stdout is the testbench's captured output on success, used by
    main() to report one jitter run's random-traffic counts."""
    try:
        stdout = fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False, None
    print(f"PASS: {label}")
    return True, stdout


def run_one(rtl_path, cfg, seed):
    """Builds and runs the testbench for one configuration, raising with the
    full build/run output on any failure."""
    all_defines = list(cfg.style.defines) + (['A2C_CDC_JITTER'] if cfg.jitter else [])
    with tempfile.TemporaryDirectory() as tmp:
        obj_dir = os.path.join(tmp, 'obj')
        cmd = (['verilator', '--binary', '--timing', '-j', '4', '--top-module',
                'memory_reg_bridge_tb', '-Mdir', obj_dir, '+libext+.sv',
                '-y', COMMON_DIR, '-y', MEMORY_IF_DIR,
                f'+incdir+{COMMON_DIR}', f'+incdir+{MEMORY_IF_DIR}',
                # Assertions are on by default in this Verilator release; the
                # flag keeps them on should an older release change that.
                '--assert'] +
               [f'+define+{d}' for d in all_defines] +
               [f'-GBUS_HALF_PERIOD={cfg.bus_half}', f'-GMEM_HALF_PERIOD={cfg.mem_half}',
                f'-GMEM_PHASE={cfg.mem_phase}',
                FLOPS_SV, ASSERTS_SVH, MEMORY_SP_SV, rtl_path, TB_SV])
        # With Verilator's auto-selected ccache wrapper, the binary aborted at
        # verilated_timing.cpp:83 on every run in this repeated-tmpdir setup;
        # with the cache disabled, the identical sources pass. Disable it for
        # this build only.
        build_env = dict(os.environ, CCACHE_DISABLE='1')
        # -j 4 matches the co-simulation flow's build parallelism.
        try:
            build = subprocess.run(cmd, capture_output=True, text=True,
                                    env=build_env, timeout=600)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"build timed out after 600s: {' '.join(cmd)}")
        if build.returncode != 0:
            raise AssertionError(
                f"build failed:\n{build.stdout}{build.stderr}")

        run_cmd = [os.path.join(obj_dir, 'Vmemory_reg_bridge_tb'), f'+seed={seed}']
        if not cfg.style.run_reset_scenarios:
            run_cmd.append('+no_reset_tests')
        try:
            run = subprocess.run(run_cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"run timed out after 600s: {' '.join(run_cmd)}")
        if run.returncode != 0 or 'TB_PASS' not in run.stdout:
            raise AssertionError(
                f"run failed (exit {run.returncode}):\n"
                f"build:\n{build.stdout}{build.stderr}\n"
                f"run:\n{run.stdout}{run.stderr}")
    return run.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rtl', default=BRIDGE_SV,
                         help='path to memory_reg_bridge.sv to test')
    parser.add_argument('--seed', type=int, default=None,
                         help='override the per-configuration seed for every run')
    args = parser.parse_args()

    print("=" * 72)
    print("memory_reg_bridge simulation")
    print("=" * 72)

    start = time.time()
    ok = []
    jitter_stdout = None
    for index, cfg in enumerate(CONFIGS):
        no_reset = not cfg.style.run_reset_scenarios
        label = f"{cfg.style.label}, clock ratio bus={cfg.bus_half}/mem={cfg.mem_half}"
        if no_reset:
            label += " (+no_reset_tests)"
        if cfg.mem_phase:
            label += f", MEM_PHASE={cfg.mem_phase}"
        if cfg.jitter:
            label += ", A2C_CDC_JITTER"
        seed = args.seed if args.seed is not None else index + 1
        passed, stdout = _run_case(
            label,
            lambda cfg=cfg, seed=seed: run_one(args.rtl, cfg, seed))
        ok.append(passed)
        if cfg.jitter and passed and jitter_stdout is None:
            jitter_stdout = stdout
    wall = time.time() - start

    if jitter_stdout is not None:
        print()
        print("random-traffic counts from one jitter run:")
        for line in jitter_stdout.splitlines():
            if 'random_traffic' in line:
                print(line)

    print()
    print(f"wall time: {wall:.1f}s")
    if all(ok):
        print("RESULT: all memory_reg_bridge simulation checks passed")
        return 0
    print(f"RESULT: {ok.count(False)} of {len(ok)} memory_reg_bridge "
          f"simulation checks failed")
    return 1


if __name__ == '__main__':
    sys.exit(main())
