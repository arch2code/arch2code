//

// GENERATED_CODE_PARAM --block=xpDpTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpDpTop.testbench;
import xpDpTop.base;
import xpDpTop.external;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header


export class xpDpTopTestbench: public sc_module, public blockBase, public xpDpTopChannels {

public:

    std::shared_ptr<xpDpTopBase> xpDpTop;
    xpDpTopExternal external;

    xpDpTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpDpTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpDpTopTestbench_variants() {
    instanceFactory::registerBlock("xpDpTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpTopTestbench>(blockName, variant, bbMode)); }, "", "xpDpTop");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpDpTopTestbench_registered = (register_xpDpTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpDpTopTestbench::xpDpTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpDpTopTestbench", name(), bbMode)
        ,xpDpTopChannels("Chnl", "tb")
        ,xpDpTop(std::dynamic_pointer_cast<xpDpTopBase>( instanceFactory::createInstance(name(), "xpDpTop", "xpDpTop", "", "xpDpTop")))
        ,external("external")
{
    bind(xpDpTop.get(), &external);
}
// GENERATED_CODE_END
