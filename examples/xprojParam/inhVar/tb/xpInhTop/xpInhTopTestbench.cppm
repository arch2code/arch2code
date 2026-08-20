//

// GENERATED_CODE_PARAM --block=xpInhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xpInhContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpInhVar_xpInhTop.testbench;
import xpInhVar_xpInhTop.base;
import xpInhVar_xpInhTop.external;
import xpInhVar_xpInhCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpInhVar_xpInhCont_ns;

export class xpInhTopTestbench: public sc_module, public blockBase, public xpInhTopChannels {

public:

    std::shared_ptr<xpInhTopBase> xpInhTop;
    xpInhTopExternal external;

    xpInhTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpInhTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpInhTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpInhTopTestbench_variants() {
    instanceFactory::registerBlock("xpInhTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhTopTestbench>(blockName, variant, bbMode)); }, "", "xpInhVar");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpInhTopTestbench_registered = (register_xpInhTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpInhTopTestbench::xpInhTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpInhTopTestbench", name(), bbMode)
        ,xpInhTopChannels("Chnl", "tb")
        ,xpInhTop(std::dynamic_pointer_cast<xpInhTopBase>( instanceFactory::createInstance(name(), "xpInhTop", "xpInhTop", "", "xpInhVar")))
        ,external("external")
{
    bind(xpInhTop.get(), &external);
}
// GENERATED_CODE_END
