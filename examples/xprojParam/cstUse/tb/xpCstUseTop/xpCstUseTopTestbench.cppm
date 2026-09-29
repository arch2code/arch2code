//

// GENERATED_CODE_PARAM --block=xpCstUseTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpCstUse_xpCstUseTop.testbench;
import xpCstUse_xpCstUseTop.base;
import xpCstUse_xpCstUseTop.external;
import xpCstUse_xpCstUseTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpCstUse_xpCstUseTop_ns;

export class xpCstUseTopTestbench: public sc_module, public blockBase, public xpCstUseTopChannels {

public:

    std::shared_ptr<xpCstUseTopBase> xpCstUseTop;
    xpCstUseTopExternal external;

    xpCstUseTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstUseTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpCstUseTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpCstUseTopTestbench_variants() {
    instanceFactory::registerBlock("xpCstUseTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstUseTopTestbench>(blockName, variant, bbMode)); }, "", "xpCstUse");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCstUseTopTestbench_registered = (register_xpCstUseTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpCstUseTopTestbench::xpCstUseTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpCstUseTopTestbench", name(), bbMode)
        ,xpCstUseTopChannels("Chnl", "tb")
        ,xpCstUseTop(std::dynamic_pointer_cast<xpCstUseTopBase>( instanceFactory::createInstance(name(), "xpCstUseTop", "xpCstUseTop", "", "xpCstUse")))
        ,external("external")
{
    bind(xpCstUseTop.get(), &external);
}
// GENERATED_CODE_END
