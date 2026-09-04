//

// GENERATED_CODE_PARAM --block=vliWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "vliContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module vlInh_vliWrap.block;
import vlInh_vliWrap.base;
import vlInh_vliCont;
import vlInh_vliDrv.base;
import vlInh_vliCont.base;
import vlInh_vliChk.base;
import vlInh_vliLeaf.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlInh_vliCont_ns;
export SC_MODULE(vliWrap), public blockBase, public vliWrapBase
{
private:

public:
    // channels
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vliContDefaultConfig> > out_0;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vliChkChkDefConfig> > contOut_0;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vliContAltConfig> > out_1;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vliChkChkAltConfig> > contOut_1;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vliLeafSoloConfig> > out_2;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vliLeafSoloConfig> > out_3;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vliChkChkSoloConfig> > out_4;

    //instances contained in block
    std::shared_ptr<vliDrvBase<vliDrvDrvDefConfig>> uDrvDef;
    std::shared_ptr<vliDrvBase<vliDrvDrvAltConfig>> uDrvAlt;
    std::shared_ptr<vliDrvBase<vliDrvDrvSoloConfig>> uDrvSolo;
    std::shared_ptr<vliContBase<vliContDefaultConfig>> uContDef;
    std::shared_ptr<vliContBase<vliContAltConfig>> uContAlt;
    std::shared_ptr<vliChkBase<vliChkChkDefConfig>> uChkDef;
    std::shared_ptr<vliChkBase<vliChkChkAltConfig>> uChkAlt;
    std::shared_ptr<vliChkBase<vliChkChkSoloConfig>> uChkSolo;
    std::shared_ptr<vliLeafBase<vliLeafSoloConfig>> uLeafSoloA;
    std::shared_ptr<vliLeafBase<vliLeafSoloConfig>> uLeafSoloB;

    // cross-interface thunkers
    push_ack_port_thunker<vliSt<vliContDefaultConfig>, vliSt<vliDrvDrvDefConfig>, true> thunker_out_0_uDrvDef;
    push_ack_port_thunker<vliSt<vliChkChkDefConfig>, vliSt<vliContDefaultConfig>, true> thunker_contOut_0_uContDef;
    push_ack_port_thunker<vliSt<vliContAltConfig>, vliSt<vliDrvDrvAltConfig>, true> thunker_out_1_uDrvAlt;
    push_ack_port_thunker<vliSt<vliChkChkAltConfig>, vliSt<vliContAltConfig>, true> thunker_contOut_1_uContAlt;
    push_ack_port_thunker<vliSt<vliLeafSoloConfig>, vliSt<vliDrvDrvSoloConfig>, true> thunker_out_2_uDrvSolo;
    push_ack_port_thunker<vliSt<vliChkChkSoloConfig>, vliSt<vliLeafSoloConfig>, true> thunker_out_4_uLeafSoloB;

    vliWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vliWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(vliWrap);

// === Block factory registration (vliWrap) ===
void register_vliWrap_variants() {
    instanceFactory::registerBlock("vliWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliWrap>(blockName, variant, bbMode)); }, "", "vlInh");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _vliWrap_registered = (register_vliWrap_variants(), 0);
} // namespace
// === End block factory registration ===

vliWrap::vliWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vliWrap", name(), bbMode)
        ,vliWrapBase(name(), variant)
        ,out_0("vliCont_out_0", "vliDrv")
        ,contOut_0("vliChk_contOut_0", "vliCont")
        ,out_1("vliCont_out_1", "vliDrv")
        ,contOut_1("vliChk_contOut_1", "vliCont")
        ,out_2("vliLeaf_out_2", "vliDrv")
        ,out_3("vliLeaf_out_3", "vliLeaf")
        ,out_4("vliChk_out_4", "vliLeaf")
        ,uDrvDef(std::dynamic_pointer_cast<vliDrvBase<vliDrvDrvDefConfig>>(instanceFactory::createInstance(name(), "uDrvDef", "vliDrv", "drvDef", "vlInh.vlInh_vliWrap.vlInh_vliDrv")))
        ,uDrvAlt(std::dynamic_pointer_cast<vliDrvBase<vliDrvDrvAltConfig>>(instanceFactory::createInstance(name(), "uDrvAlt", "vliDrv", "drvAlt", "vlInh.vlInh_vliWrap.vlInh_vliDrv")))
        ,uDrvSolo(std::dynamic_pointer_cast<vliDrvBase<vliDrvDrvSoloConfig>>(instanceFactory::createInstance(name(), "uDrvSolo", "vliDrv", "drvSolo", "vlInh.vlInh_vliWrap.vlInh_vliDrv")))
        ,uContDef(std::dynamic_pointer_cast<vliContBase<vliContDefaultConfig>>(instanceFactory::createInstance(name(), "uContDef", "vliCont", "default", "vlInh.vlInh_vliWrap.vlInh_vliCont")))
        ,uContAlt(std::dynamic_pointer_cast<vliContBase<vliContAltConfig>>(instanceFactory::createInstance(name(), "uContAlt", "vliCont", "alt", "vlInh.vlInh_vliWrap.vlInh_vliCont")))
        ,uChkDef(std::dynamic_pointer_cast<vliChkBase<vliChkChkDefConfig>>(instanceFactory::createInstance(name(), "uChkDef", "vliChk", "chkDef", "vlInh.vlInh_vliWrap.vlInh_vliChk")))
        ,uChkAlt(std::dynamic_pointer_cast<vliChkBase<vliChkChkAltConfig>>(instanceFactory::createInstance(name(), "uChkAlt", "vliChk", "chkAlt", "vlInh.vlInh_vliWrap.vlInh_vliChk")))
        ,uChkSolo(std::dynamic_pointer_cast<vliChkBase<vliChkChkSoloConfig>>(instanceFactory::createInstance(name(), "uChkSolo", "vliChk", "chkSolo", "vlInh.vlInh_vliWrap.vlInh_vliChk")))
        ,uLeafSoloA(std::dynamic_pointer_cast<vliLeafBase<vliLeafSoloConfig>>(instanceFactory::createInstance(name(), "uLeafSoloA", "vliLeaf", "solo", "vlInh.vlInh_vliWrap.vlInh_vliLeaf")))
        ,uLeafSoloB(std::dynamic_pointer_cast<vliLeafBase<vliLeafSoloConfig>>(instanceFactory::createInstance(name(), "uLeafSoloB", "vliLeaf", "solo", "vlInh.vlInh_vliWrap.vlInh_vliLeaf")))
        ,thunker_out_0_uDrvDef("thunker_out_0_uDrvDef", out_0, uDrvDef->out, name())
        ,thunker_contOut_0_uContDef("thunker_contOut_0_uContDef", contOut_0, uContDef->contOut, name())
        ,thunker_out_1_uDrvAlt("thunker_out_1_uDrvAlt", out_1, uDrvAlt->out, name())
        ,thunker_contOut_1_uContAlt("thunker_contOut_1_uContAlt", contOut_1, uContAlt->contOut, name())
        ,thunker_out_2_uDrvSolo("thunker_out_2_uDrvSolo", out_2, uDrvSolo->out, name())
        ,thunker_out_4_uLeafSoloB("thunker_out_4_uLeafSoloB", out_4, uLeafSoloB->out, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uContDef->contIn(out_0);
    uChkDef->in(contOut_0);
    uContAlt->contIn(out_1);
    uChkAlt->in(contOut_1);
    uLeafSoloA->in(out_2);
    uLeafSoloA->out(out_3);
    uLeafSoloB->in(out_3);
    uChkSolo->in(out_4);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
