//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtInhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpRtInh_xpRtInhTop.block;
import xpRtInh_xpRtInhTop.base;
import xpRtInh.xpRtWrap.config;
import common_shared_types;
import xpRtInh_xpRtPrimeDecode.base;
import xpRtInh_xpRtWrap.base;
import xpRtInh;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace common_shared_types_ns;
using namespace xpRtInh_ns;
export SC_MODULE(xpRtInhTop), public blockBase, public xpRtInhTopBase
{
private:

public:
    // channels
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uWrap;

    //instances contained in block
    std::shared_ptr<xpRtPrimeDecodeBase> uPrimeDecode;
    std::shared_ptr<xpRtWrapBase<xpRtInh_xpRtWrapUseConfig>> uWrap;

    xpRtInhTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpRtInhTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpRtInhTop);

// === Block factory registration (xpRtInhTop) ===
void register_xpRtInhTop_variants() {
    instanceFactory::registerBlock("xpRtInhTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtInhTop>(blockName, variant, bbMode)); }, "", "xpRtInh");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpRtInhTop_registered = (register_xpRtInhTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpRtInhTop::xpRtInhTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpRtInhTop", name(), bbMode)
        ,xpRtInhTopBase(name(), variant)
        ,apbReg_uWrap("xpRtWrap_apbReg_uWrap", "xpRtPrimeDecode")
        ,uPrimeDecode(std::dynamic_pointer_cast<xpRtPrimeDecodeBase>(instanceFactory::createInstance(name(), "uPrimeDecode", "xpRtPrimeDecode", "", "xpRtInh")))
        ,uWrap(std::dynamic_pointer_cast<xpRtWrapBase<xpRtInh_xpRtWrapUseConfig>>(instanceFactory::createInstance(name(), "uWrap", "xpRtWrap", "use", "xpRtInh.xpRtInh_xpRtInhTop.xpRtInh_xpRtWrap")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uPrimeDecode->cpu_main(cpu_main);
    // instance to instance connections via channel
    uPrimeDecode->apbReg_uWrap(apbReg_uWrap);
    uWrap->apbReg(apbReg_uWrap);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

