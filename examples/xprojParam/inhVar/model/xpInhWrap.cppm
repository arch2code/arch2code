//

// GENERATED_CODE_PARAM --block=xpInhWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpInhContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpInhVar_xpInhWrap.block;
import xpInhVar_xpInhWrap.base;
import xpInhVar_xpInhCont;
import xpInhVar_xpInhDrv.base;
import xpInhVar_xpInhCont.base;
import xpInhVar_xpInhChk.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpInhVar_xpInhCont_ns;
export SC_MODULE(xpInhWrap), public blockBase, public xpInhWrapBase
{
private:

public:
    // channels
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<xpInhContDefaultConfig> > out;
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<xpInhChkChkDefConfig> > contOut_0;
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<xpInhContAltConfig> > out2;
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<xpInhChkChkAltConfig> > contOut_1;

    //instances contained in block
    std::shared_ptr<xpInhDrvBase<xpInhDrvDrvConfig>> uDrv;
    std::shared_ptr<xpInhContBase<xpInhContDefaultConfig>> uContDef;
    std::shared_ptr<xpInhContBase<xpInhContAltConfig>> uContAlt;
    std::shared_ptr<xpInhChkBase<xpInhChkChkDefConfig>> uChkDef;
    std::shared_ptr<xpInhChkBase<xpInhChkChkAltConfig>> uChkAlt;

    // cross-interface thunkers
    push_ack_port_thunker<inhSt<xpInhContDefaultConfig>, inhSt<xpInhDrvDrvConfig>, true> thunker_out_uDrv;
    push_ack_port_thunker<inhSt<xpInhChkChkDefConfig>, inhSt<xpInhContDefaultConfig>, true> thunker_contOut_0_uContDef;
    push_ack_port_thunker<inhSt<xpInhContAltConfig>, inhSt<xpInhDrvDrvConfig>, true> thunker_out2_uDrv;
    push_ack_port_thunker<inhSt<xpInhChkChkAltConfig>, inhSt<xpInhContAltConfig>, true> thunker_contOut_1_uContAlt;

    xpInhWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpInhWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpInhWrap);

// === Block factory registration (xpInhWrap) ===
void register_xpInhWrap_variants() {
    instanceFactory::registerBlock("xpInhWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhWrap>(blockName, variant, bbMode)); }, "", "xpInhVar");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpInhWrap_registered = (register_xpInhWrap_variants(), 0);
} // namespace
// === End block factory registration ===

xpInhWrap::xpInhWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpInhWrap", name(), bbMode)
        ,xpInhWrapBase(name(), variant)
        ,out("xpInhCont_out", "xpInhDrv")
        ,contOut_0("xpInhChk_contOut_0", "xpInhCont")
        ,out2("xpInhCont_out2", "xpInhDrv")
        ,contOut_1("xpInhChk_contOut_1", "xpInhCont")
        ,uDrv(std::dynamic_pointer_cast<xpInhDrvBase<xpInhDrvDrvConfig>>(instanceFactory::createInstance(name(), "uDrv", "xpInhDrv", "drv", "xpInhVar")))
        ,uContDef(std::dynamic_pointer_cast<xpInhContBase<xpInhContDefaultConfig>>(instanceFactory::createInstance(name(), "uContDef", "xpInhCont", "default", "xpInhVar")))
        ,uContAlt(std::dynamic_pointer_cast<xpInhContBase<xpInhContAltConfig>>(instanceFactory::createInstance(name(), "uContAlt", "xpInhCont", "alt", "xpInhVar")))
        ,uChkDef(std::dynamic_pointer_cast<xpInhChkBase<xpInhChkChkDefConfig>>(instanceFactory::createInstance(name(), "uChkDef", "xpInhChk", "chkDef", "xpInhVar")))
        ,uChkAlt(std::dynamic_pointer_cast<xpInhChkBase<xpInhChkChkAltConfig>>(instanceFactory::createInstance(name(), "uChkAlt", "xpInhChk", "chkAlt", "xpInhVar")))
        ,thunker_out_uDrv("thunker_out_uDrv", out, uDrv->out, name())
        ,thunker_contOut_0_uContDef("thunker_contOut_0_uContDef", contOut_0, uContDef->contOut, name())
        ,thunker_out2_uDrv("thunker_out2_uDrv", out2, uDrv->out2, name())
        ,thunker_contOut_1_uContAlt("thunker_contOut_1_uContAlt", contOut_1, uContAlt->contOut, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uContDef->contIn(out);
    uChkDef->in(contOut_0);
    uContAlt->contIn(out2);
    uChkAlt->in(contOut_1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

