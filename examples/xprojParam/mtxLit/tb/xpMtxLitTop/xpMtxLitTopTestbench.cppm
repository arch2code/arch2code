//

// GENERATED_CODE_PARAM --block=xpMtxLitTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpMtxLit_xpMtxLitTop.testbench;
import xpMtxLit_xpMtxLitTop.base;
import xpMtxLit_xpMtxLitTop.external;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header


export class xpMtxLitTopTestbench: public sc_module, public blockBase, public xpMtxLitTopChannels {

public:

    std::shared_ptr<xpMtxLitTopBase> xpMtxLitTop;
    xpMtxLitTopExternal external;

    xpMtxLitTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxLitTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpMtxLitTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpMtxLitTopTestbench_variants() {
    instanceFactory::registerBlock("xpMtxLitTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxLitTopTestbench>(blockName, variant, bbMode)); }, "", "xpMtxLit");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxLitTopTestbench_registered = (register_xpMtxLitTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxLitTopTestbench::xpMtxLitTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpMtxLitTopTestbench", name(), bbMode)
        ,xpMtxLitTopChannels("Chnl", "tb")
        ,xpMtxLitTop(std::dynamic_pointer_cast<xpMtxLitTopBase>( instanceFactory::createInstance(name(), "xpMtxLitTop", "xpMtxLitTop", "", "xpMtxLit")))
        ,external("external")
{
    bind(xpMtxLitTop.get(), &external);
}
// GENERATED_CODE_END
