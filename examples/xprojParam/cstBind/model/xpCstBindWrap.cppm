//

// GENERATED_CODE_PARAM --block=xpCstBindWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpCstIpVariantConfig.h"
#include "xpCstSupVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCstBind_xpCstBindWrap.block;
import xpCstBind_xpCstBindWrap.base;
import xpCstBind.xpCstChkInc.config;
import xpCstBind.xpCstDut.config;
import xpCstBind.xpCstSrcInc.config;
import xpCstIp;
import xpCstBind_xpCstSup;
import xpCstBind_xpCstSrcInc.base;
import xpCstIp_xpCstDut.base;
import xpCstBind_xpCstChkInc.base;
import xpCstBind_xpCstSrcOwn.base;
import xpCstBind_xpCstChkOwn.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstIp_ns;
using namespace xpCstBind_xpCstSup_ns;
export SC_MODULE(xpCstBindWrap), public blockBase, public xpCstBindWrapBase
{
private:

public:
    // channels
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<xpCstDutDfltConfig> > out_0;
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<xpCstBind_xpCstChkIncDfltConfig> > out_1;
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<xpCstBind_xpCstDutUseConfig> > out_2;
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<xpCstBind_xpCstDutUseConfig> > out_3;

    //instances contained in block
    std::shared_ptr<xpCstSrcIncBase<xpCstBind_xpCstSrcIncDfltConfig>> uSrcA;
    std::shared_ptr<xpCstDutBase<xpCstDutDfltConfig>> uDutA;
    std::shared_ptr<xpCstChkIncBase<xpCstBind_xpCstChkIncDfltConfig>> uChkA;
    std::shared_ptr<xpCstSrcOwnBase<xpCstSrcOwnUseConfig>> uSrcB;
    std::shared_ptr<xpCstDutBase<xpCstBind_xpCstDutUseConfig>> uDutB;
    std::shared_ptr<xpCstChkOwnBase<xpCstChkOwnUseConfig>> uChkB;

    // cross-interface thunkers
    push_ack_port_thunker<csDutSt<xpCstDutDfltConfig>, csDutSt<xpCstBind_xpCstSrcIncDfltConfig>, true> thunker_out_0_uSrcA;
    push_ack_port_thunker<csDutSt<xpCstBind_xpCstChkIncDfltConfig>, csDutSt<xpCstDutDfltConfig>, true> thunker_out_1_uDutA;
    push_ack_port_thunker<csDutSt<xpCstBind_xpCstDutUseConfig>, csOwnSt<xpCstSrcOwnUseConfig>, true> thunker_out_2_uSrcB;
    push_ack_port_thunker<csDutSt<xpCstBind_xpCstDutUseConfig>, csOwnSt<xpCstChkOwnUseConfig>, true> thunker_out_3_uChkB;

    xpCstBindWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstBindWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpCstBindWrap);

// === Block factory registration (xpCstBindWrap) ===
void register_xpCstBindWrap_variants() {
    instanceFactory::registerBlock("xpCstBindWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstBindWrap>(blockName, variant, bbMode)); }, "", "xpCstBind");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCstBindWrap_registered = (register_xpCstBindWrap_variants(), 0);
} // namespace
// === End block factory registration ===

xpCstBindWrap::xpCstBindWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstBindWrap", name(), bbMode)
        ,xpCstBindWrapBase(name(), variant)
        ,out_0("xpCstDut_out_0", "xpCstSrcInc")
        ,out_1("xpCstChkInc_out_1", "xpCstDut")
        ,out_2("xpCstDut_out_2", "xpCstSrcOwn")
        ,out_3("xpCstChkOwn_out_3", "xpCstDut")
        ,uSrcA(std::dynamic_pointer_cast<xpCstSrcIncBase<xpCstBind_xpCstSrcIncDfltConfig>>(instanceFactory::createInstance(name(), "uSrcA", "xpCstSrcInc", "dflt", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstBind_xpCstSrcInc")))
        ,uDutA(std::dynamic_pointer_cast<xpCstDutBase<xpCstDutDfltConfig>>(instanceFactory::createInstance(name(), "uDutA", "xpCstDut", "dflt", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstIp_xpCstDut")))
        ,uChkA(std::dynamic_pointer_cast<xpCstChkIncBase<xpCstBind_xpCstChkIncDfltConfig>>(instanceFactory::createInstance(name(), "uChkA", "xpCstChkInc", "dflt", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstBind_xpCstChkInc")))
        ,uSrcB(std::dynamic_pointer_cast<xpCstSrcOwnBase<xpCstSrcOwnUseConfig>>(instanceFactory::createInstance(name(), "uSrcB", "xpCstSrcOwn", "use", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstBind_xpCstSrcOwn")))
        ,uDutB(std::dynamic_pointer_cast<xpCstDutBase<xpCstBind_xpCstDutUseConfig>>(instanceFactory::createInstance(name(), "uDutB", "xpCstDut", "use", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstIp_xpCstDut")))
        ,uChkB(std::dynamic_pointer_cast<xpCstChkOwnBase<xpCstChkOwnUseConfig>>(instanceFactory::createInstance(name(), "uChkB", "xpCstChkOwn", "use", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstBind_xpCstChkOwn")))
        ,thunker_out_0_uSrcA("thunker_out_0_uSrcA", out_0, uSrcA->out, name())
        ,thunker_out_1_uDutA("thunker_out_1_uDutA", out_1, uDutA->out, name())
        ,thunker_out_2_uSrcB("thunker_out_2_uSrcB", out_2, uSrcB->out, name())
        ,thunker_out_3_uChkB("thunker_out_3_uChkB", out_3, uChkB->in, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uDutA->in(out_0);
    uChkA->in(out_1);
    uDutB->in(out_2);
    uDutB->out(out_3);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

