#ifndef SIMPLE_IP_H
#define SIMPLE_IP_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import simple_ip.base;
#include "apb_channel.h"
#include "push_ack_channel.h"
#include "apb_port_thunker.h"
#include "push_ack_port_thunker.h"
#include "ipVariantConfig.h"
import shared_types;
using namespace shared_types_ns;
import simple_ip;
using namespace simple_ip_ns;
import ip;
using namespace ip_ns;
//contained instances base module imports
import apbDecode.base;
import dataGen.base;
import ip.base;

SC_MODULE(simple_ip), public blockBase, public simple_ipBase
{
private:

public:
    // channels
    // Non-parameterized producer -> uIp.ipDataIf boundary
    push_ack_channel< simpleData8St > out;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uIp;

    //instances contained in block
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<dataGenBase> uDataGen;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp;

    // cross-interface thunkers
    push_ack_port_thunker<simpleData8St, ipDataSt<ipVariant0Config>> thunker_out_uIp;
    apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt> thunker_apbReg_uIp_uIp;

    simple_ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simple_ip() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //SIMPLE_IP_H
