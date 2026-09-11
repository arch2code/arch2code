//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtInhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpRtInh_xpRtInhTop.testbench;
import xpRtInh_xpRtInhTop.base;
import xpRtInh_xpRtInhTop.external;
import common_shared_types;
import xpRtInh;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace common_shared_types_ns;
using namespace xpRtInh_ns;

export class xpRtInhTopTestbench: public sc_module, public blockBase, public xpRtInhTopChannels {

public:

    std::shared_ptr<xpRtInhTopBase> xpRtInhTop;
    xpRtInhTopExternal external;

    xpRtInhTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpRtInhTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpRtInhTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpRtInhTopTestbench_variants() {
    instanceFactory::registerBlock("xpRtInhTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtInhTopTestbench>(blockName, variant, bbMode)); }, "", "xpRtInh");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpRtInhTopTestbench_registered = (register_xpRtInhTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpRtInhTopTestbench::xpRtInhTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpRtInhTopTestbench", name(), bbMode)
        ,xpRtInhTopChannels("Chnl", "tb")
        ,xpRtInhTop(std::dynamic_pointer_cast<xpRtInhTopBase>( instanceFactory::createInstance(name(), "xpRtInhTop", "xpRtInhTop", "", "xpRtInh")))
        ,external("external")
{
    bind(xpRtInhTop.get(), &external);
}
// GENERATED_CODE_END
