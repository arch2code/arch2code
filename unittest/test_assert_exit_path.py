#!/usr/bin/env python3
"""How a run ends when Q_ASSERT fires, and which of those ends report anything.

`q_assert_body` unwinds a thread process by waiting after `sc_stop()`, and there
is no process to unwind outside one. Its tail therefore decides what a failing
run looks like to whoever started it, and the two contexts want opposite things.

Rule 1 - a post-simulation assert returns. `main()` calls `testBench->final()`
and `exitSummary()` after `sc_start()` has returned, and library code asserts
from there. Aborting at that point discards the summary and replaces the exit
code with a signal, so the run reports nothing at all; returning is what lets
`main()` finish and hand back the code `errorCode::fail` recorded.

Rule 2 - the failure is still a failure. Returning must not soften it: the
recorded exit code has to survive to the process exit status, or a broken run
reports success.

Rule 3 - an elaboration assert still aborts. Nothing downstream reports it -
there is no summary yet and no `main()` tail to reach - so the abort is the only
signal, and widening Rule 1 past the post-simulation states would silence it.

Rule 4 - an assert inside a thread process still kills that process. That is the
path every design assert takes, and it is what stops the failing thread from
running on past the check it just failed.

The rules are checked by building and running the shipped `q_assert.cpp` through
each context, because the defect is in which context returns and which aborts,
not in how the tail is spelled. The probe is built against every framework
source in common/systemc by the same discovery the watchdog probe uses.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

# Fires the shipped Q_ASSERT from one context per run. The tail after sc_start()
# stands in for main()'s: logging::final(), testBench->final(), exitSummary() and
# the `return exit_code` all run there, outside any process and after the
# scheduler has stopped.
PROBE_SRC = """
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include <iostream>
#include <string>

int sc_main(int argc, char *argv[])
{
    std::string scenario = argc > 1 ? argv[1] : "";
    if (scenario == "elaboration") {
        Q_ASSERT_CTX_NODUMP(false, "probe", "assert fired from elaboration");
        std::cout << "elaborationContinued=1\\n";
        return 0;
    }
    sc_spawn([scenario]() {
        wait(sc_time(1, SC_US));
        if (scenario == "inThread") {
            Q_ASSERT_CTX_NODUMP(false, "probe", "assert fired from a thread process");
            std::cout << "threadContinued=1\\n";
        }
        sc_stop();
    });
    sc_start();
    if (scenario == "postSim") {
        Q_ASSERT_CTX_NODUMP(false, "probe", "assert fired after simulation stopped");
    }
    std::cout << "status=" << sc_get_status() << "\\n";
    std::cout << "reachedSummary=1\\n";
    int code = errorCode::getExitCode();
    std::cout << "exitCode=" << code << "\\n";
    // errorCode starts at -1 and only main()'s pass()/fail() callers move it off
    // that, so a run with no assert must not be read as a failure here.
    return code > 0 ? code : 0;
}
"""

# scenario -> (process exit status, output lines that must be present, absent, why)
SCENARIOS = {
    'clean': (0, ('reachedSummary=1', 'exitCode=-1'), (),
              "a run with no assert reaches its tail and exits zero, without "
              "which every expectation below would be met by a probe that "
              "asserts nothing"),
    'postSim': (1, ('reachedSummary=1', 'status=SC_STOPPED', 'exitCode=1'), (),
                "an assert after sc_start() returns must hand control back so "
                "main() reaches exitSummary() and returns the recorded code, "
                "rather than aborting with the summary unwritten"),
    'elaboration': (-6, (), ('elaborationContinued=1',),
                    "an elaboration assert has no summary to reach and no "
                    "main() tail to return to, so the abort is its only signal"),
    'inThread': (1, ('reachedSummary=1',), ('threadContinued=1',),
                 "a design assert must kill the process that failed the check "
                 "instead of letting it run on, and the run must still end "
                 "through main()'s tail"),
}

FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


def test_assert_exit_path():
    print("\nWhat Q_ASSERT does to a run, per context")
    print("-" * 72)
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='assertExitPath')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"assert probe must build and link: {binPath}")
            return
        for scenario in sorted(SCENARIOS):
            status, present, absent, why = SCENARIOS[scenario]
            run = subprocess.run([binPath, scenario], capture_output=True, text=True,
                                 timeout=120,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            output = run.stdout + run.stderr
            before = len(FAILURES)
            check(run.returncode == status,
                  f"{scenario} exits with status {status} (got {run.returncode}): {why}")
            for needle in present:
                check(needle in output, f"{scenario} prints {needle!r}: {why}")
            for needle in absent:
                check(needle not in output, f"{scenario} does not print {needle!r}: {why}")
            # The probe's own output is the evidence, but a passing assert
            # scenario prints a stack trace by design, so it is shown only when
            # a check on it failed.
            if len(FAILURES) > before:
                print(f"--- {scenario} output ---\n{output}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    print("=" * 72)
    print("TESTING THE Q_ASSERT EXIT PATH")
    print("=" * 72)
    test_assert_exit_path()

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all assert exit path checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
