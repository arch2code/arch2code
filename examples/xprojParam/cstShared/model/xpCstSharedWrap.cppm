//

// GENERATED_CODE_PARAM --block=xpCstSharedWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCstShared_xpCstSharedWrap.block;
import xpCstShared_xpCstSharedWrap.base;
import xpCstShared.xpCstSharedChk.config;
import xpCstShared.xpCstSharedSrc.config;
import xpCstShared_xpCstSharedDefs;
import xpCstShared_xpCstSharedSrc.base;
import xpCstShared_xpCstSharedChk.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstShared_xpCstSharedDefs_ns;
export SC_MODULE(xpCstSharedWrap), public blockBase, public xpCstSharedWrapBase
{
private:

public:
    // channels
    // Shared parameterized pixel push/ack stream
    push_ack_channel< cshSt<xpCstShared_xpCstSharedChkUseConfig> > out;

    //instances contained in block
    std::shared_ptr<xpCstSharedSrcBase<xpCstShared_xpCstSharedSrcUseConfig>> uSrc;
    std::shared_ptr<xpCstSharedChkBase<xpCstShared_xpCstSharedChkUseConfig>> uChk;

    // cross-interface thunkers
    push_ack_port_thunker<cshSt<xpCstShared_xpCstSharedChkUseConfig>, cshSt<xpCstShared_xpCstSharedSrcUseConfig>, true> thunker_out_uSrc;

    xpCstSharedWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstSharedWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpCstSharedWrap);

// === Block factory registration (xpCstSharedWrap) ===
void register_xpCstSharedWrap_variants() {
    instanceFactory::registerBlock("xpCstSharedWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSharedWrap>(blockName, variant, bbMode)); }, "", "xpCstShared");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCstSharedWrap_registered = (register_xpCstSharedWrap_variants(), 0);
} // namespace
// === End block factory registration ===

xpCstSharedWrap::xpCstSharedWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstSharedWrap", name(), bbMode)
        ,xpCstSharedWrapBase(name(), variant)
        ,out("xpCstSharedChk_out", "xpCstSharedSrc")
        ,uSrc(std::dynamic_pointer_cast<xpCstSharedSrcBase<xpCstShared_xpCstSharedSrcUseConfig>>(instanceFactory::createInstance(name(), "uSrc", "xpCstSharedSrc", "use", "xpCstShared.xpCstShared_xpCstSharedWrap.xpCstShared_xpCstSharedSrc")))
        ,uChk(std::dynamic_pointer_cast<xpCstSharedChkBase<xpCstShared_xpCstSharedChkUseConfig>>(instanceFactory::createInstance(name(), "uChk", "xpCstSharedChk", "use", "xpCstShared.xpCstShared_xpCstSharedWrap.xpCstShared_xpCstSharedChk")))
        ,thunker_out_uSrc("thunker_out_uSrc", out, uSrc->out, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uChk->in(out);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

