#!/usr/bin/env python3
"""The bitTwiddling power-of-two helpers must hold their contracts across the
whole 64-bit domain, not just below 2**32.

Both helpers were hand-rolled bit manipulation, correct below a 32-bit boundary
and silently wrong above it. `findNextPowerOf2` must return the least power of
two at or above its input and must agree with its constexpr twin, which it now
delegates to. `log2ofPowerOf2` must return the exponent of its power-of-two
argument; it now calls std::countr_zero and asserts its precondition.

Inputs the preconditions exclude - an input above 2**63, and a zero or
non-power-of-two exponent argument - are checked by running the harness with an
abort-* argument and requiring SIGABRT. They are deliberately absent from the
contract sweep, which stops at 2**63.

WHICH INPUTS ACTUALLY BITE, pinned here because the obvious test set does not:

For `log2ofPowerOf2`:

- It was correct at 2**32 BY COINCIDENCE - 32 is the one answer the surviving
  b[5] mask can produce on its own - and first wrong at 2**33. A test that
  probed the 32-bit boundary with 2**32 alone would have passed. The k=0..63
  sweep and the explicit 31..34 boundary block both exist for this; do not
  reduce either to "representative" values.

For `findNextPowerOf2`:

- Every exact power of two passes against the BROKEN code, at any magnitude.
  `n-1` is then all ones, and smearing an all-ones value is idempotent, so the
  missing `>> 32` step changes nothing. `findNextPowerOf2(2**40)` was correct.
- Everything at or below 2**32 passes against the broken code, including the
  2**32 boundary itself, because `n-1` still fits in the 32 positions smeared.
- The exposing inputs are `2**k + 1` for k >= 32, and more generally any input
  whose `n-1` has a 32-bit run of zeros below its top set bit.

A future edit that trims the input set to powers of two, or that stops at
2**32, would restore the gap while still passing. Do not narrow the binade
sweep in the fixture.

The build is done here rather than by a project makefile because the fixture is
not a generated artifact of any project. It needs no database, no example
design, and unlike the thunker harness no SystemC or boost either -
`bitTwiddling.h` pulls only <bit>, <cassert>, <cstdint>, <type_traits> and
clog2.h. It is compiled under the same warning set as the real model build, from
`include/make/a2c-systemc.mk`.
"""

import os
import shutil
import signal
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

FIXTURE = os.path.join(test_dir, 'fixtures', 'bit-twiddling', 'bit_twiddling_runtime.cpp')
COMMON_SC = os.path.join(base_dir, 'common', 'systemc')
SOURCE = os.path.join(COMMON_SC, 'bitTwiddling.cpp')

CXX = 'clang++'
STD = '-std=c++23'
# The warning half of a2c-systemc.mk CXX_FLAGS. Its target, debug-format and
# SystemC/boost flags are dropped; none of them bears on compiling this header.
WARNINGS = ['-Wall', '-Wextra', '-Wpedantic', '-Wshadow', '-Wno-unused-variable',
            '-Wno-unused-parameter', '-Wfatal-errors']

# Pinned so a fixture edit that drops inputs or assertions fails here rather
# than reducing the evidence silently. EXPECTED_CHECKS is the harness total
# across all assertion groups, not a per-input formula.
EXPECTED_INPUTS = 1187
EXPECTED_CHECKS = 6003


def run(cmd, what):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{what} failed:\n{' '.join(cmd)}\n{result.stdout}\n{result.stderr}")
    return result


def build(build_dir):
    """Compile the runtime source and the harness, link, and return the binary."""
    common = [STD] + WARNINGS + ['-I' + COMMON_SC]
    objects = []
    for src in (SOURCE, FIXTURE):
        obj = os.path.join(build_dir, os.path.basename(src)[:-4] + '.o')
        run([CXX] + common + ['-c', src, '-o', obj], f'compile {os.path.basename(src)}')
        objects.append(obj)

    binary = os.path.join(build_dir, 'bit_twiddling_runtime')
    run([CXX, STD, '-o', binary] + objects, 'link')
    return binary


def test_power_of_two_helpers_hold_their_contracts_across_the_domain():
    """Build and run the harness; every contract assertion must hold."""
    assert shutil.which(CXX), f"{CXX} not found on PATH"
    build_dir = tempfile.mkdtemp(prefix='a2c_bittwiddle_rt_')
    try:
        binary = build(build_dir)
        result = subprocess.run([binary], capture_output=True, text=True, timeout=300)
        # Inputs the preconditions exclude must abort rather than return a value.
        excluded = {}
        for mode in ('abort-domain', 'abort-log2-zero', 'abort-log2-nonpower'):
            excluded[mode] = subprocess.run([binary, mode], capture_output=True,
                                            text=True, timeout=300)
    finally:
        shutil.rmtree(build_dir)

    for mode, r in excluded.items():
        assert r.returncode == -signal.SIGABRT, (
            f"{mode}: expected SIGABRT from the precondition assert, got "
            f"returncode {r.returncode}:\n{r.stdout}{r.stderr}")

    output = result.stdout + result.stderr
    assert result.returncode == 0, f"harness exited {result.returncode}:\n{output}"

    summary = [line for line in output.splitlines() if line.startswith('checks:')]
    assert len(summary) == 1, f"expected one summary line, got {summary!r}:\n{output}"
    checks, fails = summary[0].split()
    assert fails == 'failures:0', f"{output}"

    counted = [line for line in output.splitlines() if line.startswith('inputs:')]
    assert len(counted) == 1, f"expected one input-count line, got {counted!r}:\n{output}"
    inputs = int(counted[0].split(':')[1])
    assert inputs == EXPECTED_INPUTS, f"expected {EXPECTED_INPUTS} inputs, got {inputs}:\n{output}"

    count = int(checks.split(':')[1])
    assert count == EXPECTED_CHECKS, f"expected {EXPECTED_CHECKS} checks, got {count}:\n{output}"
    print(f"  {count} contract assertions over {inputs} inputs, 0 failures")


def run_all_tests():
    tests = [
        test_power_of_two_helpers_hold_their_contracts_across_the_domain,
    ]
    print("=" * 70)
    print("BIT TWIDDLING RUNTIME TESTS")
    print("=" * 70)
    results = []
    for test_func in tests:
        print(f"\n{test_func.__name__}:")
        try:
            test_func()
            results.append((test_func.__name__, True))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    print("\n" + "=" * 70 + "\nTEST SUMMARY\n" + "=" * 70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    if passed == len(results):
        print("\n  ALL TESTS PASSED!")
        return 0
    print("\n  SOME TESTS FAILED")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
