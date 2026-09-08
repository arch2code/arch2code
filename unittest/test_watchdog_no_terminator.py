#!/usr/bin/env python3
"""What ends a run that has nothing able to end it.

A run stops when an end-of-test voter votes it done, or when `--scTimeLimit`
expires. With neither - no voter registered and no time limit - nothing can ever
stop it, and it is not rescued by event starvation: the framework watchdog is
spawned for every project and its periodic wake keeps events queued. Such a run
spins until it is killed, printing nothing about why.

Either condition alone is legitimate. A run with voters needs no time limit, and
a zero-voter run under an explicit `--scTimeLimit` is supported. Together they
are unconditionally a hang, so `watchDogHandler` arms a second path on exactly
that pair and fails the run naming the cause.

Rule 1 - the no-terminator path fires, and only on that pair.

Rule 2 - tickles do not defeat it. The stall path resets its timer on a tickle
because a tickle is evidence of progress. Having no terminator is not a progress
property but a static property of the configuration: a run that can never end
usually makes fine progress, so a design that tickles would otherwise hold the
fallback off forever.

Rule 3 - the stall path is unchanged. The two paths share a wall-clock bound and
a loop, so a change to one can silently disarm the other.

Rule 4 - the wall-clock bound is load-bearing, not decoration. It is the whole
reason the check is safe to run at all: voters register lazily, so a zero read
taken early is not evidence of anything. A path that fired on the first sample
would be indistinguishable from the correct one on every configuration that has
no voter at all, which is why the bound needs a case of its own.

Rule 5 - an already-ended run is not a run that cannot end. `forceEndOfTest()`
ends a test without registering a voter, so voter count alone would report a run
that has demonstrably terminated as one that never can.

Rule 6 - what the stall path bounds is the gap between tickles, not whether a
tickle was ever seen. A design tickling on a period wider than the bound is
stalled in every one of its gaps, so the timer has to restart on each tickle
rather than a tickle disarming the check for the rest of the run. The
never-tickled and briskly-tickled cases cannot tell those two apart, so pinning
the bound needs a case whose tickles arrive too late to be progress.

The rules are checked by building and running the shipped watchdog, because the
defect is in when it fires, not in how it is spelled. The framework sources it
links against are discovered from `common/systemc` rather than listed, so a new
framework source does not silently drop out of the probe.
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

SYSTEMC_COMMON = os.path.join(base_dir, 'common', 'systemc')
INTERFACE_DIRS = sorted(d for d in glob.glob(os.path.join(base_dir, 'interfaces', '*'))
                        if os.path.isdir(d))

# The two diagnostics the watchdog can fail a run with. They must stay distinct:
# a run with no terminator is not stuck, so reporting it as a stall sends the
# reader hunting for a deadlock that is not there.
NO_TERMINATOR_MSG = 'No end-of-test voter is registered and no --scTimeLimit is set'
STALL_MSG = 'Simulation stuck Watchdog timeout'

# Drives the shipped watchDogHandler through one configuration per run. The
# design process advances simulation time slowly against the wall clock, which
# is what both watchdog paths are bounded by, and stops the run on its own so a
# configuration the watchdog is meant to ignore still terminates.
PROBE_SRC = """
#include "systemc.h"
#include "simController.h"
#include "watchDog.h"
import a2c.endOfTest;
#include <chrono>
#include <ctime>
#include <iostream>
#include <string>
#include <thread>

static const uint64_t MILLI_TO_NANO = 1000000ULL;
static const uint64_t SECS_TO_NANO = 1000000000ULL;

static uint64_t nsecSince(const struct timespec &start)
{
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return (now.tv_sec * SECS_TO_NANO + now.tv_nsec) - (start.tv_sec * SECS_TO_NANO + start.tv_nsec);
}

