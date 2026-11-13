//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegs --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module uvmRegs.testbench;
import uvmRegs.base;
import uvmRegs.external;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace uvmRegs_ns;

export class uvmRegsTestbench: public sc_module, public blockBase, public uvmRegsChannels {

public:

    std::shared_ptr<uvmRegsBase> uvmRegs;
    uvmRegsExternal external;

    uvmRegsTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (uvmRegsTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_uvmRegsTestbench_variants() {
    instanceFactory::registerBlock("uvmRegsTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsTestbench>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegsTestbench_registered = (register_uvmRegsTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

uvmRegsTestbench::uvmRegsTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("uvmRegsTestbench", name(), bbMode)
        ,uvmRegsChannels("Chnl", "tb")
        ,uvmRegs(std::dynamic_pointer_cast<uvmRegsBase>( instanceFactory::createInstance(name(), "uvmRegs", "uvmRegs", "", "uvmRegs")))
        ,external("external")
{
    bind(uvmRegs.get(), &external);
}
// GENERATED_CODE_END
