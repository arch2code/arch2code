//

// GENERATED_CODE_PARAM --block=xpCstUseTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "xpCstIpVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCstUse_xpCstUseTop.block;
import xpCstUse_xpCstUseTop.base;
import xpCstUse_xpCstUseWrap.base;
import xpCstUse_xpCstUseTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstUse_xpCstUseTop_ns;
export SC_MODULE(xpCstUseTop), public blockBase, public xpCstUseTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpCstUseWrapBase> uWrap;

    xpCstUseTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstUseTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpCstUseTop);

// === Block factory registration (xpCstUseTop) ===
void register_xpCstUseTop_variants() {
    instanceFactory::registerBlock("xpCstUseTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstUseTop>(blockName, variant, bbMode)); }, "", "xpCstUse");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCstUseTop_registered = (register_xpCstUseTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpCstUseTop::xpCstUseTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstUseTop", name(), bbMode)
        ,xpCstUseTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<xpCstUseWrapBase>(instanceFactory::createInstance(name(), "uWrap", "xpCstUseWrap", "", "xpCstUse")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

