//

// GENERATED_CODE_PARAM --block=xpCstBindTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpCstBind_xpCstBindTop.testbench;
import xpCstBind_xpCstBindTop.base;
import xpCstBind_xpCstBindTop.external;
import xpCstBind_xpCstBindTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpCstBind_xpCstBindTop_ns;

export class xpCstBindTopTestbench: public sc_module, public blockBase, public xpCstBindTopChannels {

public:

    std::shared_ptr<xpCstBindTopBase> xpCstBindTop;
    xpCstBindTopExternal external;

    xpCstBindTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstBindTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpCstBindTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpCstBindTopTestbench_variants() {
    instanceFactory::registerBlock("xpCstBindTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstBindTopTestbench>(blockName, variant, bbMode)); }, "", "xpCstBind");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCstBindTopTestbench_registered = (register_xpCstBindTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpCstBindTopTestbench::xpCstBindTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpCstBindTopTestbench", name(), bbMode)
        ,xpCstBindTopChannels("Chnl", "tb")
        ,xpCstBindTop(std::dynamic_pointer_cast<xpCstBindTopBase>( instanceFactory::createInstance(name(), "xpCstBindTop", "xpCstBindTop", "", "xpCstBind")))
        ,external("external")
{
    bind(xpCstBindTop.get(), &external);
}
// GENERATED_CODE_END
