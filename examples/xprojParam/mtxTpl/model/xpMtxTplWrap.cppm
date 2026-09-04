//

// GENERATED_CODE_PARAM --block=xpMtxTplWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpMtxIpVariantConfig.h"
#include "xpMtxTplTopVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpMtxTpl_xpMtxTplWrap.block;
import xpMtxTpl_xpMtxTplWrap.base;
import xpMtxTpl_xpMtxTplTop;
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
using namespace xpMtxTpl_xpMtxTplTop_ns;
using namespace xpMtxIp_ns;
export template<typename Config>
SC_MODULE(xpMtxTplWrap), public blockBase, public xpMtxTplWrapBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpMtxTplWrap);

    // inherited names usable unqualified (no Config:: / this->)
    using xpMtxTplWrapBase<Config>::MTX_CH_WIDTH;

    // channels
    // Parameterized assembler-owned channel between the two endpoint ports
    push_ack_channel< mtChSt<Config> > out_0;
    // Parameterized assembler-owned channel between the two endpoint ports
    push_ack_channel< mtChSt<Config> > out_1;
    // Parameterized assembler-owned channel between the two endpoint ports
    push_ack_channel< mtChSt<Config> > out_2;
    // Parameterized assembler-owned channel between the two endpoint ports
    push_ack_channel< mtChSt<Config> > out_3;

    //instances contained in block
    std::shared_ptr<xpMtxSrcLitBase> uSrcLL;
    std::shared_ptr<xpMtxDstLitBase> uDstLL;
    std::shared_ptr<xpMtxSrcLitBase> uSrcLP;
    std::shared_ptr<xpMtxDstParBase<xpMtxDstParV0Config>> uDstLP;
    std::shared_ptr<xpMtxSrcParBase<xpMtxSrcParV0Config>> uSrcPL;
    std::shared_ptr<xpMtxDstLitBase> uDstPL;
    std::shared_ptr<xpMtxSrcParBase<xpMtxSrcParV0Config>> uSrcPP;
    std::shared_ptr<xpMtxDstParBase<xpMtxDstParV0Config>> uDstPP;

    // cross-interface thunkers
    push_ack_port_thunker<mtChSt<Config>, miSrcLitSt, false> thunker_out_0_uSrcLL;
    push_ack_port_thunker<mtChSt<Config>, miDstLitSt, false> thunker_out_0_uDstLL;
    push_ack_port_thunker<mtChSt<Config>, miSrcLitSt, false> thunker_out_1_uSrcLP;
    push_ack_port_thunker<mtChSt<Config>, miDstParSt<xpMtxDstParV0Config>, true> thunker_out_1_uDstLP;
    push_ack_port_thunker<mtChSt<Config>, miSrcParSt<xpMtxSrcParV0Config>, true> thunker_out_2_uSrcPL;
    push_ack_port_thunker<mtChSt<Config>, miDstLitSt, false> thunker_out_2_uDstPL;
    push_ack_port_thunker<mtChSt<Config>, miSrcParSt<xpMtxSrcParV0Config>, true> thunker_out_3_uSrcPP;
    push_ack_port_thunker<mtChSt<Config>, miDstParSt<xpMtxDstParV0Config>, true> thunker_out_3_uDstPP;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpMtxTplWrapBase<Config>::mtChPixelT;
    using typename xpMtxTplWrapBase<Config>::mtChSt;

    xpMtxTplWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxTplWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpMtxTplWrap<Config>::xpMtxTplWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxTplWrap", name(), bbMode)
        ,xpMtxTplWrapBase<Config>(name(), variant)
        ,out_0("xpMtxDstLit_out_0", "xpMtxSrcLit")
        ,out_1("xpMtxDstPar_out_1", "xpMtxSrcLit")
        ,out_2("xpMtxDstLit_out_2", "xpMtxSrcPar")
        ,out_3("xpMtxDstPar_out_3", "xpMtxSrcPar")
        ,uSrcLL(std::dynamic_pointer_cast<xpMtxSrcLitBase>(instanceFactory::createInstance(name(), "uSrcLL", "xpMtxSrcLit", "", "xpMtxIp")))
        ,uDstLL(std::dynamic_pointer_cast<xpMtxDstLitBase>(instanceFactory::createInstance(name(), "uDstLL", "xpMtxDstLit", "", "xpMtxIp")))
        ,uSrcLP(std::dynamic_pointer_cast<xpMtxSrcLitBase>(instanceFactory::createInstance(name(), "uSrcLP", "xpMtxSrcLit", "", "xpMtxIp")))
        ,uDstLP(std::dynamic_pointer_cast<xpMtxDstParBase<xpMtxDstParV0Config>>(instanceFactory::createInstance(name(), "uDstLP", "xpMtxDstPar", "v0", "xpMtxTpl.xpMtxTpl_xpMtxTplWrap.xpMtxIp_xpMtxDstPar")))
        ,uSrcPL(std::dynamic_pointer_cast<xpMtxSrcParBase<xpMtxSrcParV0Config>>(instanceFactory::createInstance(name(), "uSrcPL", "xpMtxSrcPar", "v0", "xpMtxTpl.xpMtxTpl_xpMtxTplWrap.xpMtxIp_xpMtxSrcPar")))
        ,uDstPL(std::dynamic_pointer_cast<xpMtxDstLitBase>(instanceFactory::createInstance(name(), "uDstPL", "xpMtxDstLit", "", "xpMtxIp")))
        ,uSrcPP(std::dynamic_pointer_cast<xpMtxSrcParBase<xpMtxSrcParV0Config>>(instanceFactory::createInstance(name(), "uSrcPP", "xpMtxSrcPar", "v0", "xpMtxTpl.xpMtxTpl_xpMtxTplWrap.xpMtxIp_xpMtxSrcPar")))
        ,uDstPP(std::dynamic_pointer_cast<xpMtxDstParBase<xpMtxDstParV0Config>>(instanceFactory::createInstance(name(), "uDstPP", "xpMtxDstPar", "v0", "xpMtxTpl.xpMtxTpl_xpMtxTplWrap.xpMtxIp_xpMtxDstPar")))
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

