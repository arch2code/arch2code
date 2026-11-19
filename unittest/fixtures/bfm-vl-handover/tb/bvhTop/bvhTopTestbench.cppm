//

// GENERATED_CODE_PARAM --block=bvhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module bfmVlHandover_bvhTop.testbench;
import bfmVlHandover_bvhTop.base;
import bfmVlHandover_bvhTop.external;
import bfmVlHandover_bvh;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace bfmVlHandover_bvh_ns;

export class bvhTopTestbench: public sc_module, public blockBase, public bvhTopChannels {

public:

    std::shared_ptr<bvhTopBase> bvhTop;
    bvhTopExternal external;

    bvhTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bvhTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (bvhTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_bvhTopTestbench_variants() {
    instanceFactory::registerBlock("bvhTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bvhTopTestbench>(blockName, variant, bbMode)); }, "", "bfmVlHandover");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _bvhTopTestbench_registered = (register_bvhTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

bvhTopTestbench::bvhTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("bvhTopTestbench", name(), bbMode)
        ,bvhTopChannels("Chnl", "tb")
        ,bvhTop(std::dynamic_pointer_cast<bvhTopBase>( instanceFactory::createInstance(name(), "bvhTop", "bvhTop", "", "bfmVlHandover")))
        ,external("external")
{
    bind(bvhTop.get(), &external);
}
// GENERATED_CODE_END
