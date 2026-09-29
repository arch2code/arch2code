//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=someRapper --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module apbDecode_someRapper.testbench;
import apbDecode_someRapper.base;
import apbDecode_someRapper.external;
import apbDecode;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace apbDecode_ns;

export class someRapperTestbench: public sc_module, public blockBase, public someRapperChannels {

public:

    std::shared_ptr<someRapperBase> someRapper;
    someRapperExternal external;

    someRapperTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~someRapperTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (someRapperTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_someRapperTestbench_variants() {
    instanceFactory::registerBlock("someRapperTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<someRapperTestbench>(blockName, variant, bbMode)); }, "", "apbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _someRapperTestbench_registered = (register_someRapperTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

someRapperTestbench::someRapperTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("someRapperTestbench", name(), bbMode)
        ,someRapperChannels("Chnl", "tb")
        ,someRapper(std::dynamic_pointer_cast<someRapperBase>( instanceFactory::createInstance(name(), "someRapper", "someRapper", "", "apbDecode")))
        ,external("external")
{
    bind(someRapper.get(), &external);
}
// GENERATED_CODE_END
