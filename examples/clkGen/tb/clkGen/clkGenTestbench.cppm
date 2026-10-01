//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module clkGen.testbench;
import clkGen.base;
import clkGen.external;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header


export class clkGenTestbench: public sc_module, public blockBase, public clkGenChannels {

public:

    std::shared_ptr<clkGenBase> clkGen;
    clkGenExternal external;

    clkGenTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~clkGenTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (clkGenTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_clkGenTestbench_variants() {
    instanceFactory::registerBlock("clkGenTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkGenTestbench>(blockName, variant, bbMode)); }, "", "clkGen");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _clkGenTestbench_registered = (register_clkGenTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

clkGenTestbench::clkGenTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("clkGenTestbench", name(), bbMode)
        ,clkGenChannels("Chnl", "tb")
        ,clkGen(std::dynamic_pointer_cast<clkGenBase>( instanceFactory::createInstance(name(), "clkGen", "clkGen", "", "clkGen")))
        ,external("external")
{
    bind(clkGen.get(), &external);
}
// GENERATED_CODE_END
