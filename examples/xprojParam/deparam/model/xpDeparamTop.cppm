//

// GENERATED_CODE_PARAM --block=xpDeparamTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpFilterVariantConfig.h"
#include "xpGainVariantConfig.h"
#include "xpSinkVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpDeparam_xpDeparamTop.block;
import xpDeparam_xpDeparamTop.base;
import xpDeparam_xpDeparamTop;
import xpGain;
import xpFilter;
import xpSink;
import xpGain.base;
import xpFilter.base;
import xpSink.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDeparam_xpDeparamTop_ns;
using namespace xpGain_ns;
using namespace xpFilter_ns;
using namespace xpSink_ns;
export SC_MODULE(xpDeparamTop), public blockBase, public xpDeparamTopBase
{
private:

public:
    // channels
    // Assembler-owned literal-width push/ack boundary stream
    push_ack_channel< boundarySt > videoOut_0;
    // Assembler-owned literal-width push/ack boundary stream
    push_ack_channel< boundarySt > videoOut_1;

    //instances contained in block
    std::shared_ptr<xpGainBase<xpGainV0Config>> uGain;
    std::shared_ptr<xpFilterBase<xpFilterV0Config>> uFilter;
    std::shared_ptr<xpSinkBase<xpSinkV0Config>> uSink;

    // cross-interface thunkers
    push_ack_port_thunker<boundarySt, videoSt<xpGainV0Config>, false> thunker_videoOut_0_uGain;
    push_ack_port_thunker<boundarySt, videoSt<xpFilterV0Config>, false> thunker_videoOut_0_uFilter;
    push_ack_port_thunker<boundarySt, videoSt<xpFilterV0Config>, false> thunker_videoOut_1_uFilter;
    push_ack_port_thunker<boundarySt, videoSt<xpSinkV0Config>, false> thunker_videoOut_1_uSink;

    xpDeparamTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDeparamTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpDeparamTop);

// === Block factory registration (xpDeparamTop) ===
void register_xpDeparamTop_variants() {
    instanceFactory::registerBlock("xpDeparamTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDeparamTop>(blockName, variant, bbMode)); }, "", "xpDeparam");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpDeparamTop_registered = (register_xpDeparamTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpDeparamTop::xpDeparamTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDeparamTop", name(), bbMode)
        ,xpDeparamTopBase(name(), variant)
        ,videoOut_0("xpFilter_videoOut_0", "xpGain")
        ,videoOut_1("xpSink_videoOut_1", "xpFilter")
        ,uGain(std::dynamic_pointer_cast<xpGainBase<xpGainV0Config>>(instanceFactory::createInstance(name(), "uGain", "xpGain", "v0", "xpDeparam.xpDeparam_xpDeparamTop.xpGain")))
        ,uFilter(std::dynamic_pointer_cast<xpFilterBase<xpFilterV0Config>>(instanceFactory::createInstance(name(), "uFilter", "xpFilter", "v0", "xpDeparam.xpDeparam_xpDeparamTop.xpFilter")))
        ,uSink(std::dynamic_pointer_cast<xpSinkBase<xpSinkV0Config>>(instanceFactory::createInstance(name(), "uSink", "xpSink", "v0", "xpDeparam.xpDeparam_xpDeparamTop.xpSink")))
        ,thunker_videoOut_0_uGain("thunker_videoOut_0_uGain", videoOut_0, uGain->videoOut, name())
        ,thunker_videoOut_0_uFilter("thunker_videoOut_0_uFilter", videoOut_0, uFilter->videoIn, name())
        ,thunker_videoOut_1_uFilter("thunker_videoOut_1_uFilter", videoOut_1, uFilter->videoOut, name())
        ,thunker_videoOut_1_uSink("thunker_videoOut_1_uSink", videoOut_1, uSink->videoIn, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

