//

// GENERATED_CODE_PARAM --block=xpTwoCtxTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpTwoCtx_xpTwoCtxTop.testbench;
import xpTwoCtx_xpTwoCtxTop.base;
import xpTwoCtx_xpTwoCtxTop.external;
import xpTwoCtx;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpTwoCtx_ns;

export class xpTwoCtxTopTestbench: public sc_module, public blockBase, public xpTwoCtxTopChannels {

public:

    std::shared_ptr<xpTwoCtxTopBase> xpTwoCtxTop;
    xpTwoCtxTopExternal external;

    xpTwoCtxTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpTwoCtxTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpTwoCtxTopTestbench_variants() {
    instanceFactory::registerBlock("xpTwoCtxTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxTopTestbench>(blockName, variant, bbMode)); }, "", "xpTwoCtx");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpTwoCtxTopTestbench_registered = (register_xpTwoCtxTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpTwoCtxTopTestbench::xpTwoCtxTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpTwoCtxTopTestbench", name(), bbMode)
        ,xpTwoCtxTopChannels("Chnl", "tb")
        ,xpTwoCtxTop(std::dynamic_pointer_cast<xpTwoCtxTopBase>( instanceFactory::createInstance(name(), "xpTwoCtxTop", "xpTwoCtxTop", "", "xpTwoCtx")))
        ,external("external")
{
    bind(xpTwoCtxTop.get(), &external);
}
// GENERATED_CODE_END
