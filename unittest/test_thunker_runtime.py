#!/usr/bin/env python3
"""The six new protocol port thunkers bridge a payload at runtime, not just at compile time.

`interfaces/<proto>/<proto>_port_thunker.h` exists for `axi4_stream`,
`external_reg`, `memory`, `pop_ack`, `raw` and `status` as well as for the seven
protocols that already had one. A header that compiles but is never run proves
nothing about the adapter: a forwarding loop that deadlocks, drops a beat,
duplicates one, or selects the wrong arm of `copyPayload` compiles perfectly.

This suite therefore builds and RUNS `fixtures/thunker-runtime/thunker_runtime.cpp`
under the SystemC kernel. That program instantiates every one of the six templates
explicitly and drives real transactions through each, in both forwarding
directions and at both settings of the adapter's direct-copy verdict.

WHAT MAKES THE RUN EVIDENCE RATHER THAN A SMOKE TEST, in the fixture's own words
and pinned here so a future edit that weakens it is visible:

- The two payload declarations have identical storage but a `_bitWidth` narrower
  than that storage, so `copyPayload`'s two arms disagree - the packed arm drops
  the bits above `_bitWidth`, the direct arm keeps them. Every asserted value
  therefore says WHICH ARM RAN.
- The two multi-payload protocols are instantiated at complementary verdict
  subsets, so a flag wired to the wrong payload slot fails.
- Each protocol runs in the consumer-child shape (`thunkIn`) and the
  producer-child shape (`thunkOut`), and `raw` additionally in the two port
  shapes, which are the ones that resolve their up-side interface lazily.
- Every sink loop runs forever and counts; the totals are asserted after the
  kernel drains, so a duplicated transaction fails even though every value
  matched.

The build is done here rather than by a project makefile because the harness is
not a generated artifact of any project: it needs no database, and no example
design exercises these six protocols across a cross-interface bind. The
toolchain, defines, warning set and libraries mirror `include/make/a2c-systemc.mk`,
so a header that trips a warning the real model build treats as an error fails
here too.
"""

import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

FIXTURE = os.path.join(test_dir, 'fixtures', 'thunker-runtime', 'thunker_runtime.cpp')
COMMON_SC = os.path.join(base_dir, 'common', 'systemc')
# Base interfaces only. The fixture includes no pro header, and a base suite
# must not depend on builder/pro being present in the checkout.
INTERFACE_ROOT = os.path.join(base_dir, 'interfaces')

# Clang only: the module flag spelling for the `a2c.endOfTest` interface unit
# differs under GCC, and the makefiles' Clang path is the default.
CXX = 'clang++'
STD = '-std=c++23'
# a2c-systemc.mk CXX_FLAGS, less the flags that select a target or a debug
# format and have no bearing on what compiles.
WARNINGS = ['-Wall', '-Wextra', '-Wpedantic', '-Wshadow', '-Wno-unused-variable',
            '-Wno-unused-parameter', '-Wfatal-errors']
DEFINES = ['-DSC_CPLUSPLUS=201703L', '-DSC_INCLUDE_DYNAMIC_PROCESSES', '-DBOOST_STACKTRACE_LINK']
LIBS = ['-lboost_system', '-lboost_program_options', '-lboost_stacktrace_basic',
        '-ldl', '-lrt', '-lsystemc', '-pthread']

# Twelve consumer-shape, twelve producer-shape and two port-shape harnesses.
# Pinned so a harness that stopped being constructed fails here rather than
# reducing the evidence silently.
EXPECTED_CHECKS = 388


def toolchain_env():
    env = {}
    for var in ('SYSTEMC_INCLUDE', 'SYSTEMC_LIBDIR', 'BOOST_INCLUDE', 'LD_BOOST'):
        value = os.environ.get(var)
        if not value:
            raise RuntimeError(f"{var} is not set; the SystemC toolchain variables the "
                               f"arch2code makefiles require must be set to run this suite")
        env[var] = value
    return env


def include_flags(env):
    flags = ['-I' + env['BOOST_INCLUDE'], '-I' + env['SYSTEMC_INCLUDE'], '-I' + COMMON_SC]
    for entry in sorted(os.listdir(INTERFACE_ROOT)):
        path = os.path.join(INTERFACE_ROOT, entry)
        if os.path.isdir(path):
            flags.append('-I' + path)
    return flags


def run(cmd, what):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{what} failed:\n{' '.join(cmd)}\n{result.stdout}\n{result.stderr}")
    return result


def build_and_run(build_dir, env):
    """Compile the endOfTest module, the runtime and the harness; link and run."""
    common = [STD] + WARNINGS + DEFINES + include_flags(env)

    # `q_assert.cpp` and its neighbours import the a2c.endOfTest module, so the
    # interface unit is precompiled first and its object linked in, exactly as
    # a2c-systemc.mk's Clang path does.
    pcm = os.path.join(build_dir, 'a2c.endOfTest.pcm')
    run([CXX] + common + ['--precompile', os.path.join(COMMON_SC, 'endOfTest.cppm'), '-o', pcm],
        'endOfTest precompile')
    module_obj = os.path.join(build_dir, 'endOfTest.o')
    run([CXX, STD, '-c', pcm, '-o', module_obj], 'endOfTest module object')

    module_flag = f'-fmodule-file=a2c.endOfTest={pcm}'
    sources = sorted(os.path.join(COMMON_SC, f) for f in os.listdir(COMMON_SC) if f.endswith('.cpp'))
    sources.append(FIXTURE)

    def compile_one(src):
        obj = os.path.join(build_dir, os.path.basename(src)[:-4] + '.o')
        run([CXX] + common + [module_flag, '-c', src, '-o', obj], f'compile {os.path.basename(src)}')
        return obj

    # The translation units are independent; the fixture's own is the long pole.
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
        objects = [module_obj] + list(pool.map(compile_one, sources))

    binary = os.path.join(build_dir, 'thunker_runtime')
    run([CXX, STD, '-o', binary] + objects +
        ['-L' + env['LD_BOOST'], '-L' + env['SYSTEMC_LIBDIR']] + LIBS, 'link')

    return subprocess.run([binary], capture_output=True, text=True, timeout=300)


def test_thunkers_bridge_payloads_in_both_directions_at_both_verdicts():
    """Build and run the harness; every asserted payload and beat count must match."""
    env = toolchain_env()
    assert shutil.which(CXX), f"{CXX} not found on PATH"
    build_dir = tempfile.mkdtemp(prefix='a2c_thunker_rt_')
    try:
        result = build_and_run(build_dir, env)
    finally:
        shutil.rmtree(build_dir)

    output = result.stdout + result.stderr
    assert result.returncode == 0, f"harness exited {result.returncode}:\n{output}"
    # The summary line is the harness's own accounting. A run that forwarded
    # nothing would still exit 0 without it, so the count is checked too.
    summary = [line for line in output.splitlines() if line.startswith('checks:')]
    assert len(summary) == 1, f"expected one summary line, got {summary!r}:\n{output}"
    checks, failures = summary[0].split()
    assert failures == 'failures:0', f"{output}"
    count = int(checks.split(':')[1])
    assert count == EXPECTED_CHECKS, f"expected {EXPECTED_CHECKS} checks, got {count}:\n{output}"
    print(f"  {count} payload and beat-count checks across 28 harnesses, 0 failures")


def run_all_tests():
    tests = [
        test_thunkers_bridge_payloads_in_both_directions_at_both_verdicts,
    ]
    print("=" * 70)
    print("THUNKER RUNTIME TESTS")
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