int sc_main(int argc, char *argv[])
{
    std::string scenario = argc > 1 ? argv[1] : "";
    endOfTest voter(scenario == "voter" || scenario == "stall" || scenario == "slowTickle");
    if (scenario == "timeLimit") simController::maxRuntimeUS = 1000;
    if (scenario == "forcedEnd") endOfTestState::GetInstance().forceEndOfTest();
    // Registers from a host thread well after the watchdog's first sample but
    // well inside its one-second bound, which is the lazy registration the bound
    // exists to tolerate.
    std::thread lateVoter;
    if (scenario == "lateVoter") {
        lateVoter = std::thread([]() {
            std::this_thread::sleep_for(std::chrono::milliseconds(250));
            endOfTest late(true);
        });
    }
    bool tickle = (scenario == "tickled" || scenario == "slowTickle");
    // Wall clock the design leaves between tickles, zero being every pass of the
    // loop below. A gap wider than the watchdog's one-second bound is a stall
    // whatever came before it, so the design keeps tickling for the whole run
    // and expects to be killed inside its first gap regardless.
    uint64_t tickleGapNsec = (scenario == "slowTickle") ? 1300 * MILLI_TO_NANO : 0;
    if (scenario == "stall" || tickle) {
        watchDog::registerEnabler();
        watchDog::enableWatchdog();
    }
    watchDog::timeout = sc_time(1, SC_US);
    sc_spawn([]() { watchDogHandler(); });
    sc_spawn([tickle, tickleGapNsec]() {
        struct timespec start;
        clock_gettime(CLOCK_MONOTONIC, &start);
        uint64_t nextTickle = 0;
        while (nsecSince(start) < 3 * SECS_TO_NANO) {
            wait(sc_time(1, SC_US));
            if (tickle && nsecSince(start) >= nextTickle) {
                watchDog::tickleWatchdog();
                nextTickle = nsecSince(start) + tickleGapNsec;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        sc_stop();
    });
    sc_start();
    if (lateVoter.joinable()) lateVoter.join();
    std::cout << "ranToCompletion=1\\n";
    return 0;
}
"""

# scenario -> (diagnostic the run must fail with or None, why)
SCENARIOS = {
    'noTerminator': (NO_TERMINATOR_MSG,
                     "no voter and no time limit is the hang, and it must be "
                     "reported as that rather than left to spin"),
    'tickled': (NO_TERMINATOR_MSG,
                "a design with no terminator still makes progress, so tickles "
                "must not hold the fallback off"),
    'timeLimit': (None,
                  "a zero-voter run under an explicit --scTimeLimit is a "
                  "supported configuration that ends at its limit"),
    'voter': (None,
              "a registered voter is what ends a run, so an unbounded run with "
              "one is not a hang"),
    'lateVoter': (None,
                  "voters register lazily, so the zero read must be held for the "
                  "full wall-clock bound before it means anything - a path that "
                  "fired on its first sample would kill this run"),
    'forcedEnd': (None,
                  "forceEndOfTest() ends a run without registering a voter, so a "
                  "test that has already ended must not be reported as one that "
                  "can never end"),
    'stall': (STALL_MSG,
              "an enabled watchdog that is never tickled is the stall the "
              "watchdog has always caught"),
    'slowTickle': (STALL_MSG,
                   "a design tickling on a period wider than the bound is "
                   "stalled between its tickles, so the timer must restart on "
                   "each tickle rather than one tickle standing in for progress "
                   "the design is no longer making"),
}

FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


def buildProbe(tmpdir, probeSrc=PROBE_SRC):
    # Builds `probeSrc` against every framework source in common/systemc and
    # returns the binary path, or a diagnostic string. SystemC is a hard
    # requirement of every build in this repository (see
    # include/make/a2c-systemc.mk), so its absence is a broken environment, and
    # clang++ is that makefile's default compiler.
    scInclude = os.environ.get('SYSTEMC_INCLUDE')
    scLibdir = os.environ.get('SYSTEMC_LIBDIR')
    if not scInclude or not scLibdir:
        return "SYSTEMC_INCLUDE and SYSTEMC_LIBDIR must be set, as they are for any build here"
    flags = ['-m64', '-std=c++23', '-DSC_CPLUSPLUS=201703L',
             '-DSC_INCLUDE_DYNAMIC_PROCESSES', '-DBOOST_STACKTRACE_LINK',
             f'-I{scInclude}', f'-I{SYSTEMC_COMMON}']
    flags += [f'-I{d}' for d in INTERFACE_DIRS]

    # Every module interface in the directory is compiled, so adding a second
    # framework module extends the probe instead of tripping a count. They are
    # precompiled in turn, each seeing the ones built before it, which is what an
    # import between two framework modules needs. Naming each BMI after the
    # module it declares is what lets an importer find it.
    pcms = []
    for source in sorted(glob.glob(os.path.join(SYSTEMC_COMMON, '*.cppm'))):
        with open(source) as fh:
            declaration = re.search(r'^\s*export\s+module\s+([\w.]+)\s*;', fh.read(), re.M)
        if not declaration:
            return (f"{os.path.relpath(source, base_dir)} is a .cppm that declares no "
                    f"module, so the probe cannot name the module it exports")
        pcm = os.path.join(tmpdir, declaration.group(1) + '.pcm')
        build = subprocess.run(['clang++'] + flags +
                               ['--precompile', '-x', 'c++-module', source, '-o', pcm],
                               capture_output=True, text=True)
        if build.returncode != 0:
            return f"framework module {declaration.group(1)} did not build: {build.stderr.strip()}"
        flags.append(f'-fmodule-file={declaration.group(1)}={pcm}')
        pcms.append(pcm)
    if not pcms:
        return (f"no framework module interface found in "
                f"{os.path.relpath(SYSTEMC_COMMON, base_dir)}")

    srcPath = os.path.join(tmpdir, 'probe.cpp')
    with open(srcPath, 'w') as fh:
        fh.write(probeSrc)
    objects = [pcm[:-4] + '.module.o' for pcm in pcms]
    compiles = [subprocess.Popen(['clang++'] + flags + ['-c', pcm, '-o', obj],
                                 stderr=subprocess.PIPE, text=True)
                for pcm, obj in zip(pcms, objects)]
    for source in sorted(glob.glob(os.path.join(SYSTEMC_COMMON, '*.cpp'))) + [srcPath]:
        obj = os.path.join(tmpdir, os.path.basename(source)[:-4] + '.o')
        objects.append(obj)
        compiles.append(subprocess.Popen(['clang++'] + flags + ['-c', source, '-o', obj],
                                         stderr=subprocess.PIPE, text=True))
    errors = []
    for process in compiles:
        _, stderr = process.communicate()
        if process.returncode != 0:
            errors.append(stderr.strip())
    if errors:
        return f"framework sources did not build: {errors[0]}"

    binPath = os.path.join(tmpdir, 'probe')
    link = subprocess.run(['clang++', '-o', binPath] + objects +
                          ['-lboost_system', '-lboost_program_options',
                           '-lboost_stacktrace_basic', f'-L{scLibdir}',
                           '-ldl', '-lrt', '-lsystemc', '-pthread'],
                          capture_output=True, text=True)
    if link.returncode != 0:
        return f"probe did not link: {link.stderr.strip()}"
    return binPath


def runScenario(binPath, scenario, scLibdir):
    # The watchdog needs a second of wall clock before either path fires and the
    # probe's design process runs for three, so the timeout only trips if the
    # run never ends at all - which is the defect under test. Runs are concurrent
    # because each is wall-clock bound and spends nearly all of it asleep, so the
    # suite costs one run rather than one per scenario.
    try:
        run = subprocess.run([binPath, scenario], capture_output=True, text=True,
                             timeout=60, env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    except subprocess.TimeoutExpired:
        return None
    return run.stdout


def test_watchdog_arming():
    print("\nWhen the watchdog ends a run, and with which diagnostic")
    print("-" * 72)
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='watchDogNoTerminator')
    try:
        binPath = buildProbe(tmpdir)
        if not os.path.isfile(binPath):
            check(False, f"watchdog probe must build and link: {binPath}")
            return
        scenarios = sorted(SCENARIOS)
        with ThreadPoolExecutor(max_workers=len(scenarios)) as pool:
            outputs = dict(zip(scenarios, pool.map(
                lambda scenario: runScenario(binPath, scenario, scLibdir), scenarios)))
        for scenario in scenarios:
            expected, why = SCENARIOS[scenario]
            output = outputs[scenario]
            if output is None:
                check(False, f"{scenario} run must terminate on its own: it did not, "
                             f"which is the unbounded hang this path exists to end")
                continue
            fired = [message for message in (NO_TERMINATOR_MSG, STALL_MSG)
                     if message in output]
            check(fired == ([expected] if expected else []),
                  f"{scenario} fails with {expected!r} (got {fired}): {why}"
                  if expected else
                  f"{scenario} runs to completion untouched (got {fired}): {why}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    print("=" * 72)
    print("TESTING WATCHDOG TERMINATION OF A RUN WITH NO TERMINATOR")
    print("=" * 72)
    test_watchdog_arming()

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all watchdog termination checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
