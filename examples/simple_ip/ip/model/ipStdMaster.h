#ifndef IPSTDMASTER_H
#define IPSTDMASTER_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ipStdMaster
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import ipStdMaster.base;
#include "apb_channel.h"
import ip;
using namespace ip_ns;

SC_MODULE(ipStdMaster), public blockBase, public ipStdMasterBase
{
private:

public:

    ipStdMaster(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdMaster() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //IPSTDMASTER_H
