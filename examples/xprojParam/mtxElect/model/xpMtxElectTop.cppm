//

// GENERATED_CODE_PARAM --block=xpMtxElectTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpMtxElect_xpMtxElectTop.block;
import xpMtxElect_xpMtxElectTop.base;
import xpMtxElect_xpMtxElectWrap.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(xpMtxElectTop), public blockBase, public xpMtxElectTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpMtxElectWrapBase> uWrap;

    xpMtxElectTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxElectTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpMtxElectTop);

// === Block factory registration (xpMtxElectTop) ===
void register_xpMtxElectTop_variants() {
    instanceFactory::registerBlock("xpMtxElectTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxElectTop>(blockName, variant, bbMode)); }, "", "xpMtxElect");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxElectTop_registered = (register_xpMtxElectTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxElectTop::xpMtxElectTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxElectTop", name(), bbMode)
        ,xpMtxElectTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<xpMtxElectWrapBase>(instanceFactory::createInstance(name(), "uWrap", "xpMtxElectWrap", "", "xpMtxElect")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

