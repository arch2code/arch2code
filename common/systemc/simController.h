#ifndef SIMCONTROLLER_H
#define SIMCONTROLLER_H
// copyright QiStor 2025
#include <string>
#include "systemc.h"
#include <boost/program_options.hpp>
#include "timedDelay.h"
#include "testBenchConfigBase.h"

namespace po = boost::program_options;
enum startupPhaseEnum {STARTUP_PRE_SIM, STARTUP_SIMSTART, STARTUP_DONE};

// this class is intended to be the global controller for the simulation
class simController
{
public:
    static std::string testBenchName;
    static std::string vlInst; // name of instance that is focus of the test
    static std::string vlType; // type of instance that is focus of the test
    static bool vlTandem; // is the instance in tandem mode
    static bool vlTrace; // enable VCD trace dump
    static sc_time scMaxRunTime;  
    static sc_time startupDelay;
    static uint64_t startupDelayns;
    static sc_time watchdogTimeout;
    static uint64_t delayNSec; 
    static timedDelayMode delayMode;
    static float maxRuntimeUS;
    static volatile startupPhaseEnum startupPhase;
    static std::atomic<int> startupCounter;
    static int startupVoters;
    static bool configDone;

    // startup control
    static startupPhaseEnum getStartupPhase(void) {return startupPhase;};
    static void advanceStartupPhase(std::string name);
    static void setStartupVoters(int startupVoters_) {startupVoters = startupVoters_;};
    static void waitConfig(void)
    {
        while( !configDone )
        {
            wait(sc_time(10, SC_NS));
        }
    }
    static void setConfigDone(void) {configDone=true;};
    
    // parameter handling
    static bool addProgramOptions(po::options_description &options);
    static bool handleProgramOptions(po::variables_map &vm);
    static void setTimingMode(void);
    static bool handleTestBenchParams(po::variables_map &vm, std::shared_ptr<testBenchConfigBase> testBench);
private: 
};
#endif //SIMCONTROLLER_H
