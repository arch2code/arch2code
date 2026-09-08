//

// GENERATED_CODE_PARAM --block=xpCstBindTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCstBind_xpCstBindTop.block;
import xpCstBind_xpCstBindTop.base;
import xpCstBind_xpCstBindWrap.base;
import xpCstBind_xpCstBindTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstBind_xpCstBindTop_ns;
export SC_MODULE(xpCstBindTop), public blockBase, public xpCstBindTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpCstBindWrapBase> uWrap;

    xpCstBindTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstBindTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpCstBindTop);

// === Block factory registration (xpCstBindTop) ===
void register_xpCstBindTop_variants() {
    instanceFactory::registerBlock("xpCstBindTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstBindTop>(blockName, variant, bbMode)); }, "", "xpCstBind");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCstBindTop_registered = (register_xpCstBindTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpCstBindTop::xpCstBindTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstBindTop", name(), bbMode)
        ,xpCstBindTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<xpCstBindWrapBase>(instanceFactory::createInstance(name(), "uWrap", "xpCstBindWrap", "", "xpCstBind")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

