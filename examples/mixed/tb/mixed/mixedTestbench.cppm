//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "mixedVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module mixed.testbench;
import mixed.base;
import mixed.external;
import mixed;
import mixed_mixedBlockC;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace mixed_ns;
using namespace mixed_mixedBlockC_ns;

export class mixedTestbench: public sc_module, public blockBase, public mixedChannels {

public:

    std::shared_ptr<mixedBase> mixed;
    mixedExternal external;

    mixedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~mixedTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (mixedTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_mixedTestbench_variants() {
    instanceFactory::registerBlock("mixedTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<mixedTestbench>(blockName, variant, bbMode)); }, "", "mixed");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _mixedTestbench_registered = (register_mixedTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

mixedTestbench::mixedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("mixedTestbench", name(), bbMode)
        ,mixedChannels("Chnl", "tb")
        ,mixed(std::dynamic_pointer_cast<mixedBase>( instanceFactory::createInstance(name(), "mixed", "mixed", "", "mixed")))
        ,external("external")
{
    bind(mixed.get(), &external);
}
// GENERATED_CODE_END
