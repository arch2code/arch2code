//

// GENERATED_CODE_PARAM --block=xpTwoCtxWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpDpLeafVariantConfig.h"
#include "xpTwoCtxVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpTwoCtx_xpTwoCtxWrap.block;
import xpTwoCtx_xpTwoCtxWrap.base;
import xpTwoCtx.xpTwoCtxDut.config;
import xpTwoCtx.xpTwoCtxSrc.config;
import xpDpLeaf;
import xpTwoCtx;
import xpTwoCtx_xpTwoCtxSrc.base;
import xpTwoCtx_xpTwoCtxDut.base;
import xpTwoCtx_xpTwoCtxSnk.base;
import xpTwoCtx_xpTwoCtxLitSrc.base;
import xpTwoCtx_xpTwoCtxBare.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
using namespace xpTwoCtx_ns;
export SC_MODULE(xpTwoCtxWrap), public blockBase, public xpTwoCtxWrapBase
{
private:

public:
    // channels
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpTwoCtx_xpTwoCtxDutTwoctxConfig> > out;
    // This file's own parameterized stream
    push_ack_channel< tcSt<xpTwoCtxSnkTwoctxConfig> > valOut;
    // Literal, non-parameterizable stream
    push_ack_channel< litSt > litOut;

    //instances contained in block
    std::shared_ptr<xpTwoCtxSrcBase<xpTwoCtx_xpTwoCtxSrcTwoctxConfig>> uSrc;
    std::shared_ptr<xpTwoCtxDutBase<xpTwoCtx_xpTwoCtxDutTwoctxConfig>> uDut;
    std::shared_ptr<xpTwoCtxSnkBase<xpTwoCtxSnkTwoctxConfig>> uSnk;
    std::shared_ptr<xpTwoCtxLitSrcBase> uLitSrc;
    std::shared_ptr<xpTwoCtxBareBase<xpTwoCtxBareTwoctxConfig>> uBare;

    // cross-interface thunkers
    push_ack_port_thunker<dpSt<xpTwoCtx_xpTwoCtxDutTwoctxConfig>, dpSt<xpTwoCtx_xpTwoCtxSrcTwoctxConfig>, true> thunker_out_uSrc;
    push_ack_port_thunker<tcSt<xpTwoCtxSnkTwoctxConfig>, tcSt<xpTwoCtx_xpTwoCtxDutTwoctxConfig>, true> thunker_valOut_uDut;

    xpTwoCtxWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpTwoCtxWrap);

// === Block factory registration (xpTwoCtxWrap) ===
void register_xpTwoCtxWrap_variants() {
    instanceFactory::registerBlock("xpTwoCtxWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxWrap>(blockName, variant, bbMode)); }, "", "xpTwoCtx");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpTwoCtxWrap_registered = (register_xpTwoCtxWrap_variants(), 0);
} // namespace
// === End block factory registration ===

xpTwoCtxWrap::xpTwoCtxWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxWrap", name(), bbMode)
        ,xpTwoCtxWrapBase(name(), variant)
        ,out("xpTwoCtxDut_out", "xpTwoCtxSrc")
        ,valOut("xpTwoCtxSnk_valOut", "xpTwoCtxDut")
        ,litOut("xpTwoCtxBare_litOut", "xpTwoCtxLitSrc")
        ,uSrc(std::dynamic_pointer_cast<xpTwoCtxSrcBase<xpTwoCtx_xpTwoCtxSrcTwoctxConfig>>(instanceFactory::createInstance(name(), "uSrc", "xpTwoCtxSrc", "twoctx", "xpTwoCtx")))
        ,uDut(std::dynamic_pointer_cast<xpTwoCtxDutBase<xpTwoCtx_xpTwoCtxDutTwoctxConfig>>(instanceFactory::createInstance(name(), "uDut", "xpTwoCtxDut", "twoctx", "xpTwoCtx")))
        ,uSnk(std::dynamic_pointer_cast<xpTwoCtxSnkBase<xpTwoCtxSnkTwoctxConfig>>(instanceFactory::createInstance(name(), "uSnk", "xpTwoCtxSnk", "twoctx", "xpTwoCtx")))
        ,uLitSrc(std::dynamic_pointer_cast<xpTwoCtxLitSrcBase>(instanceFactory::createInstance(name(), "uLitSrc", "xpTwoCtxLitSrc", "", "xpTwoCtx")))
        ,uBare(std::dynamic_pointer_cast<xpTwoCtxBareBase<xpTwoCtxBareTwoctxConfig>>(instanceFactory::createInstance(name(), "uBare", "xpTwoCtxBare", "twoctx", "xpTwoCtx")))
        ,thunker_out_uSrc("thunker_out_uSrc", out, uSrc->out, name())
        ,thunker_valOut_uDut("thunker_valOut_uDut", valOut, uDut->valOut, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uDut->in(out);
    uSnk->in(valOut);
    uLitSrc->litOut(litOut);
    uBare->litIn(litOut);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

