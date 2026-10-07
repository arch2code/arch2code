#!/usr/bin/env python3
"""What a testbench must do before it is allowed to report a pass.

A run reports a pass from its testbench Config's `final()`. Two shipped pieces
of developer-authored library content decide whether that pass means anything,
and neither is reachable from any generator run, so both are checked here.

Rule 1 - completion requires seeded tests that finished.

`testController::are_all_tests_complete()` compares a completed-test counter
against a seeded-test total. Both start at zero, so without a guard on the
total the comparison is trivially true for a testbench that seeded no tests at
all: a run that exercised nothing reports every test complete, and a `final()`
asserting on it passes vacuously. The rule is checked by compiling and running
the shipped header, because the defect is in what the function returns, not in
how it is spelled.

Rule 2 - a scaffold that asserts end-of-test also asserts completion.

End-of-test is a vote that the run may stop; it says nothing about what ran. A
scaffolded Config asserting only end-of-test therefore passes on any vote, so a
new project starts life reporting a pass while checking nothing. Every shipped
scaffold template that asserts end-of-test must also seed test names and assert
completion, which given Rule 1 makes the scaffold fail until its author replaces
the placeholder with tests the design actually runs.

Scaffold templates are discovered from the `fileGen` template module rather than
listed, so a newly added testbench-Config scaffold is held to Rule 2 without
anyone extending this file.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

FILEGEN_PY = os.path.join(base_dir, 'templates', 'fileGen', 'fileGen.py')
SYSTEMC_COMMON = os.path.join(base_dir, 'common', 'systemc')

# The end-of-test assertion each testbench Config scaffold emits, the seeding
# call that gives it something to check, and the completion assertion that
# checks it.
END_OF_TEST_ASSERT = 'isEndOfTest()'
SEED_CALL = 'set_test_names('
COMPLETION_ASSERT = 'are_all_tests_complete()'

# Exercises the shipped testController through the states a Config drives it
# through. sc_start leaves elaboration first because completing the last test
# notifies an sc_event, which SystemC rejects during elaboration.
PROBE_SRC = """
#include "testController.h"
#include <iostream>

int sc_main(int, char **)
{
    sc_start(SC_ZERO_TIME);
    testController &controller = testController::GetInstance();
    std::cout << "unseeded=" << controller.are_all_tests_complete() << '\\n';
    controller.set_test_names({});
    std::cout << "emptySeed=" << controller.are_all_tests_complete() << '\\n';
    controller.set_test_names({"t0"});
    std::cout << "seeded=" << controller.are_all_tests_complete() << '\\n';
    controller.register_test_name("t0");
    controller.test_complete("t0");
    std::cout << "finished=" << controller.are_all_tests_complete() << '\\n';
    return 0;
}
"""

FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


def run_probe():
    # Returns the probe's state -> value map, or a diagnostic string. SystemC is
    # a hard requirement of every build in this repository (see
    # include/make/a2c-systemc.mk), so its absence is a broken environment.
    scInclude = os.environ.get('SYSTEMC_INCLUDE')
    scLibdir = os.environ.get('SYSTEMC_LIBDIR')
    if not scInclude or not scLibdir:
        return "SYSTEMC_INCLUDE and SYSTEMC_LIBDIR must be set, as they are for any build here"
    tmpdir = tempfile.mkdtemp(prefix='tbCompletionGate')
    try:
        srcPath = os.path.join(tmpdir, 'probe.cpp')
        binPath = os.path.join(tmpdir, 'probe')
        with open(srcPath, 'w') as fh:
            fh.write(PROBE_SRC)
        build = subprocess.run(
            ['g++', '-std=c++23', '-DSC_CPLUSPLUS=201703L',
             f'-I{scInclude}', f'-I{SYSTEMC_COMMON}', srcPath, '-o', binPath,
             f'-L{scLibdir}', '-lsystemc', '-pthread'],
            capture_output=True, text=True)
        if build.returncode != 0:
            return f"probe did not build: {build.stderr.strip()}"
        run = subprocess.run([binPath], capture_output=True, text=True,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        if run.returncode != 0:
            return f"probe did not run: {run.stderr.strip()}"
        states = {}
        for line in run.stdout.splitlines():
            if '=' in line:
                name, _, value = line.partition('=')
                states[name.strip()] = value.strip()
        return states
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_completion_requires_seeded_tests():
    print("\nRule 1: are_all_tests_complete() requires seeded tests that finished")
    print("-" * 72)
    states = run_probe()
    if isinstance(states, str):
        check(False, f"testController probe must build and run: {states}")
        return
    expected = {
        'unseeded': ('0', "a testbench that never called set_test_names has not "
                          "completed its tests, so final() cannot pass on a run "
                          "that checked nothing"),
        'emptySeed': ('0', "seeding an empty test list is not completion either, "
                           "for the same reason as never seeding"),
        'seeded': ('0', "a seeded test that has not finished is not complete"),
        'finished': ('1', "every seeded test having finished is completion - "
                          "without this the guard would reject valid passes"),
    }
    for state, (want, why) in expected.items():
        got = states.get(state)
        check(got == want,
              f"are_all_tests_complete() is {'true' if want == '1' else 'false'} "
              f"when {state} (got {got!r}): {why}")


def load_scaffold_templates():
    spec = importlib.util.spec_from_file_location('fileGenTemplates', FILEGEN_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {name: value for name, value in vars(module).items()
            if name.endswith('Template') and isinstance(value, str)}


def test_scaffold_asserts_completion(templates):
    print("\nRule 2: a scaffold asserting end-of-test also asserts completion")
    print("-" * 72)
    asserting = {name: text for name, text in templates.items()
                 if END_OF_TEST_ASSERT in text}
    check(bool(asserting),
          f"at least one shipped scaffold template asserts {END_OF_TEST_ASSERT}, "
          f"otherwise this rule silently checks nothing (searched "
          f"{len(templates)} templates in {os.path.relpath(FILEGEN_PY, base_dir)})")
    for name, text in sorted(asserting.items()):
        check(COMPLETION_ASSERT in text,
              f"{name} asserts {COMPLETION_ASSERT}: end-of-test is only a vote "
              f"that the run may stop, so without this the scaffolded project "
              f"passes on any vote while checking nothing")
        check(SEED_CALL in text,
              f"{name} calls {SEED_CALL}): the completion assertion needs seeded "
              f"tests to check, and the placeholder it seeds is what makes a new "
              f"project fail until its author writes a real test")


def main():
    print("=" * 72)
    print("TESTING TESTBENCH PASS CRITERIA")
    print("=" * 72)
    test_completion_requires_seeded_tests()
    test_scaffold_asserts_completion(load_scaffold_templates())

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all testbench pass criteria checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
