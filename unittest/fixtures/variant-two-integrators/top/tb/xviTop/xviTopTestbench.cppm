//

// GENERATED_CODE_PARAM --block=xviTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xviLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xviTop.testbench;
import xviTop.base;
import xviTop.external;
import xviLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xviLeaf_ns;

export class xviTopTestbench: public sc_module, public blockBase, public xviTopChannels {

public:

    std::shared_ptr<xviTopBase> xviTop;
    xviTopExternal external;

    xviTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xviTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xviTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xviTopTestbench_variants() {
    instanceFactory::registerBlock("xviTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviTopTestbench>(blockName, variant, bbMode)); }, "", "xviTop");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xviTopTestbench_registered = (register_xviTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xviTopTestbench::xviTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xviTopTestbench", name(), bbMode)
        ,xviTopChannels("Chnl", "tb")
        ,xviTop(std::dynamic_pointer_cast<xviTopBase>( instanceFactory::createInstance(name(), "xviTop", "xviTop", "", "xviTop")))
        ,external("external")
{
    bind(xviTop.get(), &external);
}
// GENERATED_CODE_END
