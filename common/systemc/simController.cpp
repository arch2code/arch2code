//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "q_assert.h"

#include "simController.h"
#include "instanceFactory.h"
#include "workerThread.h"
#include "watchDog.h" 

std::string simController::testBenchName;
std::string simController::vlInst; 
std::string simController::vlType; 
bool simController::vlTandem; 
bool simController::vlTrace; 
sc_time simController::scMaxRunTime;  
sc_time simController::startupDelay = sc_time(1, SC_NS);
uint64_t simController::startupDelayns;
sc_time simController::watchdogTimeout;
uint64_t simController::delayNSec; 
timedDelayMode simController::delayMode;
float simController::maxRuntimeUS;
volatile startupPhaseEnum simController::startupPhase = STARTUP_PRE_SIM;
std::atomic<int> simController::startupCounter = 0;
int simController::startupVoters = 0;
bool simController::configDone = false;

bool simController::handleProgramOptions(po::variables_map &vm)
{
    // handle seed
    if (vm.count("seed")) {
        std::string seed_str = vm["seed"].as<std::string>();
        try {
            randFactory::setSeed(std::stoul(seed_str, nullptr, 0));
        } catch(std::invalid_argument&) {
            if ( seed_str == "random" ) {
                std::random_device rd;
                randFactory::setSeed(rd());
            } else {
                cout << "Invalid seed format" << endl;
                return(false);
            }
        }
    }
    if (vm.count("delayMode")) {
        static const std::map<std::string, timedDelayMode> delayModeMap = {
            {"fixedInit", timedDelayMode::TIMED_DELAY_FIXED_INIT},
            {"randInit", timedDelayMode::TIMED_DELAY_RAND_INIT},
            {"randFull", timedDelayMode::TIMED_DELAY_RAND_FULL}
        };
        auto it = delayModeMap.find(vm["delayMode"].as<std::string>());
        if (it != delayModeMap.end()) {
            delayMode = it->second;
        } else {
            cout << "Invalid delayMode value specified" << endl;
            return(false);
        }
    } else {
        delayMode = timedDelayMode::TIMED_DELAY_FIXED_INIT;
    }
    #ifndef A2CPRO
    Q_ASSERT_CTX_NODUMP(vlTandem == false, "simController", "Tandem mode not supported");
    #endif

    startupDelay = sc_time(startupDelayns, SC_NS); //this is the simulation time delay between worker threads and systemC

    uint64_t nsec = 0;
    if (vm.count("delay")) nsec = vm["delay"].as<uint64_t>();
    if (vlInst != "" ) {
        if (vlTandem) {
            instanceFactory::registerInstance(vlInst, "tandem");
            instanceFactory::setInstanceFactoryMode(INSTANCE_FACTORY_PRIMARY_TYPE, vlType);
        } else {
            instanceFactory::registerInstance(vlInst, vlType);
        }
        // scale the watchdog timeout based on the delay mode
        if (nsec > 0) {
            watchDog::timeout = watchDog::timeout * nsec;
        } else if (vlType == "verif") {
            watchDog::timeout = watchDog::timeout * 5;
        }
    } else if (nsec > 0) {
        watchDog::timeout = watchDog::timeout * nsec;
    }
    cout << "Watchdog timeout: " << watchDog::timeout << endl;


    return true;
}
bool simController::addProgramOptions(po::options_description &options)
{
    options.add_options()
#ifndef VCS
        ("vlInst", po::value<std::string>(&vlInst), "Primary Instance Hierarchy")
        ("vlType", po::value<std::string>(&vlType)->default_value("verif"), "Primary Instance object type")
        ("vlTandem", po::bool_switch(&vlTandem), "Primary instance in tandem mode")
        ("vlTrace", po::bool_switch(&vlTrace)->default_value(false), "Enable VCD trace dump")
#endif
        ("delay", po::value<uint64_t>(&delayNSec), "Set delay in nsec for named instance or all")
        ("delayMode", po::value<std::string>(), "Set delay mode for named instance [fixedInit, randInit, randFull]")
        ("scTimeLimit", po::value<float>(&maxRuntimeUS)->default_value(0.0), "SystemC time limit (in microseconds)")
        ("startupDelay", po::value<uint64_t>(&startupDelayns)->default_value(100), "simulation startup delay in ns")
        ("seed", po::value<std::string>(), "Random Number Generator Seed")
        ("param", po::value<std::vector<std::string>>()->composing(), "Parameter in the form key,value. Multiple --param options allowed");
    return true;
}

void simController::setTimingMode(void)
{
    if (vlInst != "" ) {
        if (delayNSec > 0) {
            instanceFactory::setTimed(delayNSec, false, delayMode);
        }
    } else if (delayNSec > 0) {
        instanceFactory::setTimed(delayNSec, true, delayMode);
    }
}

void simController::advanceStartupPhase(std::string name) 
{
    static logging &log_ = logging::GetInstance();
    log_.logDirect( std::string("advanceStartupPhase ") + name + " phase:" + std::to_string(startupPhase) + " count:" + std::to_string(startupCounter) );
    startupCounter++;
    if (startupCounter>=startupVoters)
    {
        startupPhase = (startupPhaseEnum)(startupPhase + 1);
        workerFactory::notifyAll();
        startupCounter = 0;
    }
}

bool simController::handleTestBenchParams(po::variables_map &vm, std::shared_ptr<testBenchConfigBase> testBench)
{
    if (vm.count("param")) {
        auto paramStrings = vm["param"].as<std::vector<std::string>>();
        for (const auto &entry : paramStrings) {
            // Assume each entry is in the form "key,value"
            auto pos = entry.find(',');
            if (pos != std::string::npos) {
                std::string key = entry.substr(0, pos);
                std::string value = entry.substr(pos + 1);
                if (testBench->isValidParam(key)){
                    uint64_t maxVal = testBench->getParam(key);
                    // Check that the parameter is valid and that a value exists.
                    if (maxVal == 0 || value.empty()) {
                        std::cerr << "Invalid parameter: " << key << ". Ignoring\n";
                        return false;
                    } else {
                        try {
                            uint64_t val = std::stoul(value);
                            if (val > maxVal) {
                                std::cerr << "Invalid parameter value: " << key << ". Value " << val << " exceeds maximum value " << maxVal << ". Ignoring\n";
                                return false;
                            } else {
                                testBench->addParam(key, val);
                                std::cout << "Parameter " << key << " set to " << val << std::endl;
                            }
                        }
                        catch (const std::exception &ex) {
                            std::cerr << "Error converting parameter value for " << key << ": " << ex.what() << ". Ignoring\n";
                            return false;
                        }
                    }
                } else {
                    std::cerr << "Invalid parameter: " << key << ". Ignoring\n";
                    return false;
                }
            } else {
                std::cerr << "Invalid parameter format: " << entry << ". use key,value\n";
                return false;
            }
        }
    }
    return true;
}