//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module simple.testbench;
import simple.base;
import simple.external;
import simple;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace simple_ns;

export class simpleTestbench: public sc_module, public blockBase, public simpleChannels {

public:

    std::shared_ptr<simpleBase> simple;
    simpleExternal external;

    simpleTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simpleTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (simpleTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_simpleTestbench_variants() {
    instanceFactory::registerBlock("simpleTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<simpleTestbench>(blockName, variant, bbMode)); }, "", "simple");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _simpleTestbench_registered = (register_simpleTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

simpleTestbench::simpleTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("simpleTestbench", name(), bbMode)
        ,simpleChannels("Chnl", "tb")
        ,simple(std::dynamic_pointer_cast<simpleBase>( instanceFactory::createInstance(name(), "simple", "simple", "", "simple")))
        ,external("external")
{
    bind(simple.get(), &external);
}
// GENERATED_CODE_END
