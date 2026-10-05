//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=core --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module hier_core.testbench;
import hier_core.base;
import hier_core.external;
import hier_core;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace hier_core_ns;

export class coreTestbench: public sc_module, public blockBase, public coreChannels {

public:

    std::shared_ptr<coreBase> core;
    coreExternal external;

    coreTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~coreTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (coreTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_coreTestbench_variants() {
    instanceFactory::registerBlock("coreTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<coreTestbench>(blockName, variant, bbMode)); }, "", "hier");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _coreTestbench_registered = (register_coreTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

coreTestbench::coreTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("coreTestbench", name(), bbMode)
        ,coreChannels("Chnl", "tb")
        ,core(std::dynamic_pointer_cast<coreBase>( instanceFactory::createInstance(name(), "core", "core", "", "hier")))
        ,external("external")
{
    bind(core.get(), &external);
}
// GENERATED_CODE_END
