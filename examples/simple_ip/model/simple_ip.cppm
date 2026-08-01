//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple_ip --mode=module
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
export module simple_ip.block;
import simple_ip.base;
import common_shared_types;
import simple_ip;
import ip;
import simple_ip_apbDecode.base;
import simple_ip_dataGen.base;
import ip.base;
using namespace common_shared_types_ns;
using namespace simple_ip_ns;
using namespace ip_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(simple_ip), public blockBase, public simple_ipBase
{
private:

public:
    // channels
    // Non-parameterized producer -> uIp.ipDataIf boundary
    push_ack_channel< simpleData8St > out;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uIp;

    //instances contained in block
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<dataGenBase> uDataGen;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp;

    // cross-interface thunkers
    push_ack_port_thunker<simpleData8St, ipDataSt<ipVariant0Config>> thunker_out_uIp;
    apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt> thunker_apbReg_uIp_uIp;

    simple_ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simple_ip() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
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

