//

// GENERATED_CODE_PARAM --block=xpMtxCompTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "xpMtxIpVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpMtxComp_xpMtxCompTop.block;
import xpMtxComp_xpMtxCompTop.base;
import xpMtxElect_xpMtxElectWrap.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(xpMtxCompTop), public blockBase, public xpMtxCompTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpMtxElectWrapBase> uReusedWrap;

    xpMtxCompTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxCompTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpMtxCompTop);

// === Block factory registration (xpMtxCompTop) ===
void register_xpMtxCompTop_variants() {
    instanceFactory::registerBlock("xpMtxCompTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxCompTop>(blockName, variant, bbMode)); }, "", "xpMtxComp");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxCompTop_registered = (register_xpMtxCompTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxCompTop::xpMtxCompTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxCompTop", name(), bbMode)
        ,xpMtxCompTopBase(name(), variant)
        ,uReusedWrap(std::dynamic_pointer_cast<xpMtxElectWrapBase>(instanceFactory::createInstance(name(), "uReusedWrap", "xpMtxElectWrap", "", "xpMtxElect")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

