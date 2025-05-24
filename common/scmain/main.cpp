// copyright QiStor 2022

#include "systemc.h"
#include <boost/program_options.hpp>
#include <string>
#include <random>
#include "logging.h"
#include <thread>
#include "tagTrackers.h"
#include "randFactory.h"
#include <csignal>
#include <chrono>
#include <sys/utsname.h>
#include <filesystem>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "synchLock.h"
#include "simController.h"

#if defined(VERILATOR) || defined(VCS)
#include "vl_wrap.h"
#endif

#ifdef VERILATOR
#include "vl_tracer.h"
#endif

#ifdef VCS
extern "C" void VcsSetExitFunc(int (*)(int));

int exit_handler(int flag) {
    exit(errorCode::getExitCode());
}
#endif

static std::string VERSION = "build " __DATE__ " "  __TIME__;
static std::string COPYRIGHT = "Copyright QiStor, Inc. 2022-2024";
int try_sc_start(bool noLimit, const sc_time scMaxRunTime);
void configureLogging(verbosity_e verbosity, std::vector<std::string> &blockVerbosity);
void testStructs(void);
namespace po = boost::program_options;

void signalHandler(int signum) {
    std::cout << "Interrupt signal (" << signum << ") received." << std::endl;
    logging::GetInstance().statusPrint();
    logging::GetInstance().trackerDump();
    // Perform any necessary cleanup here
    // For example, close files, release resources, etc.
     // Exit the program
    exit(signum);
}

