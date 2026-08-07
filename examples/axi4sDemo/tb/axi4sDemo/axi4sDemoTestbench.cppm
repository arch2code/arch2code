//

// GENERATED_CODE_PARAM --block=axi4sDemo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module axi4sDemo.testbench;
import axi4sDemo.base;
import axi4sDemo.external;
import axi4sDemo_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace axi4sDemo_tb_ns;

export class axi4sDemoTestbench: public sc_module, public blockBase, public axi4sDemoChannels {

public:

    std::shared_ptr<axi4sDemoBase> axi4sDemo;
    axi4sDemoExternal external;

    axi4sDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4sDemoTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (axi4sDemoTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_axi4sDemoTestbench_variants() {
    instanceFactory::registerBlock("axi4sDemoTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axi4sDemoTestbench>(blockName, variant, bbMode)); }, "", "axi4sDemo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axi4sDemoTestbench_registered = (register_axi4sDemoTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

axi4sDemoTestbench::axi4sDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("axi4sDemoTestbench", name(), bbMode)
        ,axi4sDemoChannels("Chnl", "tb")
        ,axi4sDemo(std::dynamic_pointer_cast<axi4sDemoBase>( instanceFactory::createInstance(name(), "axi4sDemo", "axi4sDemo", "", "axi4sDemo")))
        ,external("external")
{
    bind(axi4sDemo.get(), &external);
}
// GENERATED_CODE_END
