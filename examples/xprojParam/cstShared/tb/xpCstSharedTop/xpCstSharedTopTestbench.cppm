//

// GENERATED_CODE_PARAM --block=xpCstSharedTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpCstShared_xpCstSharedTop.testbench;
import xpCstShared_xpCstSharedTop.base;
import xpCstShared_xpCstSharedTop.external;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header


export class xpCstSharedTopTestbench: public sc_module, public blockBase, public xpCstSharedTopChannels {

public:

    std::shared_ptr<xpCstSharedTopBase> xpCstSharedTop;
    xpCstSharedTopExternal external;

    xpCstSharedTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstSharedTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpCstSharedTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpCstSharedTopTestbench_variants() {
    instanceFactory::registerBlock("xpCstSharedTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSharedTopTestbench>(blockName, variant, bbMode)); }, "", "xpCstShared");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCstSharedTopTestbench_registered = (register_xpCstSharedTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpCstSharedTopTestbench::xpCstSharedTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpCstSharedTopTestbench", name(), bbMode)
        ,xpCstSharedTopChannels("Chnl", "tb")
        ,xpCstSharedTop(std::dynamic_pointer_cast<xpCstSharedTopBase>( instanceFactory::createInstance(name(), "xpCstSharedTop", "xpCstSharedTop", "", "xpCstShared")))
        ,external("external")
{
    bind(xpCstSharedTop.get(), &external);
}
// GENERATED_CODE_END
