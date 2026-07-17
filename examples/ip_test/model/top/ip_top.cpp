//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ip_top.h"
import apbDecode.base;
import src.base;
import ip.base;
import ipBridge.base;
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
        ,uSrc(std::dynamic_pointer_cast<srcBase<srcDefaultConfig>>(instanceFactory::createInstance(name(), "uSrc", "src", "variantSrc0", "ip_test")))
        ,uIp0(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uIp0", "ip", "variant0", "ip_test")))
        ,uIp1(std::dynamic_pointer_cast<ipBase<ipVariant1Config>>(instanceFactory::createInstance(name(), "uIp1", "ip", "variant1", "ip_test")))
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

