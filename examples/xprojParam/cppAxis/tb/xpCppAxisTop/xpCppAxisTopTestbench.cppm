//

// GENERATED_CODE_PARAM --block=xpCppAxisTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xpCppWrapVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpCppAxis_xpCppAxisTop.testbench;
import xpCppAxis_xpCppAxisTop.base;
import xpCppAxis_xpCppAxisTop.external;
import xpCppAxis_xpCppAxisTop;
import xpCppAxis_xpCppWrap;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpCppAxis_xpCppAxisTop_ns;
using namespace xpCppAxis_xpCppWrap_ns;

export class xpCppAxisTopTestbench: public sc_module, public blockBase, public xpCppAxisTopChannels {

public:

    std::shared_ptr<xpCppAxisTopBase> xpCppAxisTop;
    xpCppAxisTopExternal external;

    xpCppAxisTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCppAxisTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpCppAxisTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpCppAxisTopTestbench_variants() {
    instanceFactory::registerBlock("xpCppAxisTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppAxisTopTestbench>(blockName, variant, bbMode)); }, "", "xpCppAxis");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpCppAxisTopTestbench_registered = (register_xpCppAxisTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpCppAxisTopTestbench::xpCppAxisTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpCppAxisTopTestbench", name(), bbMode)
        ,xpCppAxisTopChannels("Chnl", "tb")
        ,xpCppAxisTop(std::dynamic_pointer_cast<xpCppAxisTopBase>( instanceFactory::createInstance(name(), "xpCppAxisTop", "xpCppAxisTop", "", "xpCppAxis")))
        ,external("external")
{
    bind(xpCppAxisTop.get(), &external);
}
// GENERATED_CODE_END
