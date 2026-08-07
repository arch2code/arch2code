//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dut --variant=dutV0 --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xifVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xif_dut.testbench;
import xif_dut.base;
import xif_dut.external;
import xif;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xif_ns;

export class dutTestbench: public sc_module, public blockBase, public dutChannels<dutDutV0Config> {

public:

    std::shared_ptr<dutBase<dutDutV0Config>> dut;
    dutExternal external;

    dutTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dutTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (dutTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_dutTestbench_variants() {
    instanceFactory::registerBlock("dutTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dutTestbench>(blockName, variant, bbMode)); }, "", "xif");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _dutTestbench_registered = (register_dutTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

dutTestbench::dutTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("dutTestbench", name(), bbMode)
        ,dutChannels<dutDutV0Config>("Chnl", "tb")
        ,dut(std::dynamic_pointer_cast<dutBase<dutDutV0Config>>( instanceFactory::createInstance(name(), "dut", "dut", "dutV0", "xif")))
        ,external("external")
{
    bind(dut.get(), &external);
}
// GENERATED_CODE_END
