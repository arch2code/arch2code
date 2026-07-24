#ifndef IPSTDTOP_H
#define IPSTDTOP_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ipStdTop
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import ipStdTop.base;
#include "apb_channel.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "ipVariantConfig.h"
import ip;
using namespace ip_ns;
import ipTop;
using namespace ipTop_ns;
//contained instances base module imports
import ipStdMaster.base;
import ipStdDriver.base;
import ipStdDecode.base;
import ip.base;

SC_MODULE(ipStdTop), public blockBase, public ipStdTopBase
{
private:

public:
    // channels
    // Register bus the ip block consumes
    apb_channel< ipRegAddrSt, ipRegDataSt > apbOut;
    // Non-parameterized container boundary interface for uIp.ipDataIf
    push_ack_channel< ipStdData8St > out0;
    // Register bus the ip block consumes
    apb_channel< ipRegAddrSt, ipRegDataSt > ipReg_uIp;

    //instances contained in block
    std::shared_ptr<ipStdMasterBase> uIpStdMaster;
    std::shared_ptr<ipStdDriverBase> uIpStdDriver;
    std::shared_ptr<ipStdDecodeBase> uIpStdDecode;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp;

    // cross-interface thunkers
    push_ack_port_thunker<ipStdData8St, ipDataSt<ipVariant0Config>> thunker_out0_uIp;

    ipStdTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //IPSTDTOP_H
