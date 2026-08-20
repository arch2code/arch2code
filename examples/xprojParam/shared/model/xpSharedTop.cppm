//

// GENERATED_CODE_PARAM --block=xpSharedTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpGainVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpShared_xpSharedTop.block;
import xpShared_xpSharedTop.base;
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
    push_ack_channel< videoSt<xpGainDefaultConfig> > videoOut_0;
    // Parameterized pixel push/ack stream
    push_ack_channel< videoSt<xpGainDefaultConfig> > videoOut_1;

    //instances contained in block
    std::shared_ptr<xpGainBase<xpGainV0Config>> uGain;
    std::shared_ptr<xpFilterSharedBase<xpGainDefaultConfig>> uFilter;
    std::shared_ptr<xpSinkSharedBase<xpGainDefaultConfig>> uSink;

    // cross-interface thunkers
    push_ack_port_thunker<videoSt<xpGainDefaultConfig>, videoSt<xpGainV0Config>, true> thunker_videoOut_0_uGain;

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
        ,uGain(std::dynamic_pointer_cast<xpGainBase<xpGainV0Config>>(instanceFactory::createInstance(name(), "uGain", "xpGain", "v0", "xpShared")))
        ,uFilter(std::dynamic_pointer_cast<xpFilterSharedBase<xpGainDefaultConfig>>(instanceFactory::createInstance(name(), "uFilter", "xpFilterShared", "v0", "xpShared")))
        ,uSink(std::dynamic_pointer_cast<xpSinkSharedBase<xpGainDefaultConfig>>(instanceFactory::createInstance(name(), "uSink", "xpSinkShared", "v0", "xpShared")))
        ,thunker_videoOut_0_uGain("thunker_videoOut_0_uGain", videoOut_0, uGain->videoOut, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uFilter->videoIn(videoOut_0);
    uFilter->videoOut(videoOut_1);
    uSink->videoIn(videoOut_1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

