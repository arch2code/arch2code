//

// GENERATED_CODE_PARAM --block=vliWrap --mode=module
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
export module vlInh_vliWrap.block;
import vlInh_vliWrap.base;
import vlInh.vliChk.config;
import vlInh.vliCont.config;
import vlInh.vliDrv.config;
import vlInh.vliLeaf.config;
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
    push_ack_channel< vliSt<vlInh_vliContDefaultConfig> > out_0;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vlInh_vliChkChkDefConfig> > contOut_0;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vlInh_vliContAltConfig> > out_1;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vlInh_vliChkChkAltConfig> > contOut_1;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vlInh_vliLeafSoloConfig> > out_2;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vlInh_vliLeafSoloConfig> > out_3;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vlInh_vliChkChkSoloConfig> > out_4;

    //instances contained in block
    std::shared_ptr<vliDrvBase<vlInh_vliDrvDrvDefConfig>> uDrvDef;
    std::shared_ptr<vliDrvBase<vlInh_vliDrvDrvAltConfig>> uDrvAlt;
    std::shared_ptr<vliDrvBase<vlInh_vliDrvDrvSoloConfig>> uDrvSolo;
    std::shared_ptr<vliContBase<vlInh_vliContDefaultConfig>> uContDef;
    std::shared_ptr<vliContBase<vlInh_vliContAltConfig>> uContAlt;
    std::shared_ptr<vliChkBase<vlInh_vliChkChkDefConfig>> uChkDef;
    std::shared_ptr<vliChkBase<vlInh_vliChkChkAltConfig>> uChkAlt;
    std::shared_ptr<vliChkBase<vlInh_vliChkChkSoloConfig>> uChkSolo;
    std::shared_ptr<vliLeafBase<vlInh_vliLeafSoloConfig>> uLeafSoloA;
    std::shared_ptr<vliLeafBase<vlInh_vliLeafSoloConfig>> uLeafSoloB;

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
        ,uDrvDef(std::dynamic_pointer_cast<vliDrvBase<vlInh_vliDrvDrvDefConfig>>(instanceFactory::createInstance(name(), "uDrvDef", "vliDrv", "drvDef", "vlInh.vlInh_vliWrap.vlInh_vliDrv")))
        ,uDrvAlt(std::dynamic_pointer_cast<vliDrvBase<vlInh_vliDrvDrvAltConfig>>(instanceFactory::createInstance(name(), "uDrvAlt", "vliDrv", "drvAlt", "vlInh.vlInh_vliWrap.vlInh_vliDrv")))
        ,uDrvSolo(std::dynamic_pointer_cast<vliDrvBase<vlInh_vliDrvDrvSoloConfig>>(instanceFactory::createInstance(name(), "uDrvSolo", "vliDrv", "drvSolo", "vlInh.vlInh_vliWrap.vlInh_vliDrv")))
        ,uContDef(std::dynamic_pointer_cast<vliContBase<vlInh_vliContDefaultConfig>>(instanceFactory::createInstance(name(), "uContDef", "vliCont", "default", "vlInh.vlInh_vliWrap.vlInh_vliCont")))
        ,uContAlt(std::dynamic_pointer_cast<vliContBase<vlInh_vliContAltConfig>>(instanceFactory::createInstance(name(), "uContAlt", "vliCont", "alt", "vlInh.vlInh_vliWrap.vlInh_vliCont")))
        ,uChkDef(std::dynamic_pointer_cast<vliChkBase<vlInh_vliChkChkDefConfig>>(instanceFactory::createInstance(name(), "uChkDef", "vliChk", "chkDef", "vlInh.vlInh_vliWrap.vlInh_vliChk")))
        ,uChkAlt(std::dynamic_pointer_cast<vliChkBase<vlInh_vliChkChkAltConfig>>(instanceFactory::createInstance(name(), "uChkAlt", "vliChk", "chkAlt", "vlInh.vlInh_vliWrap.vlInh_vliChk")))
        ,uChkSolo(std::dynamic_pointer_cast<vliChkBase<vlInh_vliChkChkSoloConfig>>(instanceFactory::createInstance(name(), "uChkSolo", "vliChk", "chkSolo", "vlInh.vlInh_vliWrap.vlInh_vliChk")))
        ,uLeafSoloA(std::dynamic_pointer_cast<vliLeafBase<vlInh_vliLeafSoloConfig>>(instanceFactory::createInstance(name(), "uLeafSoloA", "vliLeaf", "solo", "vlInh.vlInh_vliWrap.vlInh_vliLeaf")))
        ,uLeafSoloB(std::dynamic_pointer_cast<vliLeafBase<vlInh_vliLeafSoloConfig>>(instanceFactory::createInstance(name(), "uLeafSoloB", "vliLeaf", "solo", "vlInh.vlInh_vliWrap.vlInh_vliLeaf")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uDrvDef->out(out_0);
    uContDef->contIn(out_0);
    uContDef->contOut(contOut_0);
    uChkDef->in(contOut_0);
    uDrvAlt->out(out_1);
    uContAlt->contIn(out_1);
    uContAlt->contOut(contOut_1);
    uChkAlt->in(contOut_1);
    uDrvSolo->out(out_2);
    uLeafSoloA->in(out_2);
    uLeafSoloA->out(out_3);
    uLeafSoloB->in(out_3);
    uLeafSoloB->out(out_4);
    uChkSolo->in(out_4);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
