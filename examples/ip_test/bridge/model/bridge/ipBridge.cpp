//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ipBridge.h"
import bridgeApbDecode.base;
import ip.base;
SC_HAS_PROCESS(ipBridge);

// === Block factory registration (ipBridge) ===
void register_ipBridge_variants() {
    instanceFactory::registerBlock("ipBridge_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipBridge>(blockName, variant, bbMode)); }, "", "ip_test");
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
        ,uBridgeAPBDecode(std::dynamic_pointer_cast<bridgeApbDecodeBase>(instanceFactory::createInstance(name(), "uBridgeAPBDecode", "bridgeApbDecode", "", "ip_test")))
        ,uBridgeIp0(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uBridgeIp0", "ip", "variant0", "ip_test")))
        ,uBridgeIp1(std::dynamic_pointer_cast<ipBase<ipVariant1Config>>(instanceFactory::createInstance(name(), "uBridgeIp1", "ip", "variant1", "ip_test")))
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

