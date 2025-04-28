// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <boost/program_options.hpp>
#include <string>
#include "top.h"

using namespace boost::program_options;

int sc_main(int argc, char* argv[])
{
    logging &log = logging::GetInstance();
    log.setDefaultVerbosity(VERBOSITY_HIGH);
    std::shared_ptr<blockBase> uTop = instanceFactory::createInstance("", "uTop", "top", "");
    // start simulation
    sc_start();
    return(0);
}
