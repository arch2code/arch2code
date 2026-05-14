//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ipBridge.h"
#include "bridgeApbDecodeBase.h"
#include "ipBase.h"
SC_HAS_PROCESS(ipBridge);

// === Block factory registration (ipBridge) ===
void force_link_ipBridge() {}

void register_ipBridge_variants() {
    instanceFactory::registerBlock("ipBridge_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipBridge>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _ipBridge_registered = (register_ipBridge_variants(), 0);
} // namespace
// === End block factory registration ===

ipBridge::ipBridge(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipBridge", name(), bbMode)
        ,ipBridgeBase(name(), variant)
        ,apb_uBridgeIp0("ip_apb_uBridgeIp0", "bridgeApbDecode")
        ,apb_uBridgeIp1("ip_apb_uBridgeIp1", "bridgeApbDecode")
        ,uBridgeAPBDecode(std::dynamic_pointer_cast<bridgeApbDecodeBase>((force_link_bridgeApbDecode(), instanceFactory::createInstance(name(), "uBridgeAPBDecode", "bridgeApbDecode", ""))))
        ,uBridgeIp0(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uBridgeIp0", "ip", "variant0")))
        ,uBridgeIp1(std::dynamic_pointer_cast<ipBase<ipVariant1Config>>(instanceFactory::createInstance(name(), "uBridgeIp1", "ip", "variant1")))
        ,thunker_uBridgeIp0("thunker_uBridgeIp0", data8In, uBridgeIp0->ipDataIf, name())
        ,thunker_uBridgeIp1("thunker_uBridgeIp1", data70In, uBridgeIp1->ipDataIf, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uBridgeAPBDecode->apbReg(apbReg);
    // instance to instance connections via channel
    uBridgeAPBDecode->apb_uBridgeIp0(apb_uBridgeIp0);
    uBridgeIp0->apbReg(apb_uBridgeIp0);
    uBridgeAPBDecode->apb_uBridgeIp1(apb_uBridgeIp1);
    uBridgeIp1->apbReg(apb_uBridgeIp1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

