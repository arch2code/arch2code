#ifndef IP_TOP_H
#define IP_TOP_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import ip_top.base;
#include "apb_channel.h"
#include "push_ack_channel.h"
#include "apb_port_thunker.h"
#include "push_ack_port_thunker.h"
#include "ipVariantConfig.h"
#include "srcVariantConfig.h"
#include "ip_test_ipVariantConfig.h"
import shared_types;
using namespace shared_types_ns;
import ip_top;
using namespace ip_top_ns;
import src;
using namespace src_ns;
import ip;
using namespace ip_ns;
import ipBridge;
using namespace ipBridge_ns;
//contained instances base module imports
import apbDecode.base;
import src.base;
import ip.base;
import ipBridge.base;

SC_MODULE(ip_top), public blockBase, public ip_topBase
{
private:

public:
    // channels
    // Non-parameterized container boundary interface for uSrc.out0 -> uIp0.ipDataIf
    push_ack_channel< srcOut0BoundarySt > out0;
    // Non-parameterized container boundary interface for uSrc.out1 -> uIp1.ipDataIf
    push_ack_channel< srcOut1BoundarySt > out1;
    // Non-parameterized container boundary interface for uSrc.out0 -> uIp0.ipDataIf
    push_ack_channel< srcOut0BoundarySt > out2;
    // Non-parameterized container boundary interface for uSrc.out1 -> uIp1.ipDataIf
    push_ack_channel< srcOut1BoundarySt > out3;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBridge;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uIp0;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uIp1;

    //instances contained in block
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<srcBase<srcDefaultConfig>> uSrc;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp0;
    std::shared_ptr<ipBase<ip_test_ipVariant1Config>> uIp1;
    std::shared_ptr<ipBridgeBase> uBridge;

    // cross-interface thunkers
    push_ack_port_thunker<srcOut0BoundarySt, srcOut0St<srcDefaultConfig>> thunker_out0_uSrc;
    push_ack_port_thunker<srcOut0BoundarySt, ipDataSt<ipVariant0Config>> thunker_out0_uIp0;
    push_ack_port_thunker<srcOut1BoundarySt, srcOut1St<srcDefaultConfig>> thunker_out1_uSrc;
    push_ack_port_thunker<srcOut1BoundarySt, ipDataSt<ip_test_ipVariant1Config>> thunker_out1_uIp1;
    push_ack_port_thunker<srcOut0BoundarySt, srcOut0St<srcDefaultConfig>> thunker_out2_uSrc;
    push_ack_port_thunker<srcOut0BoundarySt, data8St> thunker_out2_uBridge;
    push_ack_port_thunker<srcOut1BoundarySt, srcOut1St<srcDefaultConfig>> thunker_out3_uSrc;
    push_ack_port_thunker<srcOut1BoundarySt, data70St> thunker_out3_uBridge;
    apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt> thunker_apbReg_uIp0_uIp0;
    apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt> thunker_apbReg_uIp1_uIp1;

    ip_top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip_top() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //IP_TOP_H
