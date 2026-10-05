#!/usr/bin/env python3
"""--test and --listTests select from the tests a testbench declares.

A testbench declares its tests, in run order, with
testController::set_test_names. --test <name>, repeatable, runs only the named
tests and keeps the testbench's order. --listTests prints the declared names,
one per line, and exits 0 before simulation starts. A name the testbench did not
declare exits with status 2 and lists the valid names, as any other mistyped
option does. A testbench that never calls set_test_names has nothing to select
from, so either option exits with status 2 instead of running everything.
With --log, a run with --test writes the simulation to the log file and prints
the exit summary once on the console. --listTests and a rejected --test print
on the console, since they exit before simulating.

The probe runs the shipped sc_main. selectProbe declares alpha, beta and gamma;
each test prints "ran <name>". noTestsProbe declares none.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
FIXTURE = os.path.join(test_dir, 'fixtures', 'testbench-cli', 'test_selection_probe.cpp')
MAIN_CPP = os.path.join(base_dir, 'common', 'scmain', 'main.cpp')

ALL = ('ran alpha', 'ran beta', 'ran gamma')
INVALID = "Invalid test 'bogus'. Valid tests: alpha, beta, gamma"
NOT_DECLARED = 'Testbench noTestsProbe does not declare its tests with testController::set_test_names'

# (testbench, args) -> (exit status, output lines in this order, output that must be absent)
SCENARIOS = {
    ('selectProbe', ()): (0, ALL, ()),
    ('selectProbe', ('--listTests',)): (0, ('alpha', 'beta', 'gamma'), ('ran ', 'Simulation')),
    ('selectProbe', ('--test', 'beta')): (0, ('ran beta',), ('ran alpha', 'ran gamma')),
    ('selectProbe', ('--test', 'gamma', '--test', 'alpha')): (0, ('ran alpha', 'ran gamma'), ('ran beta',)),
    ('selectProbe', ('--test', 'bogus')): (2, (INVALID,), ('ran ', 'Simulation')),
    ('noTestsProbe', ()): (0, ('ran noTests',), ()),
    ('noTestsProbe', ('--test', 'alpha')): (2, (NOT_DECLARED,), ('ran ', 'Simulation')),
    ('noTestsProbe', ('--listTests',)): (2, (NOT_DECLARED,), ('ran ', 'Simulation')),
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
    label = 'selectProbe --log x.log --test beta'
    run = subprocess.run([binPath, 'selectProbe', '--scTimeLimit', '1000', '--log', logPath, '--test', 'beta'],
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


# (testbench, args) -> (exit status, lines on stdout, line on stderr)
LOG_CONSOLE_SCENARIOS = {
    ('selectProbe', ('--listTests',)): (0, ('alpha', 'beta', 'gamma'), None),
    ('selectProbe', ('--test', 'bogus')): (2, (), INVALID),
    ('noTestsProbe', ('--listTests',)): (2, (), NOT_DECLARED),
}


def check_log_console(binPath, tmpdir, scLibdir):
    # Options that print and exit before simulating print on the console, not
    # into the --log file.
    logPath = os.path.join(tmpdir, 'x.log')
    for (testBench, args), (status, stdoutLines, stderrLine) in LOG_CONSOLE_SCENARIOS.items():
        label = ' '.join((testBench, '--log', 'x.log') + args)
        run = subprocess.run([binPath, testBench, '--scTimeLimit', '1000', '--log', logPath, *args],
                             capture_output=True, text=True, timeout=120, cwd=tmpdir,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        before = len(FAILURES)
        check(run.returncode == status, f"{label} exits with status {status} (got {run.returncode})")
        if stdoutLines:
            check(in_order(run.stdout, stdoutLines), f"{label} prints {stdoutLines!r} on stdout")
        if stderrLine:
            check(stderrLine in run.stderr, f"{label} prints {stderrLine!r} on stderr")
        if len(FAILURES) > before:
            print(run.stdout + run.stderr)


def test_testbench_test_selection():
    scLibdir = os.environ['SYSTEMC_LIBDIR']
    tmpdir = tempfile.mkdtemp(prefix='a2c_test_selection_')
    try:
        # buildProbe writes the probe into tmpdir, so its quoted include of
        # main.cpp resolves to this copy of the file under test.
        shutil.copy(MAIN_CPP, tmpdir)
        with open(FIXTURE) as fh:
            binPath = buildProbe(tmpdir, fh.read())
        if not os.path.isfile(binPath):
            check(False, f"test selection probe must build and link: {binPath}")
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
            if INVALID in ordered:
                check(INVALID in run.stderr and INVALID not in run.stdout,
                      f"{label} reports the invalid test on stderr, not stdout")
            if len(FAILURES) > before:
                print(output)
        check_log_redirect(binPath, tmpdir, scLibdir)
        check_log_console(binPath, tmpdir, scLibdir)
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    test_testbench_test_selection()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
