//

// GENERATED_CODE_PARAM --block=vltTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module vlTiming_vltTop.testbench;
import vlTiming_vltTop.base;
import vlTiming_vltTop.external;
import vlTiming_vlt;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace vlTiming_vlt_ns;

export class vltTopTestbench: public sc_module, public blockBase, public vltTopChannels {

public:

    std::shared_ptr<vltTopBase> vltTop;
    vltTopExternal external;

    vltTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vltTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (vltTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_vltTopTestbench_variants() {
    instanceFactory::registerBlock("vltTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vltTopTestbench>(blockName, variant, bbMode)); }, "", "vlTiming");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _vltTopTestbench_registered = (register_vltTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

vltTopTestbench::vltTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("vltTopTestbench", name(), bbMode)
        ,vltTopChannels("Chnl", "tb")
        ,vltTop(std::dynamic_pointer_cast<vltTopBase>( instanceFactory::createInstance(name(), "vltTop", "vltTop", "", "vlTiming")))
        ,external("external")
{
    bind(vltTop.get(), &external);
}
// GENERATED_CODE_END
