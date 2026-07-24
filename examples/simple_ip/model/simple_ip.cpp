//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "simple_ip.h"
import apbDecode.base;
import dataGen.base;
import ip.base;
SC_HAS_PROCESS(simple_ip);

// === Block factory registration (simple_ip) ===
void register_simple_ip_variants() {
    instanceFactory::registerBlock("simple_ip_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<simple_ip>(blockName, variant, bbMode)); }, "", "simple_ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _simple_ip_registered = (register_simple_ip_variants(), 0);
} // namespace
// === End block factory registration ===

simple_ip::simple_ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("simple_ip", name(), bbMode)
        ,simple_ipBase(name(), variant)
        ,out("ip_out", "dataGen")
        ,apbReg_uIp("ip_apbReg_uIp", "apbDecode")
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>(instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "", "simple_ip")))
        ,uDataGen(std::dynamic_pointer_cast<dataGenBase>(instanceFactory::createInstance(name(), "uDataGen", "dataGen", "", "simple_ip")))
        ,uIp(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uIp", "ip", "variant0", "simple_ip")))
        ,thunker_out_uIp("thunker_out_uIp", out, uIp->ipDataIf, name())
        ,thunker_apbReg_uIp_uIp("thunker_apbReg_uIp_uIp", apbReg_uIp, uIp->regs, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->cpu_main(cpu_main);
    // instance to instance connections via channel
    uDataGen->out(out);
    uAPBDecode->apbReg_uIp(apbReg_uIp);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

