#!/usr/bin/env python3
"""ADD_TEST runs a member function as a test, in the testbench's list order.

A testbench lists its tests, in run order, with testController::set_test_names.
ADD_TEST(fn) in a module constructor runs fn as the test named fn when its turn
comes. The order of the ADD_TEST lines does not matter. --test runs only the
named tests and never starts the others, and --listTests prints the list.
With --log, a run with --test writes the simulation to the log file and prints
the exit summary once on the console. Two blocks may each add a function with
the same name; that test ends when both return.

A testbench may run some tests with ADD_TEST and others with old-style
register_test_name threads. Once it uses ADD_TEST, one warning before simulation
names every test that will run without an ADD_TEST, because the run never
completes any of them that no old-style thread runs either. --test leaves the
unselected tests out of the warning. A testbench that never uses ADD_TEST gets
no warning. A name run both ways exits with status 1 before either body prints,
whether register_test_name or ADD_TEST comes first. ADD_TEST before
set_test_names, and set_test_names after ADD_TEST, exit with status 1 and say
so.

The probe runs the shipped sc_main with the testbenches described in
fixtures/testbench-cli/add_test_probe.cpp.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
FIXTURE = os.path.join(test_dir, 'fixtures', 'testbench-cli', 'add_test_probe.cpp')
MAIN_CPP = os.path.join(base_dir, 'common', 'scmain', 'main.cpp')

ALL = ('ran alpha', 'ran shared fast', 'ran shared slow', 'Completing test shared', 'ran beta', 'ran gamma')
WARNING = 'WARNING: no add_test or ADD_TEST runs these tests from set_test_names: '
MISSING = WARNING + 'forgotten, alsoForgotten. '
MIXED_NAMES = WARNING + 'oldStyle. '
MIXED_SAME = 'ERROR: test alpha runs with add_test or ADD_TEST and also calls register_test_name'
RELIST = 'ERROR: set_test_names runs after add_test or ADD_TEST registered a test.'
UNLISTED = 'ERROR: test name alpha is not valid: the test list is empty. Call set_test_names before ADD_TEST'
TIME_LIMIT = 'Simulation has reached the maximum'

# (testbench, args) -> (exit status, output lines in this order, output that must be absent)
SCENARIOS = {
    ('addTestProbe', ()): (0, ALL, ()),
    ('addTestProbe', ('--test', 'beta')): (0, ('ran beta',), ('ran alpha', 'ran shared', 'ran gamma')),
    ('addTestProbe', ('--listTests',)): (0, ('alpha', 'shared', 'beta', 'gamma'), ('ran ', 'Simulation')),
    ('missingProbe', ()): (1, (MISSING, 'ran alpha', TIME_LIMIT), ('ran forgotten',)),
    ('missingProbe', ('--listTests',)): (0, ('alpha', 'forgotten', 'alsoForgotten'), (WARNING, 'ran ')),
    ('mixedNamesProbe', ()): (0, (MIXED_NAMES, 'ran alpha', 'ran oldStyle old style'), (TIME_LIMIT,)),
    ('mixedNamesProbe', ('--test', 'alpha')): (0, ('ran alpha',), (WARNING, 'ran oldStyle')),
    ('mixedNamesProbe', ('--test', 'oldStyle')): (0, (MIXED_NAMES, 'ran oldStyle old style'), ('ran alpha', TIME_LIMIT)),
    ('mixedSameNameProbe', ()): (1, (MIXED_SAME,), ('ran ', TIME_LIMIT)),
    ('earlyOldFormProbe', ()): (1, (MIXED_SAME,), ('ran ', TIME_LIMIT)),
    ('oldFormProbe', ()): (0, ('ran oldStyle old style',), (WARNING, TIME_LIMIT)),
    ('relistProbe', ()): (1, (RELIST,), ('ran ', TIME_LIMIT)),
    ('unlistedProbe', ()): (1, (UNLISTED,), ('ran ', TIME_LIMIT)),
}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def in_order(output, needles):
    # Each needle starts a line, after the line the previous needle started.
    lines = output.splitlines()
    pos = 0
    for needle in needles:
        while pos < len(lines) and not lines[pos].startswith(needle):
            pos += 1
        if pos == len(lines):
            return False
        pos += 1
    return True


def check_log_redirect(binPath, tmpdir, scLibdir):
    # A valid --test simulates, so the --log redirect must stay in place.
    logPath = os.path.join(tmpdir, 'x.log')
    label = 'addTestProbe --log x.log --test beta'
    run = subprocess.run([binPath, 'addTestProbe', '--scTimeLimit', '1000', '--log', logPath, '--test', 'beta'],
                         capture_output=True, text=True, timeout=120, cwd=tmpdir,
                         env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    if not os.path.isfile(logPath):
        check(False, f"{label} writes the log file {logPath}")
        print(run.stdout + run.stderr)
        return
    with open(logPath) as fh:
        logText = fh.read()
    before = len(FAILURES)
    check(run.returncode == 0, f"{label} exits with status 0 (got {run.returncode})")
    check(in_order(logText, ('ran beta', 'Completing test beta')), f"{label} writes the test to the log file")
    for needle in ('ran beta', 'Completing test beta'):
        check(needle not in run.stdout + run.stderr, f"{label} does not print {needle!r} on the console")
    check(run.stdout.count('No error') == 1, f"{label} prints the exit summary once on the console")
    check(logText.count('No error') == 1, f"{label} writes the exit summary once to the log file")
    if len(FAILURES) > before:
        print(run.stdout + run.stderr)
        print(logText)


def test_testbench_add_test():
    scLibdir = os.environ['SYSTEMC_LIBDIR']
    tmpdir = tempfile.mkdtemp(prefix='a2c_add_test_')
    try:
        # buildProbe writes the probe into tmpdir, so its quoted include of
        # main.cpp resolves to this copy of the file under test.
        shutil.copy(MAIN_CPP, tmpdir)
        with open(FIXTURE) as fh:
            binPath = buildProbe(tmpdir, fh.read())
        if not os.path.isfile(binPath):
            check(False, f"add_test probe must build and link: {binPath}")
            return
        for (testBench, args), (status, ordered, absent) in SCENARIOS.items():
            label = ' '.join((testBench,) + args)
            run = subprocess.run([binPath, testBench, '--scTimeLimit', '1000', *args],
                                 capture_output=True, text=True, timeout=120, cwd=tmpdir,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            output = run.stdout + run.stderr
            before = len(FAILURES)
            check(run.returncode == status, f"{label} exits with status {status} (got {run.returncode})")
            check(in_order(output, ordered), f"{label} prints lines starting {ordered!r} in that order")
            for needle in absent:
                check(needle not in output, f"{label} does not print {needle!r}")
            if ordered == ALL:
                check(output.count('Completing test shared') == 1,
                      f"{label} completes the shared test once, after both of its functions return")
            if len(FAILURES) > before:
                print(output)
        check_log_redirect(binPath, tmpdir, scLibdir)
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    test_testbench_add_test()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
