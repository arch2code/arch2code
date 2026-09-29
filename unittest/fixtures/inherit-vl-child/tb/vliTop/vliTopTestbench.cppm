//

// GENERATED_CODE_PARAM --block=vliTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "vliContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module vlInh_vliTop.testbench;
import vlInh_vliTop.base;
import vlInh_vliTop.external;
import vlInh_vliCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace vlInh_vliCont_ns;

export class vliTopTestbench: public sc_module, public blockBase, public vliTopChannels {

public:

    std::shared_ptr<vliTopBase> vliTop;
    vliTopExternal external;

    vliTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vliTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (vliTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_vliTopTestbench_variants() {
    instanceFactory::registerBlock("vliTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliTopTestbench>(blockName, variant, bbMode)); }, "", "vlInh");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _vliTopTestbench_registered = (register_vliTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

vliTopTestbench::vliTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("vliTopTestbench", name(), bbMode)
        ,vliTopChannels("Chnl", "tb")
        ,vliTop(std::dynamic_pointer_cast<vliTopBase>( instanceFactory::createInstance(name(), "vliTop", "vliTop", "", "vlInh")))
        ,external("external")
{
    bind(vliTop.get(), &external);
}
// GENERATED_CODE_END
