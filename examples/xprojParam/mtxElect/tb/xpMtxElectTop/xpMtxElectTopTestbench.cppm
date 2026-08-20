//

// GENERATED_CODE_PARAM --block=xpMtxElectTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xpMtxIpVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpMtxElect_xpMtxElectTop.testbench;
import xpMtxElect_xpMtxElectTop.base;
import xpMtxElect_xpMtxElectTop.external;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header


export class xpMtxElectTopTestbench: public sc_module, public blockBase, public xpMtxElectTopChannels {

public:

    std::shared_ptr<xpMtxElectTopBase> xpMtxElectTop;
    xpMtxElectTopExternal external;

    xpMtxElectTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxElectTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpMtxElectTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpMtxElectTopTestbench_variants() {
    instanceFactory::registerBlock("xpMtxElectTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxElectTopTestbench>(blockName, variant, bbMode)); }, "", "xpMtxElect");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxElectTopTestbench_registered = (register_xpMtxElectTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxElectTopTestbench::xpMtxElectTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpMtxElectTopTestbench", name(), bbMode)
        ,xpMtxElectTopChannels("Chnl", "tb")
        ,xpMtxElectTop(std::dynamic_pointer_cast<xpMtxElectTopBase>( instanceFactory::createInstance(name(), "xpMtxElectTop", "xpMtxElectTop", "", "xpMtxElect")))
        ,external("external")
{
    bind(xpMtxElectTop.get(), &external);
}
// GENERATED_CODE_END