int sc_main(int argc, char* argv[])
{
    logging &lg = logging::GetInstance();
    testStructs();
    // cmd line & config
    std::string logfile;
    bool unbufferedLogs = false;
    bool log = true;    
    bool enableTimeStamp = false;
    std::vector<std::string> blockVerbosity;
    verbosity_e verbosity = VERBOSITY_MEDIUM;
    verbosity_e instVerbosity = VERBOSITY_UNKNOWN;
    std::string verbosityStr;
    std::string instVerbosityStr;
    verbosity_e tempVerbosity = VERBOSITY_UNKNOWN;
    std::string testBenchName;
    std::shared_ptr<testBenchConfigBase> testBench;
    std::string configFile;
    bool vlTrace = false;
    std::filesystem::path execPath{argv[0]};
    std::string execName = execPath.filename().string();
#ifdef VCS
    #define STR(s) #s
    #define XSTR(s) STR(s)
    vlInst = XSTR(VL_INST);
    vlType = XSTR(VL_TYPE);
    simController::vlTandem = VL_TANDEM ? true : false;

    VcsSetExitFunc(exit_handler);
    synchLockFactoryRegistery::getInstance().setHierarchyPrefix("sc_main");
#endif

#ifdef VERILATOR
    vl_tracer *vlTracer;
#endif
    try
    {
        // Stage 1: Parse only testBench name
        po::options_description stage1Options{"Command"};
        stage1Options.add_options()
            ("help,h", "Help screen")
            ("testBench", po::value<std::string>(&testBenchName), "Test bench selection")
            ("subargs", po::value<std::vector<std::string> >(), "Arguments for command");

        po::positional_options_description pos;
        pos.add("testBench", 1).
            add("subargs", -1);

        po::variables_map vm;

        po::parsed_options parsed1 = po::command_line_parser(argc, argv).
            options(stage1Options).
            positional(pos).
            allow_unregistered().
            run();

        // Store Stage 1 results
        po::store(parsed1, vm);
        po::notify(vm);

        std::cout << "TestBench Selected: " << testBenchName << "\n";
        testBench = testBenchConfigFactory::createTestBench(testBenchName);
        if (!testBench) {
            std::cout << "Invalid testBench selected\n";
            return 1;
        }

        // Stage 2: Parse remaining options
        po::options_description allOptions{"All Options"};
        testBench->addProgramOptions(allOptions);
        simController::addProgramOptions(allOptions);

        po::options_description logging{"Logging"};
        logging.add_options()
            ("log", po::value<std::string>(&logfile)->default_value("")->implicit_value(execName + ".log"), "Log file")
            ("config", po::value<std::string>(&configFile)->default_value( testBenchName + ".cfg"), "Config file")
            ("enableTimeStamp", po::bool_switch(&enableTimeStamp)->default_value(false), "Enable logging of timestamp")
            ("verbosity", po::value<std::string>(&verbosityStr)->default_value(""), "verbosity")
            ("instVerbosity", po::value<std::string>(&instVerbosityStr)->default_value(""), "vlInst verbosity")
            ("unbufferedLogs",  po::bool_switch(&unbufferedLogs)->default_value(false), "flush every log write immediately");
        allOptions.add(logging);

        po::options_description fileOptions{"File"};
        fileOptions.add_options()
            ("blockVerbosity", po::value<std::vector<std::string>>(&blockVerbosity)->multitoken()->composing(), "allow the verbosity of debug to change per block");

        // Collect all the unrecognized options from the first pass. This will include the
        // (positional) command name, so we need to erase that.
        std::vector<std::string> opts = po::collect_unrecognized(parsed1.options, po::include_positional);
        if (vm.count("testBench")) {
            opts.erase(opts.begin()); // remove positional argument if it was provided
        }
        po::store(po::command_line_parser(opts).options(allOptions).run(), vm);

        if (vm.count("config"))
        {
            po::options_description configFileOptions;
            configFileOptions.add(allOptions).add(fileOptions);
            std::ifstream ifs{vm["config"].as<std::string>().c_str()};
            if (ifs) {
                po::store(po::parse_config_file(ifs, configFileOptions), vm);
            }
        }
        notify(vm);
        if (!testBench->handleProgramOptions(vm)) {
            return(2);
        }
        if (!simController::handleProgramOptions(vm)) {
            return(2);
        }
        if (!simController::handleTestBenchParams(vm, testBench)) {
            return(2);
        }
        // Table showing how log levels and Verbosity Levels are handled
        // The verblevel is mapped directly onto a log level.
        // Default verbosity level is 2(HIGH) which equates to anything of log level normal (or higher)
        // will be logged
        //
        //Log Level          ------------------ Verbosity Level -------------------
        //                   LOW(0)          MEDIUM(1)      HIGH(2)         FULL(3)
        //LOG_ALWAYS (0)     Printed         Printed        Printed         Printed
        //LOG_IMPORTANT (1)  Not Printed     Printed        Printed         Printed
        //LOG_NORMAL (2)     Not Printed     Not Printed    Printed         Printed
        //LOG_DEBUG (3)      Not Printed     Not Printed    Not Printed     Printed

        if (!verbosityStr.empty())
        {
            if ((tempVerbosity = lg.verbosityDecode(verbosityStr)) != VERBOSITY_UNKNOWN) {
                verbosity = tempVerbosity;
            } else {
                std::cout << "Invalid verbosity '"  << verbosityStr << "'. Using default verbosity " << verbosity << std::endl;
            }
        }
        if (!instVerbosityStr.empty())
        {
            if ((tempVerbosity = lg.verbosityDecode(instVerbosityStr)) != VERBOSITY_UNKNOWN) {
                instVerbosity = tempVerbosity;
            } else {
                return(2);
            }
        }
        if (vm.count("help")) {
            std::cout << "Help for testbench:" << testBenchName << '\n';
            std::cout << allOptions << '\n';
            std::cout << "Config file only options\n";
            std::cout << fileOptions << '\n';
            return(2);
        }
        configureLogging(verbosity, blockVerbosity);

        logfile = vm["log"].as<std::string>();
        if (logfile.compare("") == 0)
        {
            log = false;
        }

    }
    catch (const po::error &ex)
    {
        std::cerr << ex.what() << '\n' << errorCode::getErrorString() << std::endl;
        return(2);
    }
    std::ofstream logOut;
    auto cout_buff = std::cout.rdbuf();
    auto cerr_buff = std::cout.rdbuf();

    if (log) {
        std::cout << "Logging redirected to: " << logfile << endl;
        logOut.open(logfile);
        std::cout.rdbuf(logOut.rdbuf()); // redirect stdout to log
        std::cerr.rdbuf(logOut.rdbuf()); // redirect stderr to log
    }
    if (unbufferedLogs) {
        std::cout  << std::unitbuf;   // turn on “flush on every <<”
        std::cerr  << std::unitbuf;
    }
    // Build & copyright info
    {
        std::string logHeaderStr;
        std::string sysInfoStr;
        struct utsname unameData;
        uname(&unameData);
        sysInfoStr = std::string(unameData.sysname) + "/" + std::string(unameData.machine) + ", " +
                "SystemC " + sc_core::sc_release();
        logHeaderStr = "\n" + testBenchName + " " + VERSION + " (" + sysInfoStr + ") " + COPYRIGHT + "\n";
        std::cout << logHeaderStr << std::endl;
    }

    std::cout << "Cmd line: ";
    for(auto i = 0; i < argc; i++) {
        std::cout << argv[i] << " ";
    }
    std::cout << endl;

    std::cout << "Seed: 0x" << std::hex << randFactory::gSeed << endl;
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    // If a valid verilated instance is provided from command line, register with factory

    lg.setTimeStampPrint(enableTimeStamp);
    trackerInit(); // setup the tag trackers
    // declare and initialize tasks

#if defined(VERILATOR)
    if(simController::vlTrace) {
        vlTracer = new vl_tracer("vlTracer");
    }
#endif


    testBench->createTestBench();
    std::stringstream exitMsg;
    //std::cout << instanceFactory::dumpInstances();
    // Validate the instance hierarchy registration immediately after top is constructed
    std::string vlInst = simController::vlInst;
    if(vlInst != "" && !instanceFactory::getInstance(vlInst)) {
        errorCode::fail("Primary instance not found");
        goto exit_goto;
    }
    if (try_sc_start(false, SC_ZERO_TIME) != 0) {
        goto exit_goto;
    }
    simController::setTimingMode();
    if (instVerbosity != VERBOSITY_UNKNOWN) {
        instanceFactory::setLogging(instVerbosity);
    }
    if (vlInst != "" && simController::vlTandem) {
        std::cout << "Synchlock Report. SynchLocks associated with " << vlInst << '\n';
        std::cout << synchLockFactoryRegistery::getInstance().dumpInstanceLocks(vlInst);
    }

    simController::advanceStartupPhase("main"); // get our vote in

#if defined(VERILATOR)
    if(simController::vlTrace) {
        std::shared_ptr<blockBase> dut_wrp;
        std::string traceInst = vlInst;
        if(simController::vlTandem) traceInst.append(".verif");
        dut_wrp = std::dynamic_pointer_cast<blockBase>(instanceFactory::getInstance(traceInst));
        dut_wrp->vl_trace(vlTracer->m_tfp, 3);
        vlTracer->open_trace();
    }
#endif
    while (simController::getStartupPhase() < STARTUP_SIMSTART) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    // start simulation
    if ( simController::maxRuntimeUS ) {
        sc_time scMaxRunTime = sc_time(simController::maxRuntimeUS, SC_US);
        try_sc_start(false, scMaxRunTime);
    } else {
        try_sc_start(true, SC_ZERO_TIME);
    }
#if defined(VERILATOR)
    if(vlTrace) {
        vlTracer->close_trace();
    }
#endif

#if defined(VERILATOR) and defined(VL_COV)
    if (vlInst != "" ) {
        Verilated::threadContextp()->coveragep()->write("build/coverage.dat");
    }
#endif

    logging::GetInstance().final();
    testBench->final();
    exitMsg << errorCode::getErrorString() << endl;
    testBench->exitSummary();
    //cleanup original output buffs
exit_goto:
    std::cout << exitMsg.str(); // output to log
    std::cout.rdbuf(cout_buff);
    std::cerr.rdbuf(cerr_buff);
    // repeat for console
    std::cout << exitMsg.str();
    int exit_code = errorCode::getExitCode();
    if( exit_code !=0 ) std::cout << "exit code : " << exit_code << " " << endl;

    return(exit_code);
}


