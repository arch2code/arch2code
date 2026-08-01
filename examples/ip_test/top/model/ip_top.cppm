//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
#include "push_ack_channel.h"
#include "apb_port_thunker.h"
#include "push_ack_port_thunker.h"
#include "ipVariantConfig.h"
#include "srcVariantConfig.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module ip_test_ip_top.block;
import ip_test_ip_top.base;
import ip_test.ip.config;
import common_shared_types;
import ip_test_ip_top;
import ip_test_src;
import ip;
import ipBridge;
import ip_test_apbDecode.base;
import ip_test_src.base;
import ip.base;
import ipBridge.base;
using namespace common_shared_types_ns;
using namespace ip_test_ip_top_ns;
using namespace ip_test_src_ns;
using namespace ip_ns;
using namespace ipBridge_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(ip_top), public blockBase, public ip_topBase
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
    std::shared_ptr<srcBase<srcVariantSrc0Config>> uSrc;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp0;
    std::shared_ptr<ipBase<ip_test_ipVariant1Config>> uIp1;
    std::shared_ptr<ipBridgeBase> uBridge;

    // cross-interface thunkers
    push_ack_port_thunker<srcOut0BoundarySt, srcOut0St<srcVariantSrc0Config>> thunker_out0_uSrc;
    push_ack_port_thunker<srcOut0BoundarySt, ipDataSt<ipVariant0Config>> thunker_out0_uIp0;
    push_ack_port_thunker<srcOut1BoundarySt, srcOut1St<srcVariantSrc0Config>> thunker_out1_uSrc;
    push_ack_port_thunker<srcOut1BoundarySt, ipDataSt<ip_test_ipVariant1Config>> thunker_out1_uIp1;
    push_ack_port_thunker<srcOut0BoundarySt, srcOut0St<srcVariantSrc0Config>> thunker_out2_uSrc;
    push_ack_port_thunker<srcOut0BoundarySt, data8St> thunker_out2_uBridge;
    push_ack_port_thunker<srcOut1BoundarySt, srcOut1St<srcVariantSrc0Config>> thunker_out3_uSrc;
    push_ack_port_thunker<srcOut1BoundarySt, data70St> thunker_out3_uBridge;
    apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt> thunker_apbReg_uIp0_uIp0;
    apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt> thunker_apbReg_uIp1_uIp1;

    ip_top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip_top() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(ip_top);

// === Block factory registration (ip_top) ===
void register_ip_top_variants() {
    instanceFactory::registerBlock("ip_top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_top>(blockName, variant, bbMode)); }, "", "ip_test");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ip_top_registered = (register_ip_top_variants(), 0);
} // namespace
// === End block factory registration ===

ip_top::ip_top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip_top", name(), bbMode)
        ,ip_topBase(name(), variant)
        ,out0("ip_out0", "src")
        ,out1("ip_out1", "src")
        ,out2("ipBridge_out2", "src")
        ,out3("ipBridge_out3", "src")
        ,apbReg_uBridge("ipBridge_apbReg_uBridge", "apbDecode")
        ,apbReg_uIp0("ip_apbReg_uIp0", "apbDecode")
        ,apbReg_uIp1("ip_apbReg_uIp1", "apbDecode")
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>(instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "", "ip_test")))
        ,uSrc(std::dynamic_pointer_cast<srcBase<srcVariantSrc0Config>>(instanceFactory::createInstance(name(), "uSrc", "src", "variantSrc0", "ip_test")))
        ,uIp0(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uIp0", "ip", "variant0", "ip_test")))
        ,uIp1(std::dynamic_pointer_cast<ipBase<ip_test_ipVariant1Config>>(instanceFactory::createInstance(name(), "uIp1", "ip", "variant1", "ip_test")))
        ,uBridge(std::dynamic_pointer_cast<ipBridgeBase>(instanceFactory::createInstance(name(), "uBridge", "ipBridge", "", "ipBridge")))
        ,thunker_out0_uSrc("thunker_out0_uSrc", out0, uSrc->out0, name())
        ,thunker_out0_uIp0("thunker_out0_uIp0", out0, uIp0->ipDataIf, name())
        ,thunker_out1_uSrc("thunker_out1_uSrc", out1, uSrc->out1, name())
        ,thunker_out1_uIp1("thunker_out1_uIp1", out1, uIp1->ipDataIf, name())
        ,thunker_out2_uSrc("thunker_out2_uSrc", out2, uSrc->out2, name())
        ,thunker_out2_uBridge("thunker_out2_uBridge", out2, uBridge->data8In, name())
        ,thunker_out3_uSrc("thunker_out3_uSrc", out3, uSrc->out3, name())
        ,thunker_out3_uBridge("thunker_out3_uBridge", out3, uBridge->data70In, name())
        ,thunker_apbReg_uIp0_uIp0("thunker_apbReg_uIp0_uIp0", apbReg_uIp0, uIp0->regs, name())
        ,thunker_apbReg_uIp1_uIp1("thunker_apbReg_uIp1_uIp1", apbReg_uIp1, uIp1->regs, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->cpu_main(cpu_main);
    // instance to instance connections via channel
    uAPBDecode->apbReg_uBridge(apbReg_uBridge);
    uBridge->apbReg(apbReg_uBridge);
    uAPBDecode->apbReg_uIp0(apbReg_uIp0);
    uAPBDecode->apbReg_uIp1(apbReg_uIp1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

