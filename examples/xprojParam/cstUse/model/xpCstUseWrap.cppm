//

// GENERATED_CODE_PARAM --block=xpCstUseWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpCstIpVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCstUse_xpCstUseWrap.block;
import xpCstUse_xpCstUseWrap.base;
import xpCstUse.xpCstDut.config;
import xpCstUse.xpCstUseChk.config;
import xpCstUse.xpCstUseSrc.config;
import xpCstIp;
import xpCstUse_xpCstUseSrc.base;
import xpCstIp_xpCstDut.base;
import xpCstUse_xpCstUseChk.base;
import xpCstUse_xpCstUseTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstIp_ns;
using namespace xpCstUse_xpCstUseTop_ns;
export SC_MODULE(xpCstUseWrap), public blockBase, public xpCstUseWrapBase
{
private:

public:
    // channels
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<xpCstUse_xpCstDutUseConfig> > out_0;
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<xpCstUse_xpCstUseChkUseConfig> > out_1;

    //instances contained in block
    std::shared_ptr<xpCstUseSrcBase<xpCstUse_xpCstUseSrcUseConfig>> uSrc;
    std::shared_ptr<xpCstDutBase<xpCstUse_xpCstDutUseConfig>> uDut;
    std::shared_ptr<xpCstUseChkBase<xpCstUse_xpCstUseChkUseConfig>> uChk;

    // cross-interface thunkers
    push_ack_port_thunker<csDutSt<xpCstUse_xpCstDutUseConfig>, csDutSt<xpCstUse_xpCstUseSrcUseConfig>, true> thunker_out_0_uSrc;
    push_ack_port_thunker<csDutSt<xpCstUse_xpCstUseChkUseConfig>, csDutSt<xpCstUse_xpCstDutUseConfig>, true> thunker_out_1_uDut;

    xpCstUseWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstUseWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpCstUseWrap);

// === Block factory registration (xpCstUseWrap) ===
void register_xpCstUseWrap_variants() {
    instanceFactory::registerBlock("xpCstUseWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstUseWrap>(blockName, variant, bbMode)); }, "", "xpCstUse");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCstUseWrap_registered = (register_xpCstUseWrap_variants(), 0);
} // namespace
// === End block factory registration ===

xpCstUseWrap::xpCstUseWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstUseWrap", name(), bbMode)
        ,xpCstUseWrapBase(name(), variant)
        ,out_0("xpCstDut_out_0", "xpCstUseSrc")
        ,out_1("xpCstUseChk_out_1", "xpCstDut")
        ,uSrc(std::dynamic_pointer_cast<xpCstUseSrcBase<xpCstUse_xpCstUseSrcUseConfig>>(instanceFactory::createInstance(name(), "uSrc", "xpCstUseSrc", "use", "xpCstUse")))
        ,uDut(std::dynamic_pointer_cast<xpCstDutBase<xpCstUse_xpCstDutUseConfig>>(instanceFactory::createInstance(name(), "uDut", "xpCstDut", "use", "xpCstUse")))
        ,uChk(std::dynamic_pointer_cast<xpCstUseChkBase<xpCstUse_xpCstUseChkUseConfig>>(instanceFactory::createInstance(name(), "uChk", "xpCstUseChk", "use", "xpCstUse")))
        ,thunker_out_0_uSrc("thunker_out_0_uSrc", out_0, uSrc->out, name())
        ,thunker_out_1_uDut("thunker_out_1_uDut", out_1, uDut->out, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uDut->in(out_0);
    uChk->in(out_1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

