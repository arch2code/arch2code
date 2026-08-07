//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "ipVariantConfig.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module ip_ipStdTop.block;
import ip_ipStdTop.base;
import ip;
import ip_ipTop;
import ip_ipStdMaster.base;
import ip_ipStdDriver.base;
import ip_ipStdDecode.base;
import ip.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ip_ns;
using namespace ip_ipTop_ns;
export SC_MODULE(ipStdTop), public blockBase, public ipStdTopBase
{
private:

public:
    // channels
    // Register bus the ip block consumes
    apb_channel< ipRegAddrSt, ipRegDataSt > apbOut;
    // Non-parameterized container boundary interface for uIp.ipDataIf
    push_ack_channel< ipStdData8St > out0;
    // Register bus the ip block consumes
    apb_channel< ipRegAddrSt, ipRegDataSt > ipReg_uIp;

    //instances contained in block
    std::shared_ptr<ipStdMasterBase> uIpStdMaster;
    std::shared_ptr<ipStdDriverBase> uIpStdDriver;
    std::shared_ptr<ipStdDecodeBase> uIpStdDecode;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp;

    // cross-interface thunkers
    push_ack_port_thunker<ipStdData8St, ipDataSt<ipVariant0Config>> thunker_out0_uIp;

    ipStdTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
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

