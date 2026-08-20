//

// GENERATED_CODE_PARAM --block=xpMtxElectWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpMtxIpVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpMtxElect_xpMtxElectWrap.block;
import xpMtxElect_xpMtxElectWrap.base;
import xpMtxIp;
import xpMtxIp_xpMtxSrcPar.base;
import xpMtxIp_xpMtxDstPar.base;
import xpMtxIp_xpMtxDstLit.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpMtxIp_ns;
export SC_MODULE(xpMtxElectWrap), public blockBase, public xpMtxElectWrapBase
{
private:

public:
    // channels
    // Producer port interface, parameterized payload
    push_ack_channel< miSrcParSt<xpMtxSrcParV0Config> > out_0;
    // Producer port interface, parameterized payload
    push_ack_channel< miSrcParSt<xpMtxSrcParV0Config> > out_1;

    //instances contained in block
    std::shared_ptr<xpMtxSrcParBase<xpMtxSrcParV0Config>> uSrcPP;
    std::shared_ptr<xpMtxDstParBase<xpMtxDstParV0Config>> uDstPP;
    std::shared_ptr<xpMtxSrcParBase<xpMtxSrcParV0Config>> uSrcPL;
    std::shared_ptr<xpMtxDstLitBase> uDstPL;

    // cross-interface thunkers
    push_ack_port_thunker<miSrcParSt<xpMtxSrcParV0Config>, miDstParSt<xpMtxDstParV0Config>, true> thunker_out_0_uDstPP;
    push_ack_port_thunker<miSrcParSt<xpMtxSrcParV0Config>, miDstLitSt, false> thunker_out_1_uDstPL;

    xpMtxElectWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxElectWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpMtxElectWrap);

// === Block factory registration (xpMtxElectWrap) ===
void register_xpMtxElectWrap_variants() {
    instanceFactory::registerBlock("xpMtxElectWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxElectWrap>(blockName, variant, bbMode)); }, "", "xpMtxElect");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxElectWrap_registered = (register_xpMtxElectWrap_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxElectWrap::xpMtxElectWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxElectWrap", name(), bbMode)
        ,xpMtxElectWrapBase(name(), variant)
        ,out_0("xpMtxDstPar_out_0", "xpMtxSrcPar")
        ,out_1("xpMtxDstLit_out_1", "xpMtxSrcPar")
        ,uSrcPP(std::dynamic_pointer_cast<xpMtxSrcParBase<xpMtxSrcParV0Config>>(instanceFactory::createInstance(name(), "uSrcPP", "xpMtxSrcPar", "v0", "xpMtxElect")))
        ,uDstPP(std::dynamic_pointer_cast<xpMtxDstParBase<xpMtxDstParV0Config>>(instanceFactory::createInstance(name(), "uDstPP", "xpMtxDstPar", "v0", "xpMtxElect")))
        ,uSrcPL(std::dynamic_pointer_cast<xpMtxSrcParBase<xpMtxSrcParV0Config>>(instanceFactory::createInstance(name(), "uSrcPL", "xpMtxSrcPar", "v0", "xpMtxElect")))
        ,uDstPL(std::dynamic_pointer_cast<xpMtxDstLitBase>(instanceFactory::createInstance(name(), "uDstPL", "xpMtxDstLit", "", "xpMtxIp")))
        ,thunker_out_0_uDstPP("thunker_out_0_uDstPP", out_0, uDstPP->in, name())
        ,thunker_out_1_uDstPL("thunker_out_1_uDstPL", out_1, uDstPL->in, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uSrcPP->out(out_0);
    uSrcPL->out(out_1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

