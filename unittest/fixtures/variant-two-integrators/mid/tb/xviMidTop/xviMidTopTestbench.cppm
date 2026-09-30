//

// GENERATED_CODE_PARAM --block=xviMidTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xviLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xviMid_xviMidTop.testbench;
import xviMid_xviMidTop.base;
import xviMid_xviMidTop.external;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header


export class xviMidTopTestbench: public sc_module, public blockBase, public xviMidTopChannels {

public:

    std::shared_ptr<xviMidTopBase> xviMidTop;
    xviMidTopExternal external;

    xviMidTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xviMidTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xviMidTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xviMidTopTestbench_variants() {
    instanceFactory::registerBlock("xviMidTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviMidTopTestbench>(blockName, variant, bbMode)); }, "", "xviMid");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xviMidTopTestbench_registered = (register_xviMidTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xviMidTopTestbench::xviMidTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xviMidTopTestbench", name(), bbMode)
        ,xviMidTopChannels("Chnl", "tb")
        ,xviMidTop(std::dynamic_pointer_cast<xviMidTopBase>( instanceFactory::createInstance(name(), "xviMidTop", "xviMidTop", "", "xviMid")))
        ,external("external")
{
    bind(xviMidTop.get(), &external);
}
// GENERATED_CODE_END