void configureLogging(verbosity_e verbosity, std::vector<std::string> &blockVerbosity)
{
    logging &lg = logging::GetInstance();
    lg.setDefaultVerbosity(verbosity);
    // logging setup
    if (blockVerbosity.size())
    {
        for(auto dbgModule: blockVerbosity)
        {
            size_t equalsPos = dbgModule.find(' ');
            if (equalsPos != std::string::npos && equalsPos > 0 && equalsPos < dbgModule.size() - 1) {
                std::string moduleName = dbgModule.substr(0, equalsPos);
                std::string verbosityStr = dbgModule.substr(equalsPos + 1);
                verbosity_e tempVerbosity;
                if ((tempVerbosity = lg.verbosityDecode(verbosityStr)) != VERBOSITY_UNKNOWN) {
                    verbosity = tempVerbosity;
                } else {
                    std::cout << "Invalid block verbosity '"  << verbosityStr << " (" << moduleName << ")'. Using default verbosity " << verbosity << std::endl;
                }
                lg.addBlock(moduleName, verbosity);
            }
        }
    }
}

int try_sc_start(bool noLimit, const sc_time scMaxRunTime)
{
    std::string simEnd;
    bool isEnumeration = false;
    auto start = std::chrono::system_clock::now();
    if (noLimit ) {
        std::cout << "===== Simulation Start =====" << endl;
        simEnd = "===== Simulation End =====";
    } else if (scMaxRunTime != SC_ZERO_TIME) {
        std::cout << "Simulation Time Limit: " << scMaxRunTime << endl;
        simEnd = "===== Simulation End =====";
    } else {
        isEnumeration = true;
        std::cout << "Simulation Enumeration" << endl;
        simEnd = "Enumeration End";
    }
    int exit_code = 0;
    try {
        if (noLimit) {
            sc_start();
            exit_code = errorCode::getExitCode();
        } else {
            sc_start(scMaxRunTime);
            // Return with error status code if simulation limit is reached before expected end
            if (!isEnumeration && sc_time_stamp() >= scMaxRunTime) {
                simEnd = "Simulation has reached the maximum specified time limit !!!";
                errorCode::fail(simEnd);
            }
            exit_code = (isEnumeration) ? 0 : errorCode::getExitCode();
        }
        std::cout << simEnd << endl;
    } catch (std::exception& e) {
        std::cout << std::string("Caught exception ")+e.what() << endl;
        errorCode::fail("Caught exception during simulation.");
        exit_code = 1;
    } catch (...) {
        std::cout << "Caught exception during simulation." << endl;
        errorCode::fail("Caught exception during simulation.");
        exit_code = 1;
    }//endtry
    if (!isEnumeration)
    {
        auto end = std::chrono::system_clock::now();
        std::chrono::duration<double> elapsed_seconds = end - start;
        std::stringstream exitMsg;
        exitMsg << "elapsed time: " << elapsed_seconds.count() << "s " << "sc_timestamp: " << sc_time_stamp();
        errorCode::setErrorString(exitMsg.str());
    }
    return exit_code;
}
