//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ip_top.h"
#include "apbDecodeBase.h"
#include "srcBase.h"
#include "ipBase.h"
#include "bridgeDriverBase.h"
#include "ipBridgeBase.h"
SC_HAS_PROCESS(ip_top);

// === Block factory registration (ip_top) ===
void force_link_ip_top() {}

void register_ip_top_variants() {
    instanceFactory::registerBlock("ip_top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_top>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _ip_top_registered = (register_ip_top_variants(), 0);
} // namespace
// === End block factory registration ===

ip_top::ip_top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip_top", name(), bbMode)
        ,ip_topBase(name(), variant)
        ,out0("ip_out0", "src")
        ,out1("ip_out1", "src")
        ,out8("ipBridge_out8", "bridgeDriver")
        ,out70("ipBridge_out70", "bridgeDriver")
        ,apbReg_uBridge("ipBridge_apbReg_uBridge", "apbDecode")
        ,apbReg_uIp0("ip_apbReg_uIp0", "apbDecode")
        ,apbReg_uIp1("ip_apbReg_uIp1", "apbDecode")
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>((force_link_apbDecode(), instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", ""))))
        ,uSrc(std::dynamic_pointer_cast<srcBase<srcVariantSrc0Config>>(instanceFactory::createInstance(name(), "uSrc", "src", "variantSrc0")))
        ,uIp0(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uIp0", "ip", "variant0")))
        ,uIp1(std::dynamic_pointer_cast<ipBase<ipVariant1Config>>(instanceFactory::createInstance(name(), "uIp1", "ip", "variant1")))
        ,uBridgeDriver(std::dynamic_pointer_cast<bridgeDriverBase>((force_link_bridgeDriver(), instanceFactory::createInstance(name(), "uBridgeDriver", "bridgeDriver", ""))))
        ,uBridge(std::dynamic_pointer_cast<ipBridgeBase>((force_link_ipBridge(), instanceFactory::createInstance(name(), "uBridge", "ipBridge", ""))))
        ,thunker_out0_uIp0("thunker_out0_uIp0", out0, uIp0->ipDataIf, name())
        ,thunker_out1_uIp1("thunker_out1_uIp1", out1, uIp1->ipDataIf, name())
        ,thunker_apbReg_uIp0_uIp0("thunker_apbReg_uIp0_uIp0", apbReg_uIp0, uIp0->regs, name())
        ,thunker_apbReg_uIp1_uIp1("thunker_apbReg_uIp1_uIp1", apbReg_uIp1, uIp1->regs, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->cpu_main(cpu_main);
    // instance to instance connections via channel
    uSrc->out0(out0);
    uSrc->out1(out1);
    uBridgeDriver->out8(out8);
    uBridge->data8In(out8);
    uBridgeDriver->out70(out70);
    uBridge->data70In(out70);
    uAPBDecode->apbReg_uBridge(apbReg_uBridge);
    uBridge->apbReg(apbReg_uBridge);
    uAPBDecode->apbReg_uIp0(apbReg_uIp0);
    uAPBDecode->apbReg_uIp1(apbReg_uIp1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

