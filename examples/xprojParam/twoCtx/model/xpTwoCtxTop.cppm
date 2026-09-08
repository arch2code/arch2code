//

// GENERATED_CODE_PARAM --block=xpTwoCtxTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpTwoCtx_xpTwoCtxTop.block;
import xpTwoCtx_xpTwoCtxTop.base;
import xpTwoCtx_xpTwoCtxWrap.base;
import xpTwoCtx;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpTwoCtx_ns;
export SC_MODULE(xpTwoCtxTop), public blockBase, public xpTwoCtxTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpTwoCtxWrapBase> uWrap;

    xpTwoCtxTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpTwoCtxTop);

// === Block factory registration (xpTwoCtxTop) ===
void register_xpTwoCtxTop_variants() {
    instanceFactory::registerBlock("xpTwoCtxTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxTop>(blockName, variant, bbMode)); }, "", "xpTwoCtx");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpTwoCtxTop_registered = (register_xpTwoCtxTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpTwoCtxTop::xpTwoCtxTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxTop", name(), bbMode)
        ,xpTwoCtxTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<xpTwoCtxWrapBase>(instanceFactory::createInstance(name(), "uWrap", "xpTwoCtxWrap", "", "xpTwoCtx")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

