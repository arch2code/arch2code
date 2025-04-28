// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <boost/program_options.hpp>
#include <string>
#include "top.h"
#include "tracker.h"
#include <memory>
#include "testController.h"
#include "instanceFactory.h"
#include "logging.h"

using namespace boost::program_options;

std::string cmdidPrt(int cmdid)
{
    std::stringstream ss;
    ss << "cmd:0x" << std::hex << std::setw(2) << std::setfill('0') << cmdid;
    return(ss.str());
}
std::string tagPrt(int tag)
{
    std::stringstream ss;
    ss << "tag:0x" << std::hex << std::setw(2) << std::setfill('0') << tag;
    return(ss.str());
}

int sc_main(int argc, char* argv[])
{
    logging &lg = logging::GetInstance(); 
    lg.setDefaultVerbosity(VERBOSITY_LOW);
    //instanceFactory::registerInstance("top.uProducer", "model");
    //instanceFactory::registerInstance("top.uConsumer", "model");
    //instanceFactory::registerInstance("uTop", "model");
    testController &controller = testController::GetInstance();
    controller.set_test_names({ 
        // all tests should be listed here
        "test_axird0",
        "test_axird1",
        "test_axiwr0",
        "test_axiwr1",
        "test_axiwr2",
        "test_axiwr3"
        });
    std::shared_ptr<blockBase> uTop = instanceFactory::createInstance("", "uTop", "top", "");
    // start simulation
    sc_start();
    return(0);
}
