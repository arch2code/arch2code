//

// GENERATED_CODE_PARAM --block=xpUniqTop --mode=module
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
export module xpUniq_xpUniqTop.block;
import xpUniq_xpUniqTop.base;
import xpFilter.xpFilterUniq.config;
import xpGain.xpGainUniq.config;
import xpSink.xpSinkUniq.config;
import xpUniq_xpUniqTop;
import xpGain_xpGainUniq;
import xpFilter_xpFilterUniq;
import xpSink_xpSinkUniq;
import xpGain_xpGainUniq.base;
import xpFilter_xpFilterUniq.base;
import xpSink_xpSinkUniq.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpUniq_xpUniqTop_ns;
using namespace xpGain_xpGainUniq_ns;
using namespace xpFilter_xpFilterUniq_ns;
using namespace xpSink_xpSinkUniq_ns;
export SC_MODULE(xpUniqTop), public blockBase, public xpUniqTopBase
{
private:

public:
    // channels
    // Assembler-owned literal-width push/ack boundary stream
    push_ack_channel< boundarySt > videoOut_0;
    // Assembler-owned literal-width push/ack boundary stream
    push_ack_channel< boundarySt > videoOut_1;

    //instances contained in block
    std::shared_ptr<xpGainUniqBase<xpGain_xpGainUniqV0Config>> uGain;
    std::shared_ptr<xpFilterUniqBase<xpFilter_xpFilterUniqV0Config>> uFilter;
    std::shared_ptr<xpSinkUniqBase<xpSink_xpSinkUniqV0Config>> uSink;

    // cross-interface thunkers
    push_ack_port_thunker<boundarySt, gnVideoSt<xpGain_xpGainUniqV0Config>, false> thunker_videoOut_0_uGain;
    push_ack_port_thunker<boundarySt, flVideoSt<xpFilter_xpFilterUniqV0Config>, false> thunker_videoOut_0_uFilter;
    push_ack_port_thunker<boundarySt, flVideoSt<xpFilter_xpFilterUniqV0Config>, false> thunker_videoOut_1_uFilter;
    push_ack_port_thunker<boundarySt, skVideoSt<xpSink_xpSinkUniqV0Config>, false> thunker_videoOut_1_uSink;

    xpUniqTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpUniqTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpUniqTop);

// === Block factory registration (xpUniqTop) ===
void register_xpUniqTop_variants() {
    instanceFactory::registerBlock("xpUniqTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpUniqTop>(blockName, variant, bbMode)); }, "", "xpUniq");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpUniqTop_registered = (register_xpUniqTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpUniqTop::xpUniqTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpUniqTop", name(), bbMode)
        ,xpUniqTopBase(name(), variant)
        ,videoOut_0("xpFilterUniq_videoOut_0", "xpGainUniq")
        ,videoOut_1("xpSinkUniq_videoOut_1", "xpFilterUniq")
        ,uGain(std::dynamic_pointer_cast<xpGainUniqBase<xpGain_xpGainUniqV0Config>>(instanceFactory::createInstance(name(), "uGain", "xpGainUniq", "v0", "xpUniq.xpUniq_xpUniqTop.xpGain_xpGainUniq")))
        ,uFilter(std::dynamic_pointer_cast<xpFilterUniqBase<xpFilter_xpFilterUniqV0Config>>(instanceFactory::createInstance(name(), "uFilter", "xpFilterUniq", "v0", "xpUniq.xpUniq_xpUniqTop.xpFilter_xpFilterUniq")))
        ,uSink(std::dynamic_pointer_cast<xpSinkUniqBase<xpSink_xpSinkUniqV0Config>>(instanceFactory::createInstance(name(), "uSink", "xpSinkUniq", "v0", "xpUniq.xpUniq_xpUniqTop.xpSink_xpSinkUniq")))
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

