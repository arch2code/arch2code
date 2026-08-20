//

// GENERATED_CODE_PARAM --block=xpTwoCtxLitSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpTwoCtx_xpTwoCtxLitSrc.block;
import xpTwoCtx_xpTwoCtxLitSrc.base;
import xpTwoCtx;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpTwoCtx_ns;
export SC_MODULE(xpTwoCtxLitSrc), public blockBase, public xpTwoCtxLitSrcBase
{
private:

public:

    xpTwoCtxLitSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxLitSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpTwoCtxLitSrc);

// === Block factory registration (xpTwoCtxLitSrc) ===
void register_xpTwoCtxLitSrc_variants() {
    instanceFactory::registerBlock("xpTwoCtxLitSrc_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxLitSrc>(blockName, variant, bbMode)); }, "", "xpTwoCtx");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpTwoCtxLitSrc_registered = (register_xpTwoCtxLitSrc_variants(), 0);
} // namespace
// === End block factory registration ===

xpTwoCtxLitSrc::xpTwoCtxLitSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxLitSrc", name(), bbMode)
        ,xpTwoCtxLitSrcBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

