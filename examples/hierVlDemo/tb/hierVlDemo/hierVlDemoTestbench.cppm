//

// GENERATED_CODE_PARAM --block=hierVlDemo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module hierVlDemo.testbench;
import hierVlDemo.base;
import hierVlDemo.external;
import hierVlDemo_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace hierVlDemo_tb_ns;

export class hierVlDemoTestbench: public sc_module, public blockBase, public hierVlDemoChannels {

public:

    std::shared_ptr<hierVlDemoBase> hierVlDemo;
    hierVlDemoExternal external;

    hierVlDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~hierVlDemoTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (hierVlDemoTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_hierVlDemoTestbench_variants() {
    instanceFactory::registerBlock("hierVlDemoTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<hierVlDemoTestbench>(blockName, variant, bbMode)); }, "", "hierVlDemo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _hierVlDemoTestbench_registered = (register_hierVlDemoTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

hierVlDemoTestbench::hierVlDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("hierVlDemoTestbench", name(), bbMode)
        ,hierVlDemoChannels("Chnl", "tb")
        ,hierVlDemo(std::dynamic_pointer_cast<hierVlDemoBase>( instanceFactory::createInstance(name(), "hierVlDemo", "hierVlDemo", "", "hierVlDemo")))
        ,external("external")
{
    bind(hierVlDemo.get(), &external);
}
// GENERATED_CODE_END
