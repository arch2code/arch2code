// copyright QiStor 2025

#include "logging.h"
#include "simController.h"
#include "systemc.h"
#include "instanceFactory.h"
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


// Instantiable watchDog block. sc_main runs watchDogHandler() for every
// project, so the block adds only the "systemCWatchdog" startup vote, which a
// design counts in setStartupVoters(), and stopping the run at end-of-test.
SC_MODULE(watchDogBlock), public blockBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // watchDog is a framework-shared block owned by no user project, so
            // it registers under the unqualified (empty) projectName.
            instanceFactory::registerBlock("watchDog_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<watchDogBlock>(blockName, variant, bbMode));}, "", "" );
        }
    };
    static registerBlock registerBlock_;
public:
    watchDogBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~watchDogBlock() override = default;
    void setTimed(int nsec, timedDelayMode mode) override {};
    void setLogging(verbosity_e verbosity) override {};
private:
    void startupVoteAndStop(void);
};


SC_HAS_PROCESS(watchDogBlock);

watchDogBlock::registerBlock watchDogBlock::registerBlock_; //register the block with the factory

watchDogBlock::watchDogBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("watchDog", name(), bbMode)
{
    log_.logPrint("watchDog initialized.", LOG_IMPORTANT );
    SC_THREAD(startupVoteAndStop);
}

void watchDogBlock::startupVoteAndStop(void)
{
    endOfTestState &eot = endOfTestState::GetInstance();
    log_.logPrint("Startup delay begin", LOG_IMPORTANT);
    wait(simController::startupDelay);
    log_.logPrint("Startup delay " + simController::startupDelay.to_string() + " complete", LOG_IMPORTANT);
    simController::advanceStartupPhase("systemCWatchdog");
    // Polled: forceEndOfTest() latches end-of-test without notifying eotEvent.
    while (!eot.isEndOfTest())
    {
        wait(watchDog::timeout);
    }
    wait(sc_time(1, SC_US));
    sc_stop();
}


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

// The periodic wake keeps events queued, so a model driven from outside does not
// end on starvation. Two paths, each bounded by wall clock, since a running
// clock advances simulation time forever.
//
// Stall: armed once every registered enabler has voted it on; every tickle
// restarts its timer, since a tickle is evidence of progress.
//
// No terminator: no end-of-test voter, no --scTimeLimit and no latched
// end-of-test (forceEndOfTest() ends a run without a voter). A static property
// of the configuration, so tickles do not restart its timer; the wall-clock
// wait keeps it off runs whose voters register lazily. Its condition only goes
// true->false, so the timer is never rearmed.
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
