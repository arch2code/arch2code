//

// GENERATED_CODE_PARAM --block=xpMtxCompTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpMtxComp_xpMtxCompTop.testbench;
import xpMtxComp_xpMtxCompTop.base;
import xpMtxComp_xpMtxCompTop.external;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header


export class xpMtxCompTopTestbench: public sc_module, public blockBase, public xpMtxCompTopChannels {

public:

    std::shared_ptr<xpMtxCompTopBase> xpMtxCompTop;
    xpMtxCompTopExternal external;

    xpMtxCompTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxCompTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpMtxCompTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpMtxCompTopTestbench_variants() {
    instanceFactory::registerBlock("xpMtxCompTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxCompTopTestbench>(blockName, variant, bbMode)); }, "", "xpMtxComp");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxCompTopTestbench_registered = (register_xpMtxCompTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxCompTopTestbench::xpMtxCompTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpMtxCompTopTestbench", name(), bbMode)
        ,xpMtxCompTopChannels("Chnl", "tb")
        ,xpMtxCompTop(std::dynamic_pointer_cast<xpMtxCompTopBase>( instanceFactory::createInstance(name(), "xpMtxCompTop", "xpMtxCompTop", "", "xpMtxComp")))
        ,external("external")
{
    bind(xpMtxCompTop.get(), &external);
}
// GENERATED_CODE_END
