//

// GENERATED_CODE_PARAM --block=xpSharedTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpShared_xpSharedTop.testbench;
import xpShared_xpSharedTop.base;
import xpShared_xpSharedTop.external;
import xpGain;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpGain_ns;

export class xpSharedTopTestbench: public sc_module, public blockBase, public xpSharedTopChannels {

public:

    std::shared_ptr<xpSharedTopBase> xpSharedTop;
    xpSharedTopExternal external;

    xpSharedTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpSharedTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpSharedTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpSharedTopTestbench_variants() {
    instanceFactory::registerBlock("xpSharedTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSharedTopTestbench>(blockName, variant, bbMode)); }, "", "xpShared");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpSharedTopTestbench_registered = (register_xpSharedTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpSharedTopTestbench::xpSharedTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpSharedTopTestbench", name(), bbMode)
        ,xpSharedTopChannels("Chnl", "tb")
        ,xpSharedTop(std::dynamic_pointer_cast<xpSharedTopBase>( instanceFactory::createInstance(name(), "xpSharedTop", "xpSharedTop", "", "xpShared")))
        ,external("external")
{
    bind(xpSharedTop.get(), &external);
}
// GENERATED_CODE_END
