#!/usr/bin/env python3
"""The UVM flow turns off the SystemC watchdog's stall check.

Under UVM the test drives the DUT, so the SystemC models can sit idle while UVM
waits on something legitimate. The stall check would end that run with a
Q_ASSERT and no UVM report. The UVM testbench config therefore sets
`watchDog::stallCheckDisabledByUvm`, and the UVM flow's own guards bound stalls.

Rule 1 - with the flag set, an enabled watchdog that is never tickled does not
fire, and the run reaches its own end. The handler says once at startup that
the check is off, at VERBOSITY_LOW, the setting UVM regressions run at.

Rule 2 - enablers keep registering and voting under the flag, so a model that
votes the watchdog on and off does not trip the enable-overflow assert.

Rule 3 - without the flag, the same run still fails with the stall diagnostic,
so the flag is the only thing standing between the two outcomes.

Rule 4 - the flag leaves the no-terminator check on. A run with the flag set,
no end-of-test voter and no time limit still fails with that diagnostic, and
not with the stall one.

The probe runs the shipped watchDogHandler; test_watchdog_no_terminator.py
covers the rest of its behaviour.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe, NO_TERMINATOR_MSG, STALL_MSG

UVM_MSG = 'SystemC watchdog stall check is off; the UVM checks bound stalls'

# Two enablers vote the watchdog on, one takes its vote back and gives it again,
# and nothing ever tickles. The design process advances simulation time slowly
# against the wall clock for three seconds, past the one-second bound of both
# watchdog checks, then stops the run itself.
PROBE_SRC = """
#include "systemc.h"
#include "logging.h"
#include "simController.h"
#include "watchDog.h"
import a2c.endOfTest;
#include <chrono>
#include <ctime>
#include <iostream>
#include <string>
#include <thread>

int sc_main(int argc, char *argv[])
{
    std::string scenario = argc > 1 ? argv[1] : "";
    logging::GetInstance().setDefaultVerbosity(VERBOSITY_LOW);
    endOfTest voter(scenario != "uvmNoVoter");
    watchDog::stallCheckDisabledByUvm = (scenario == "uvm" || scenario == "uvmNoVoter");
    watchDog::registerEnabler();
    watchDog::registerEnabler();
    watchDog::enableWatchdog();
    watchDog::enableWatchdog();
    watchDog::disableWatchdog();
    watchDog::enableWatchdog();
    std::cout << "enabled=" << watchDog::enabled << "\\n";
    watchDog::timeout = sc_time(1, SC_US);
    sc_spawn([]() { watchDogHandler(); });
    sc_spawn([]() {
        auto start = std::chrono::steady_clock::now();
        while (std::chrono::steady_clock::now() - start < std::chrono::seconds(3)) {
            wait(sc_time(1, SC_US));
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        sc_stop();
    });
    sc_start();
    std::cout << "expired=" << watchDog::watchDogIsExpired() << "\\n";
    std::cout << "ranToCompletion=1\\n";
    return 0;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def runScenario(binPath, scenario, scLibdir):
    try:
        run = subprocess.run([binPath, scenario], capture_output=True, text=True,
                             timeout=60, env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    except subprocess.TimeoutExpired:
        return None
    return run.stdout + run.stderr


def test_uvm_stall_check_flag():
    print("\nThe UVM flag turns off the stall check and nothing else")
    print("-" * 72)
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_watchdog_uvm_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"watchdog probe must build and link: {binPath}")
            return
        uvm = runScenario(binPath, 'uvm', scLibdir)
        plain = runScenario(binPath, 'plain', scLibdir)
        noVoter = runScenario(binPath, 'uvmNoVoter', scLibdir)
        if uvm is None or plain is None or noVoter is None:
            check(False, "every probe run ends within 60 s")
            return
        check('enabled=1' in uvm and 'Watchdog enable overflow' not in uvm,
              "enabler votes count under the flag without an overflow assert")
        check(STALL_MSG not in uvm and 'ranToCompletion=1' in uvm and 'expired=0' in uvm,
              "with the flag set, an unticked enabled watchdog never fires and the run ends itself")
        check(uvm.count(UVM_MSG) == 1, "the handler logs once, at VERBOSITY_LOW, that the stall check is off")
        check('enabled=1' in plain and STALL_MSG in plain and 'expired=1' in plain,
              "without the flag, the same run fails with the stall diagnostic")
        check(UVM_MSG not in plain, "without the flag, the UVM line is absent")
        check(NO_TERMINATOR_MSG in noVoter and STALL_MSG not in noVoter,
              "with the flag set, a run with no voter and no time limit still fails with the no-terminator diagnostic")
        if FAILURES:
            print("--- uvm run ---\n" + uvm + "\n--- plain run ---\n" + plain +
                  "\n--- uvmNoVoter run ---\n" + noVoter)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_uvm_stall_check_flag()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
