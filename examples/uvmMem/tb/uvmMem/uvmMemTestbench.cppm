//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module uvmMem.testbench;
import uvmMem.base;
import uvmMem.external;
import uvmMem;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace uvmMem_ns;

export class uvmMemTestbench: public sc_module, public blockBase, public uvmMemChannels {

public:

    std::shared_ptr<uvmMemBase> uvmMem;
    uvmMemExternal external;

    uvmMemTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmMemTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (uvmMemTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_uvmMemTestbench_variants() {
    instanceFactory::registerBlock("uvmMemTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmMemTestbench>(blockName, variant, bbMode)); }, "", "uvmMem");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmMemTestbench_registered = (register_uvmMemTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

uvmMemTestbench::uvmMemTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("uvmMemTestbench", name(), bbMode)
        ,uvmMemChannels("Chnl", "tb")
        ,uvmMem(std::dynamic_pointer_cast<uvmMemBase>( instanceFactory::createInstance(name(), "uvmMem", "uvmMem", "", "uvmMem")))
        ,external("external")
{
    bind(uvmMem.get(), &external);
}
// GENERATED_CODE_END
