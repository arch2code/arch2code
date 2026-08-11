//

// GENERATED_CODE_PARAM --block=xpCppAxisTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpCppWrapVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCppAxis_xpCppAxisTop.block;
import xpCppAxis_xpCppAxisTop.base;
import xpCppAxis_xpCppAxisTop;
import xpCppAxis_xpCppWrap;
import xpCppAxis_cppDriver.base;
import xpCppAxis_xpCppWrap.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCppAxis_xpCppAxisTop_ns;
using namespace xpCppAxis_xpCppWrap_ns;
export SC_MODULE(xpCppAxisTop), public blockBase, public xpCppAxisTopBase
{
private:

public:
    // channels
    // Literal-width boundary stream into the wrapper's corresponding port
    push_ack_channel< bndEqSt > eqOut;
    // Literal-width boundary stream into the wrapper's reversed-storage port
    push_ack_channel< bndOrderSt > orderOut;
    // Literal-width boundary stream into the wrapper's unsigned port
    push_ack_channel< bndSignSt > signOut;
    // Literal-width boundary stream into the wrapper's nested port
    push_ack_channel< bndNestSt > nestOut;

    //instances contained in block
    std::shared_ptr<cppDriverBase> uDrive;
    std::shared_ptr<xpCppWrapBase<xpCppWrapV0Config>> uWrap;

    // cross-interface thunkers
    push_ack_port_thunker<bndEqSt, wrapEqSt<xpCppWrapV0Config>, false> thunker_eqOut_uWrap;
    push_ack_port_thunker<bndOrderSt, wrapOrderSt<xpCppWrapV0Config>, false> thunker_orderOut_uWrap;
    push_ack_port_thunker<bndSignSt, wrapSignSt<xpCppWrapV0Config>, false> thunker_signOut_uWrap;
    push_ack_port_thunker<bndNestSt, wrapNestSt<xpCppWrapV0Config>, false> thunker_nestOut_uWrap;

    xpCppAxisTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCppAxisTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpCppAxisTop);

// === Block factory registration (xpCppAxisTop) ===
void register_xpCppAxisTop_variants() {
    instanceFactory::registerBlock("xpCppAxisTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppAxisTop>(blockName, variant, bbMode)); }, "", "xpCppAxis");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCppAxisTop_registered = (register_xpCppAxisTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpCppAxisTop::xpCppAxisTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCppAxisTop", name(), bbMode)
        ,xpCppAxisTopBase(name(), variant)
        ,eqOut("xpCppWrap_eqOut", "cppDriver")
        ,orderOut("xpCppWrap_orderOut", "cppDriver")
        ,signOut("xpCppWrap_signOut", "cppDriver")
        ,nestOut("xpCppWrap_nestOut", "cppDriver")
        ,uDrive(std::dynamic_pointer_cast<cppDriverBase>(instanceFactory::createInstance(name(), "uDrive", "cppDriver", "", "xpCppAxis")))
        ,uWrap(std::dynamic_pointer_cast<xpCppWrapBase<xpCppWrapV0Config>>(instanceFactory::createInstance(name(), "uWrap", "xpCppWrap", "v0", "xpCppAxis")))
        ,thunker_eqOut_uWrap("thunker_eqOut_uWrap", eqOut, uWrap->eqIn, name())
        ,thunker_orderOut_uWrap("thunker_orderOut_uWrap", orderOut, uWrap->orderIn, name())
        ,thunker_signOut_uWrap("thunker_signOut_uWrap", signOut, uWrap->signIn, name())
        ,thunker_nestOut_uWrap("thunker_nestOut_uWrap", nestOut, uWrap->nestIn, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uDrive->eqOut(eqOut);
    uDrive->orderOut(orderOut);
    uDrive->signOut(signOut);
    uDrive->nestOut(nestOut);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

