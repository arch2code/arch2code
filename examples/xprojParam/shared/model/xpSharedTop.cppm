//

// GENERATED_CODE_PARAM --block=xpSharedTop --mode=module
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
export module xpShared_xpSharedTop.block;
import xpShared_xpSharedTop.base;
import xpFilterShared.xpFilterShared.config;
import xpGain.xpGain.config;
import xpSinkShared.xpSinkShared.config;
import xpGain;
import xpGain.base;
import xpFilterShared.base;
import xpSinkShared.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpGain_ns;
export SC_MODULE(xpSharedTop), public blockBase, public xpSharedTopBase
{
private:

public:
    // channels
    // Parameterized pixel push/ack stream
    push_ack_channel< videoSt<xpFilterShared_xpFilterSharedV0Config> > videoOut_0;
    // Parameterized pixel push/ack stream
    push_ack_channel< videoSt<xpSinkShared_xpSinkSharedV0Config> > videoOut_1;

    //instances contained in block
    std::shared_ptr<xpGainBase<xpGain_xpGainV0Config>> uGain;
    std::shared_ptr<xpFilterSharedBase<xpFilterShared_xpFilterSharedV0Config>> uFilter;
    std::shared_ptr<xpSinkSharedBase<xpSinkShared_xpSinkSharedV0Config>> uSink;

    // cross-interface thunkers
    push_ack_port_thunker<videoSt<xpFilterShared_xpFilterSharedV0Config>, videoSt<xpGain_xpGainV0Config>, true> thunker_videoOut_0_uGain;
    push_ack_port_thunker<videoSt<xpSinkShared_xpSinkSharedV0Config>, videoSt<xpFilterShared_xpFilterSharedV0Config>, true> thunker_videoOut_1_uFilter;

    xpSharedTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpSharedTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpSharedTop);

// === Block factory registration (xpSharedTop) ===
void register_xpSharedTop_variants() {
    instanceFactory::registerBlock("xpSharedTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSharedTop>(blockName, variant, bbMode)); }, "", "xpShared");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpSharedTop_registered = (register_xpSharedTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpSharedTop::xpSharedTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpSharedTop", name(), bbMode)
        ,xpSharedTopBase(name(), variant)
        ,videoOut_0("xpFilterShared_videoOut_0", "xpGain")
        ,videoOut_1("xpSinkShared_videoOut_1", "xpFilterShared")
        ,uGain(std::dynamic_pointer_cast<xpGainBase<xpGain_xpGainV0Config>>(instanceFactory::createInstance(name(), "uGain", "xpGain", "v0", "xpShared.xpShared_xpSharedTop.xpGain")))
        ,uFilter(std::dynamic_pointer_cast<xpFilterSharedBase<xpFilterShared_xpFilterSharedV0Config>>(instanceFactory::createInstance(name(), "uFilter", "xpFilterShared", "v0", "xpShared.xpShared_xpSharedTop.xpFilterShared")))
        ,uSink(std::dynamic_pointer_cast<xpSinkSharedBase<xpSinkShared_xpSinkSharedV0Config>>(instanceFactory::createInstance(name(), "uSink", "xpSinkShared", "v0", "xpShared.xpShared_xpSharedTop.xpSinkShared")))
        ,thunker_videoOut_0_uGain("thunker_videoOut_0_uGain", videoOut_0, uGain->videoOut, name())
        ,thunker_videoOut_1_uFilter("thunker_videoOut_1_uFilter", videoOut_1, uFilter->videoOut, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uFilter->videoIn(videoOut_0);
    uSink->videoIn(videoOut_1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

