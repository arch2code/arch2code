//

// GENERATED_CODE_PARAM --block=xpMtxTplTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "xpMtxTplTopVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpMtxTpl_xpMtxTplTop.block;
import xpMtxTpl_xpMtxTplTop.base;
import xpMtxTpl_xpMtxTplWrap.base;
import xpMtxTpl_xpMtxTplTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpMtxTpl_xpMtxTplTop_ns;
export SC_MODULE(xpMtxTplTop), public blockBase, public xpMtxTplTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpMtxTplWrapBase<xpMtxTplWrapV0Config>> uWrap;

    xpMtxTplTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxTplTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpMtxTplTop);

// === Block factory registration (xpMtxTplTop) ===
void register_xpMtxTplTop_variants() {
    instanceFactory::registerBlock("xpMtxTplTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxTplTop>(blockName, variant, bbMode)); }, "", "xpMtxTpl");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxTplTop_registered = (register_xpMtxTplTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxTplTop::xpMtxTplTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxTplTop", name(), bbMode)
        ,xpMtxTplTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<xpMtxTplWrapBase<xpMtxTplWrapV0Config>>(instanceFactory::createInstance(name(), "uWrap", "xpMtxTplWrap", "v0", "xpMtxTpl.xpMtxTpl_xpMtxTplTop.xpMtxTpl_xpMtxTplWrap")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

