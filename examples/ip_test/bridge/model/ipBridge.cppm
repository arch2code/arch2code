//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipBridge --mode=module
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
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module ipBridge.block;
import ipBridge.base;
import ipBridge.ip.config;
import ipBridge;
import common_shared_types;
import ip;
import ipBridge_bridgeApbDecode.base;
import ip.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ipBridge_ns;
using namespace common_shared_types_ns;
using namespace ip_ns;
export SC_MODULE(ipBridge), public blockBase, public ipBridgeBase
{
private:

public:
    // channels
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBridgeIp0;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBridgeIp1;

    //instances contained in block
    std::shared_ptr<bridgeApbDecodeBase> uBridgeAPBDecode;
    std::shared_ptr<ipBase<ipVariant0Config>> uBridgeIp0;
    std::shared_ptr<ipBase<ipBridge_ipVariant1Config>> uBridgeIp1;

    // cross-interface thunkers
    apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt> thunker_apbReg_uBridgeIp0_uBridgeIp0;
    apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt> thunker_apbReg_uBridgeIp1_uBridgeIp1;
    push_ack_port_thunker<data8St, ipDataSt<ipVariant0Config>> thunker_uBridgeIp0;
    push_ack_port_thunker<data70St, ipDataSt<ipBridge_ipVariant1Config>> thunker_uBridgeIp1;

    ipBridge(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipBridge() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(ipBridge);

// === Block factory registration (ipBridge) ===
void register_ipBridge_variants() {
    instanceFactory::registerBlock("ipBridge_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipBridge>(blockName, variant, bbMode)); }, "", "ipBridge");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ipBridge_registered = (register_ipBridge_variants(), 0);
} // namespace
// === End block factory registration ===

ipBridge::ipBridge(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipBridge", name(), bbMode)
        ,ipBridgeBase(name(), variant)
        ,apbReg_uBridgeIp0("ip_apbReg_uBridgeIp0", "bridgeApbDecode")
        ,apbReg_uBridgeIp1("ip_apbReg_uBridgeIp1", "bridgeApbDecode")
        ,uBridgeAPBDecode(std::dynamic_pointer_cast<bridgeApbDecodeBase>(instanceFactory::createInstance(name(), "uBridgeAPBDecode", "bridgeApbDecode", "", "ipBridge")))
        ,uBridgeIp0(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uBridgeIp0", "ip", "variant0", "ipBridge")))
        ,uBridgeIp1(std::dynamic_pointer_cast<ipBase<ipBridge_ipVariant1Config>>(instanceFactory::createInstance(name(), "uBridgeIp1", "ip", "variant1", "ipBridge")))
        ,thunker_apbReg_uBridgeIp0_uBridgeIp0("thunker_apbReg_uBridgeIp0_uBridgeIp0", apbReg_uBridgeIp0, uBridgeIp0->regs, name())
        ,thunker_apbReg_uBridgeIp1_uBridgeIp1("thunker_apbReg_uBridgeIp1_uBridgeIp1", apbReg_uBridgeIp1, uBridgeIp1->regs, name())
        ,thunker_uBridgeIp0("thunker_uBridgeIp0", data8In, uBridgeIp0->ipDataIf, name())
        ,thunker_uBridgeIp1("thunker_uBridgeIp1", data70In, uBridgeIp1->ipDataIf, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uBridgeAPBDecode->apbReg(apbReg);
    // instance to instance connections via channel
    uBridgeAPBDecode->apbReg_uBridgeIp0(apbReg_uBridgeIp0);
    uBridgeAPBDecode->apbReg_uBridgeIp1(apbReg_uBridgeIp1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

