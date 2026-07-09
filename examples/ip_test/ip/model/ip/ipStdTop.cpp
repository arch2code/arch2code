//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdTop
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ipStdTop.h"
import ipStdMaster.base;
import ipStdDriver.base;
import ipStdDecode.base;
import ip.base;
SC_HAS_PROCESS(ipStdTop);

// === Block factory registration (ipStdTop) ===
void register_ipStdTop_variants() {
    instanceFactory::registerBlock("ipStdTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipStdTop>(blockName, variant, bbMode)); }, "", "ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ipStdTop_registered = (register_ipStdTop_variants(), 0);
} // namespace
// === End block factory registration ===

ipStdTop::ipStdTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdTop", name(), bbMode)
        ,ipStdTopBase(name(), variant)
        ,apbOut("ipStdDecode_apbOut", "ipStdMaster")
        ,out0("ip_out0", "ipStdDriver")
        ,ipReg_uIp("ip_ipReg_uIp", "ipStdDecode")
        ,uIpStdMaster(std::dynamic_pointer_cast<ipStdMasterBase>(instanceFactory::createInstance(name(), "uIpStdMaster", "ipStdMaster", "", "ip")))
        ,uIpStdDriver(std::dynamic_pointer_cast<ipStdDriverBase>(instanceFactory::createInstance(name(), "uIpStdDriver", "ipStdDriver", "", "ip")))
        ,uIpStdDecode(std::dynamic_pointer_cast<ipStdDecodeBase>(instanceFactory::createInstance(name(), "uIpStdDecode", "ipStdDecode", "", "ip")))
        ,uIp(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uIp", "ip", "variant0", "ip")))
        ,thunker_out0_uIp("thunker_out0_uIp", out0, uIp->ipDataIf, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uIpStdMaster->apbOut(apbOut);
    uIpStdDecode->ipReg(apbOut);
    uIpStdDriver->out0(out0);
    uIpStdDecode->ipReg_uIp(ipReg_uIp);
    uIp->regs(ipReg_uIp);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

