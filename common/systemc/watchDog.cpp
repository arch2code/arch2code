// copyright QiStor 2025

#include "logging.h"
#include "endOfTest.h"
#include "simController.h"
#include "systemc.h"
#include "instanceFactory.h"
#include "watchDog.h"
#include "q_assert.h"

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


SC_MODULE(watchDogBlock), public blockBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("watchDog_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<watchDogBlock>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    watchDogBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~watchDogBlock() override = default;
    void setTimed(int nsec, timedDelayMode mode) override {};
    void setLogging(verbosity_e verbosity) override {};
private:
    void watchDogHandler(void);

};


SC_HAS_PROCESS(watchDogBlock);

watchDogBlock::registerBlock watchDogBlock::registerBlock_; //register the block with the factory

watchDogBlock::watchDogBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("watchDog", name(), bbMode)
{
    log_.logPrint("watchDog initialized.", LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(watchDogHandler);
}


enum timeConversionT {
    MICRO_TO_NANO =        1000LL,
    MILLI_TO_NANO =     1000000LL,
    SECS_TO_NANO  =  1000000000LL
};
enum watchdogTimeoutT {
    WATCHDOG_TIMEOUT = MILLI_TO_NANO * 1000LL // 1s
};

// watchdog is necessary to ensure there are always event in the system - otherwise simulation stops
// this is necessary as the stimuli is outside of the model
void watchDogBlock::watchDogHandler(void)
{
    logging &lg = logging::GetInstance();
    endOfTestState &eot = endOfTestState::GetInstance();
    log_.logPrint("Startup delay begin", LOG_IMPORTANT);
    wait(simController::startupDelay); // wait for the system to start up
    log_.logPrint("Startup delay " + simController::startupDelay.to_string() + " complete", LOG_IMPORTANT);
    bool timerRunning = false;
    struct timespec now;
    struct timespec start;
    simController::advanceStartupPhase("systemCWatchdog");
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
            if (!timerRunning)
            {
                clock_gettime(CLOCK_MONOTONIC, &start);
                timerRunning = true;
            } else {
                clock_gettime(CLOCK_MONOTONIC, &now);
                uint64_t nseconds = (now.tv_sec * SECS_TO_NANO + now.tv_nsec ) - (start.tv_sec * SECS_TO_NANO + start.tv_nsec);
                if (watchDog::enabled && nseconds > WATCHDOG_TIMEOUT)
                {
                    watchDog::isTimeout = true;
                    log_.logPrint("Watchdog timeout - timeout" + std::to_string(nseconds), LOG_IMPORTANT);
                    lg.statusPrint();
                    Q_ASSERT_NODUMP(false, "Simulation stuck Watchdog timeout");
                }
            }
        }
        if (eot.isEndOfTest())
        {
            wait(sc_time(1, SC_US));
            sc_stop();  // this is how we stop the simulation
        }
    }
}

