// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <boost/program_options.hpp>
#include <string>
#include "testContainer.h"
#include "encoderBase.h"
#include "testController.h"
#include "tracker.h"

using namespace boost::program_options;

std::string cmdidPrt(int cmdid)
{
    std::stringstream ss;
    ss << "cmdid:0x" << std::hex << std::setw(3) << std::setfill('0') << cmdid;
    return(ss.str());
}

int sc_main(int argc, char* argv[])
{
    logging &log = logging::GetInstance();
    log.setDefaultVerbosity(VERBOSITY_HIGH);
    encodeTagTest test;
    for(int i = 0 ; i < 0x13f; i++)
    {
        auto [tag, type] = test.decode(i);
        int result = test.encode(tag, type);
        if (result != i)
        {
            std::cout << "Error: " << i << " " << result << std::endl;
        }
    }
    encodeTagTest2 test2;
    for(int i = 0 ; i < 0xffff; i++)
    {
        auto [tag, type] = test2.decode(i);
        int result = test2.encode(tag, type);
        if (result != i)
        {
            std::cout << "Error: " << i << " " << result << std::endl;
        }
    }
    trackerCollection &trackers = trackerCollection::GetInstance();
    trackers.addTracker("cmdid", std::make_shared<tracker<simpleString>> (10, "cmdid", "C#", cmdidPrt));
    testController &controller = testController::GetInstance();
    controller.set_test_names({ 
        // all tests should be listed here
        "test1", 
        "test2", 
        "src_trans_dest_trans_length", 
        "src_clock_dest_trans_length", 
        "src_trans_dest_clock_length", 
        "src_trans_dest_trans_cmdidtracker", 
        "src_clock_dest_trans_cmdidtracker", 
        "src_trans_dest_clock_cmdidtracker", 
        "src_trans_dest_trans_rv_size", 
        "src_clock_dest_trans_rv_size", 
        "src_trans_dest_clock_rv_size", 
        "src_trans_dest_trans_rv_tracker", 
        "src_clock_dest_trans_rv_tracker", 
        "src_trans_dest_clock_rv_tracker" 
        });
    std::shared_ptr<blockBase> uTop = instanceFactory::createInstance("", "uTop", "top", "");

    // start simulation
    sc_start();
    return(0);
}
