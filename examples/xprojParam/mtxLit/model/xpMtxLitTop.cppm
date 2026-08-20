//

// GENERATED_CODE_PARAM --block=xpMtxLitTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpMtxLit_xpMtxLitTop.block;
import xpMtxLit_xpMtxLitTop.base;
import xpMtxLit_xpMtxLitWrap.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(xpMtxLitTop), public blockBase, public xpMtxLitTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpMtxLitWrapBase> uWrap;

    xpMtxLitTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxLitTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpMtxLitTop);

// === Block factory registration (xpMtxLitTop) ===
void register_xpMtxLitTop_variants() {
    instanceFactory::registerBlock("xpMtxLitTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxLitTop>(blockName, variant, bbMode)); }, "", "xpMtxLit");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxLitTop_registered = (register_xpMtxLitTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxLitTop::xpMtxLitTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxLitTop", name(), bbMode)
        ,xpMtxLitTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<xpMtxLitWrapBase>(instanceFactory::createInstance(name(), "uWrap", "xpMtxLitWrap", "", "xpMtxLit")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

