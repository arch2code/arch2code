//

// GENERATED_CODE_PARAM --block=xpMtxLitWrap --mode=module
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
export module xpMtxLit_xpMtxLitWrap.block;
import xpMtxLit_xpMtxLitWrap.base;
import xpMtxIp.xpMtxDstPar.config;
import xpMtxIp.xpMtxSrcPar.config;
import xpMtxLit_xpMtxLitTop;
import xpMtxIp;
import xpMtxIp_xpMtxSrcLit.base;
import xpMtxIp_xpMtxDstLit.base;
import xpMtxIp_xpMtxDstPar.base;
import xpMtxIp_xpMtxSrcPar.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpMtxLit_xpMtxLitTop_ns;
using namespace xpMtxIp_ns;
export SC_MODULE(xpMtxLitWrap), public blockBase, public xpMtxLitWrapBase
{
private:

public:
    // channels
    // Literal assembler-owned channel between the two endpoint ports
    push_ack_channel< mlChSt > out_0;
    // Literal assembler-owned channel between the two endpoint ports
    push_ack_channel< mlChSt > out_1;
    // Literal assembler-owned channel between the two endpoint ports
    push_ack_channel< mlChSt > out_2;
    // Literal assembler-owned channel between the two endpoint ports
    push_ack_channel< mlChSt > out_3;

    //instances contained in block
    std::shared_ptr<xpMtxSrcLitBase> uSrcLL;
    std::shared_ptr<xpMtxDstLitBase> uDstLL;
    std::shared_ptr<xpMtxSrcLitBase> uSrcLP;
    std::shared_ptr<xpMtxDstParBase<xpMtxIp_xpMtxDstParV0Config>> uDstLP;
    std::shared_ptr<xpMtxSrcParBase<xpMtxIp_xpMtxSrcParV0Config>> uSrcPL;
    std::shared_ptr<xpMtxDstLitBase> uDstPL;
    std::shared_ptr<xpMtxSrcParBase<xpMtxIp_xpMtxSrcParV0Config>> uSrcPP;
    std::shared_ptr<xpMtxDstParBase<xpMtxIp_xpMtxDstParV0Config>> uDstPP;

    // cross-interface thunkers
    push_ack_port_thunker<mlChSt, miSrcLitSt, true> thunker_out_0_uSrcLL;
    push_ack_port_thunker<mlChSt, miDstLitSt, true> thunker_out_0_uDstLL;
    push_ack_port_thunker<mlChSt, miSrcLitSt, true> thunker_out_1_uSrcLP;
    push_ack_port_thunker<mlChSt, miDstParSt<xpMtxIp_xpMtxDstParV0Config>, false> thunker_out_1_uDstLP;
    push_ack_port_thunker<mlChSt, miSrcParSt<xpMtxIp_xpMtxSrcParV0Config>, false> thunker_out_2_uSrcPL;
    push_ack_port_thunker<mlChSt, miDstLitSt, true> thunker_out_2_uDstPL;
    push_ack_port_thunker<mlChSt, miSrcParSt<xpMtxIp_xpMtxSrcParV0Config>, false> thunker_out_3_uSrcPP;
    push_ack_port_thunker<mlChSt, miDstParSt<xpMtxIp_xpMtxDstParV0Config>, false> thunker_out_3_uDstPP;

    xpMtxLitWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxLitWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpMtxLitWrap);

// === Block factory registration (xpMtxLitWrap) ===
void register_xpMtxLitWrap_variants() {
    instanceFactory::registerBlock("xpMtxLitWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxLitWrap>(blockName, variant, bbMode)); }, "", "xpMtxLit");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxLitWrap_registered = (register_xpMtxLitWrap_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxLitWrap::xpMtxLitWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxLitWrap", name(), bbMode)
        ,xpMtxLitWrapBase(name(), variant)
        ,out_0("xpMtxDstLit_out_0", "xpMtxSrcLit")
        ,out_1("xpMtxDstPar_out_1", "xpMtxSrcLit")
        ,out_2("xpMtxDstLit_out_2", "xpMtxSrcPar")
        ,out_3("xpMtxDstPar_out_3", "xpMtxSrcPar")
        ,uSrcLL(std::dynamic_pointer_cast<xpMtxSrcLitBase>(instanceFactory::createInstance(name(), "uSrcLL", "xpMtxSrcLit", "", "xpMtxIp")))
        ,uDstLL(std::dynamic_pointer_cast<xpMtxDstLitBase>(instanceFactory::createInstance(name(), "uDstLL", "xpMtxDstLit", "", "xpMtxIp")))
        ,uSrcLP(std::dynamic_pointer_cast<xpMtxSrcLitBase>(instanceFactory::createInstance(name(), "uSrcLP", "xpMtxSrcLit", "", "xpMtxIp")))
        ,uDstLP(std::dynamic_pointer_cast<xpMtxDstParBase<xpMtxIp_xpMtxDstParV0Config>>(instanceFactory::createInstance(name(), "uDstLP", "xpMtxDstPar", "v0", "xpMtxLit.xpMtxLit_xpMtxLitWrap.xpMtxIp_xpMtxDstPar")))
        ,uSrcPL(std::dynamic_pointer_cast<xpMtxSrcParBase<xpMtxIp_xpMtxSrcParV0Config>>(instanceFactory::createInstance(name(), "uSrcPL", "xpMtxSrcPar", "v0", "xpMtxLit.xpMtxLit_xpMtxLitWrap.xpMtxIp_xpMtxSrcPar")))
        ,uDstPL(std::dynamic_pointer_cast<xpMtxDstLitBase>(instanceFactory::createInstance(name(), "uDstPL", "xpMtxDstLit", "", "xpMtxIp")))
        ,uSrcPP(std::dynamic_pointer_cast<xpMtxSrcParBase<xpMtxIp_xpMtxSrcParV0Config>>(instanceFactory::createInstance(name(), "uSrcPP", "xpMtxSrcPar", "v0", "xpMtxLit.xpMtxLit_xpMtxLitWrap.xpMtxIp_xpMtxSrcPar")))
        ,uDstPP(std::dynamic_pointer_cast<xpMtxDstParBase<xpMtxIp_xpMtxDstParV0Config>>(instanceFactory::createInstance(name(), "uDstPP", "xpMtxDstPar", "v0", "xpMtxLit.xpMtxLit_xpMtxLitWrap.xpMtxIp_xpMtxDstPar")))
        ,thunker_out_0_uSrcLL("thunker_out_0_uSrcLL", out_0, uSrcLL->out, name())
        ,thunker_out_0_uDstLL("thunker_out_0_uDstLL", out_0, uDstLL->in, name())
        ,thunker_out_1_uSrcLP("thunker_out_1_uSrcLP", out_1, uSrcLP->out, name())
        ,thunker_out_1_uDstLP("thunker_out_1_uDstLP", out_1, uDstLP->in, name())
        ,thunker_out_2_uSrcPL("thunker_out_2_uSrcPL", out_2, uSrcPL->out, name())
        ,thunker_out_2_uDstPL("thunker_out_2_uDstPL", out_2, uDstPL->in, name())
        ,thunker_out_3_uSrcPP("thunker_out_3_uSrcPP", out_3, uSrcPP->out, name())
        ,thunker_out_3_uDstPP("thunker_out_3_uDstPP", out_3, uDstPP->in, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

