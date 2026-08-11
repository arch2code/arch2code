//

// GENERATED_CODE_PARAM --block=xpDeparamTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xpFilterVariantConfig.h"
#include "xpGainVariantConfig.h"
#include "xpSinkVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpDeparam_xpDeparamTop.testbench;
import xpDeparam_xpDeparamTop.base;
import xpDeparam_xpDeparamTop.external;
import xpDeparam_xpDeparamTop;
import xpGain;
import xpFilter;
import xpSink;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpDeparam_xpDeparamTop_ns;
using namespace xpGain_ns;
using namespace xpFilter_ns;
using namespace xpSink_ns;

export class xpDeparamTopTestbench: public sc_module, public blockBase, public xpDeparamTopChannels {

public:

    std::shared_ptr<xpDeparamTopBase> xpDeparamTop;
    xpDeparamTopExternal external;

    xpDeparamTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDeparamTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpDeparamTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpDeparamTopTestbench_variants() {
    instanceFactory::registerBlock("xpDeparamTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDeparamTopTestbench>(blockName, variant, bbMode)); }, "", "xpDeparam");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpDeparamTopTestbench_registered = (register_xpDeparamTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpDeparamTopTestbench::xpDeparamTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpDeparamTopTestbench", name(), bbMode)
        ,xpDeparamTopChannels("Chnl", "tb")
        ,xpDeparamTop(std::dynamic_pointer_cast<xpDeparamTopBase>( instanceFactory::createInstance(name(), "xpDeparamTop", "xpDeparamTop", "", "xpDeparam")))
        ,external("external")
{
    bind(xpDeparamTop.get(), &external);
}
// GENERATED_CODE_END
