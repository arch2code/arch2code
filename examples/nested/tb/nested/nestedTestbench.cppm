//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nested --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module nested.testbench;
import nested.base;
import nested.external;
import nested;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace nested_ns;

export class nestedTestbench: public sc_module, public blockBase, public nestedChannels {

public:

    std::shared_ptr<nestedBase> nested;
    nestedExternal external;

    nestedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (nestedTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_nestedTestbench_variants() {
    instanceFactory::registerBlock("nestedTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedTestbench>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nestedTestbench_registered = (register_nestedTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

nestedTestbench::nestedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("nestedTestbench", name(), bbMode)
        ,nestedChannels("Chnl", "tb")
        ,nested(std::dynamic_pointer_cast<nestedBase>( instanceFactory::createInstance(name(), "nested", "nested", "", "nested")))
        ,external("external")
{
    bind(nested.get(), &external);
}
// GENERATED_CODE_END
