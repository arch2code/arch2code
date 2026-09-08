// copyright QiStor 2025

#include "logging.h"
#include "simController.h"
#include "systemc.h"
#include "watchDog.h"
#include "q_assert.h"
import a2c.endOfTest;

#include <ctime>

bool watchDog::tickled = false;
bool watchDog::enabled = false;
sc_time watchDog::timeout = sc_time(30, SC_US);
bool watchDog::isTimeout = false;
uint64_t watchDog::enablers = 0;
uint64_t watchDog::enableVotes = 0;


void watchDog::enableWatchdog(void)
{
    enableVotes++;
    Q_ASSERT_CTX_NODUMP (enableVotes <= enablers, "watchDog", "Watchdog enable overflow, did you forget to register an enabler?");
    enabled = (enableVotes == enablers);
};
void watchDog::disableWatchdog(void)
{
    enabled = false;
    enableVotes--;
};


enum timeConversionT {
    MICRO_TO_NANO =        1000LL,
    MILLI_TO_NANO =     1000000LL,
    SECS_TO_NANO  =  1000000000LL
};
enum watchdogTimeoutT {
    WATCHDOG_TIMEOUT = MILLI_TO_NANO * 1000LL // 1s
};

// Wall-clock nanoseconds since the timer was started. The call that finds it
// stopped starts it and reports zero, so clearing *running* rewinds it.
static uint64_t elapsedNsec(struct timespec &start, bool &running)
{
    struct timespec now;
    if (!running)
    {
        clock_gettime(CLOCK_MONOTONIC, &start);
        running = true;
        return 0;
    }
    clock_gettime(CLOCK_MONOTONIC, &now);
    return (now.tv_sec * SECS_TO_NANO + now.tv_nsec) - (start.tv_sec * SECS_TO_NANO + start.tv_nsec);
}

// The periodic wake keeps events in the queue, so a model whose stimulus arrives
// from outside does not end on starvation. Two independent paths, each bounded
// by wall clock rather than simulation time, since a design whose clock still
// runs advances simulation time forever.
//
// Stall: armed only once every registered enabler has voted it on, so a design
// that registers none is never watched, and every tickle restarts its timer
// because a tickle is evidence of progress.
//
// No terminator: no end-of-test voter and no --scTimeLimit, so nothing in the
// run is able to end it. A latched end-of-test disarms it too, since a run that
// has already ended demonstrably could - forceEndOfTest() ends a run without
// registering a voter. A static property of the configuration rather than a
// stall - such a run usually makes fine progress - so tickles must not restart
// its timer. Waiting out the wall clock is what keeps it off runs whose voters
// register lazily from firmware or host threads. Its condition can only go
// true->false - voters only increment, maxRuntimeUS is fixed at command-line
// parse, end-of-test only latches - so the timer is never rearmed.
void watchDogHandler(void)
{
    logging &lg = logging::GetInstance();
    logBlock log_("watchDog");
    endOfTestState &eot = endOfTestState::GetInstance();
    wait(simController::startupDelay); // wait for the system to start up
    bool timerRunning = false;
    bool noTerminatorTimerRunning = false;
    struct timespec start;
    struct timespec noTerminatorStart;
    while(true)
    {
        wait(watchDog::timeout); // use a large timeout so if we are busy the watchdog isnt using up much time
        if (watchDog::tickled || watchDog::enabled == false)
        {
            watchDog::tickled = false;
            timerRunning = false;
        }
        else
        {
            uint64_t nseconds = elapsedNsec(start, timerRunning);
            if (nseconds > WATCHDOG_TIMEOUT)
            {
                watchDog::isTimeout = true;
                log_.logPrint(std::format("no design progress in {} ms of wall clock at {}",
                                          nseconds / MILLI_TO_NANO, sc_time_stamp().to_string()), LOG_IMPORTANT);
                lg.statusPrint();
                Q_ASSERT_CTX_NODUMP(false, "watchDog", "Simulation stuck Watchdog timeout");
            }
        }
        if (eot.isEndOfTest() == false && eot.registeredVoters() == 0 && simController::maxRuntimeUS == 0)
        {
            uint64_t nseconds = elapsedNsec(noTerminatorStart, noTerminatorTimerRunning);
            if (nseconds > WATCHDOG_TIMEOUT)
            {
                log_.logPrint(std::format("no end-of-test voter after {} ms of wall clock at {}",
                                          nseconds / MILLI_TO_NANO, sc_time_stamp().to_string()), LOG_IMPORTANT);
                lg.statusPrint();
                Q_ASSERT_CTX_NODUMP(false, "watchDog", "No end-of-test voter is registered and no --scTimeLimit is set, so this run can never terminate");
            }
        }
    }
}
