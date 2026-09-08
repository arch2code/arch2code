//

// GENERATED_CODE_PARAM --block=xpInhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpInhVar_xpInhTop.block;
import xpInhVar_xpInhTop.base;
import xpInhVar_xpInhWrap.base;
import xpInhVar_xpInhCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpInhVar_xpInhCont_ns;
export SC_MODULE(xpInhTop), public blockBase, public xpInhTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpInhWrapBase> uWrap;

    xpInhTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpInhTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpInhTop);

// === Block factory registration (xpInhTop) ===
void register_xpInhTop_variants() {
    instanceFactory::registerBlock("xpInhTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhTop>(blockName, variant, bbMode)); }, "", "xpInhVar");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpInhTop_registered = (register_xpInhTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpInhTop::xpInhTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpInhTop", name(), bbMode)
        ,xpInhTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<xpInhWrapBase>(instanceFactory::createInstance(name(), "uWrap", "xpInhWrap", "", "xpInhVar")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

