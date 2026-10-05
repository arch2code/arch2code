#!/usr/bin/env python3
"""Equality of axi4StreamInfoSt, the compare a tandem tee uses to pass or
fail a beat.

getStructValue() returns a struct's tracker field if it has one, and -1
otherwise, at any width. A compare through it treats any two untracked payloads
as equal, and tracked payloads as equal whenever their trackers match. The
harness checks that untracked payloads differing in any field, and a tracked
payload differing outside its tracker, compare unequal.
"""

import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

FIXTURE = os.path.join(test_dir, 'fixtures', 'axi4-stream-compare', 'axi4_stream_compare.cpp')
COMMON_SC = os.path.join(base_dir, 'common', 'systemc')
SOURCE = os.path.join(COMMON_SC, 'bitTwiddling.cpp')
INTERFACE_ROOT = os.path.join(base_dir, 'interfaces')

CXX = 'clang++'
STD = '-std=c++23'
WARNINGS = ['-Wall', '-Wextra', '-Wpedantic', '-Wshadow', '-Wno-unused-variable',
            '-Wno-unused-parameter', '-Wfatal-errors']
DEFINES = ['-DSC_CPLUSPLUS=201703L', '-DSC_INCLUDE_DYNAMIC_PROCESSES', '-DBOOST_STACKTRACE_LINK']
LIBS = ['-lsystemc', '-pthread']

# Pinned so a fixture edit that drops a case fails here rather than reducing
# the evidence silently.
EXPECTED_CHECKS = 12


def toolchain_env():
    env = {}
    for var in ('SYSTEMC_INCLUDE', 'SYSTEMC_LIBDIR', 'BOOST_INCLUDE'):
        value = os.environ.get(var)
        if not value:
            raise RuntimeError(f"{var} is not set; the SystemC toolchain variables the "
                               f"arch2code makefiles require must be set to run this suite")
        env[var] = value
    return env


def run(cmd, what):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{what} failed:\n{' '.join(cmd)}\n{result.stdout}\n{result.stderr}")
    return result


def build(build_dir, env):
    """Compile the runtime source and the harness, link, and return the binary."""
    common = [STD] + WARNINGS + DEFINES + ['-I' + env['BOOST_INCLUDE'], '-I' + env['SYSTEMC_INCLUDE'],
                                           '-I' + COMMON_SC]
    for entry in sorted(os.listdir(INTERFACE_ROOT)):
        path = os.path.join(INTERFACE_ROOT, entry)
        if os.path.isdir(path):
            common.append('-I' + path)
    objects = []
    for src in (SOURCE, FIXTURE):
        obj = os.path.join(build_dir, os.path.basename(src)[:-4] + '.o')
        run([CXX] + common + ['-c', src, '-o', obj], f'compile {os.path.basename(src)}')
        objects.append(obj)

    binary = os.path.join(build_dir, 'axi4_stream_compare')
    run([CXX, STD, '-o', binary] + objects + ['-L' + env['SYSTEMC_LIBDIR']] + LIBS, 'link')
    return binary


def test_axi4_stream_untracked_and_tracked_payloads_compare_by_value():
    """Build and run the harness; every equal and unequal pair must compare as expected."""
    env = toolchain_env()
    assert shutil.which(CXX), f"{CXX} not found on PATH"
    build_dir = tempfile.mkdtemp(prefix='a2c_axi4_stream_compare_')
    try:
        binary = build(build_dir, env)
        result = subprocess.run([binary], capture_output=True, text=True, timeout=300)
    finally:
        shutil.rmtree(build_dir)

    output = result.stdout + result.stderr
    assert result.returncode == 0, f"harness exited {result.returncode}:\n{output}"
    summary = [line for line in output.splitlines() if line.startswith('checks:')]
    assert len(summary) == 1, f"expected one summary line, got {summary!r}:\n{output}"
    checks, fails = summary[0].split()
    assert fails == 'failures:0', f"{output}"
    count = int(checks.split(':')[1])
    assert count == EXPECTED_CHECKS, f"expected {EXPECTED_CHECKS} checks, got {count}:\n{output}"
    print(f"  {count} axi4StreamInfoSt equality checks, 0 failures")


def run_all_tests():
    tests = [
        test_axi4_stream_untracked_and_tracked_payloads_compare_by_value,
    ]
    print("=" * 70)
    print("AXI4 STREAM COMPARE TESTS")
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
