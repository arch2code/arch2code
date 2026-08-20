//

// GENERATED_CODE_PARAM --block=xpDpMidStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xpDpLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpDpMid_xpDpMidStdTop.testbench;
import xpDpMid_xpDpMidStdTop.base;
import xpDpMid_xpDpMidStdTop.external;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header


export class xpDpMidStdTopTestbench: public sc_module, public blockBase, public xpDpMidStdTopChannels {

public:

    std::shared_ptr<xpDpMidStdTopBase> xpDpMidStdTop;
    xpDpMidStdTopExternal external;

    xpDpMidStdTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpMidStdTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpDpMidStdTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpDpMidStdTopTestbench_variants() {
    instanceFactory::registerBlock("xpDpMidStdTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMidStdTopTestbench>(blockName, variant, bbMode)); }, "", "xpDpMid");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpDpMidStdTopTestbench_registered = (register_xpDpMidStdTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpDpMidStdTopTestbench::xpDpMidStdTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpDpMidStdTopTestbench", name(), bbMode)
        ,xpDpMidStdTopChannels("Chnl", "tb")
        ,xpDpMidStdTop(std::dynamic_pointer_cast<xpDpMidStdTopBase>( instanceFactory::createInstance(name(), "xpDpMidStdTop", "xpDpMidStdTop", "", "xpDpMid")))
        ,external("external")
{
    bind(xpDpMidStdTop.get(), &external);
}
// GENERATED_CODE_END
