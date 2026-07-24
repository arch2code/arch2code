#ifndef IPSTDDRIVER_H
#define IPSTDDRIVER_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ipStdDriver
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import ipStdDriver.base;
#include "push_ack_channel.h"
import ipTop;
using namespace ipTop_ns;

SC_MODULE(ipStdDriver), public blockBase, public ipStdDriverBase
{
private:

public:

    ipStdDriver(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdDriver() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //IPSTDDRIVER_H
