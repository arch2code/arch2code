//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module helloWorld.testbench;
import helloWorld.base;
import helloWorld.external;
import helloWorld_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace helloWorld_tb_ns;

export class helloWorldTestbench: public sc_module, public blockBase, public helloWorldChannels {

public:

    std::shared_ptr<helloWorldBase> helloWorld;
    helloWorldExternal external;

    helloWorldTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~helloWorldTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (helloWorldTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_helloWorldTestbench_variants() {
    instanceFactory::registerBlock("helloWorldTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<helloWorldTestbench>(blockName, variant, bbMode)); }, "", "helloWorld");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _helloWorldTestbench_registered = (register_helloWorldTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

helloWorldTestbench::helloWorldTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("helloWorldTestbench", name(), bbMode)
        ,helloWorldChannels("Chnl", "tb")
        ,helloWorld(std::dynamic_pointer_cast<helloWorldBase>( instanceFactory::createInstance(name(), "helloWorld", "helloWorld", "", "helloWorld")))
        ,external("external")
{
    bind(helloWorld.get(), &external);
}
// GENERATED_CODE_END
