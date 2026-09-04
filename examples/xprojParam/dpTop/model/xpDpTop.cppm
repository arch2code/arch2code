//

// GENERATED_CODE_PARAM --block=xpDpTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "xpDpLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpDpTop.block;
import xpDpTop.base;
import xpDpTop.xpDpWrap.config;
import xpDpTop_xpDpWrap.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(xpDpTop), public blockBase, public xpDpTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpDpWrapBase<xpDpTop_xpDpWrapCustomerConfig>> uWrap;

    xpDpTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpDpTop);

// === Block factory registration (xpDpTop) ===
void register_xpDpTop_variants() {
    instanceFactory::registerBlock("xpDpTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpTop>(blockName, variant, bbMode)); }, "", "xpDpTop");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpDpTop_registered = (register_xpDpTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpDpTop::xpDpTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpTop", name(), bbMode)
        ,xpDpTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<xpDpWrapBase<xpDpTop_xpDpWrapCustomerConfig>>(instanceFactory::createInstance(name(), "uWrap", "xpDpWrap", "customer", "xpDpTop.xpDpTop.xpDpTop_xpDpWrap")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

