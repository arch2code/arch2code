//

// GENERATED_CODE_PARAM --block=xpUniqTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xpFilterUniqVariantConfig.h"
#include "xpGainUniqVariantConfig.h"
#include "xpSinkUniqVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpUniq_xpUniqTop.testbench;
import xpUniq_xpUniqTop.base;
import xpUniq_xpUniqTop.external;
import xpUniq_xpUniqTop;
import xpGain_xpGainUniq;
import xpFilter_xpFilterUniq;
import xpSink_xpSinkUniq;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpUniq_xpUniqTop_ns;
using namespace xpGain_xpGainUniq_ns;
using namespace xpFilter_xpFilterUniq_ns;
using namespace xpSink_xpSinkUniq_ns;

export class xpUniqTopTestbench: public sc_module, public blockBase, public xpUniqTopChannels {

public:

    std::shared_ptr<xpUniqTopBase> xpUniqTop;
    xpUniqTopExternal external;

    xpUniqTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpUniqTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpUniqTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpUniqTopTestbench_variants() {
    instanceFactory::registerBlock("xpUniqTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpUniqTopTestbench>(blockName, variant, bbMode)); }, "", "xpUniq");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpUniqTopTestbench_registered = (register_xpUniqTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpUniqTopTestbench::xpUniqTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpUniqTopTestbench", name(), bbMode)
        ,xpUniqTopChannels("Chnl", "tb")
        ,xpUniqTop(std::dynamic_pointer_cast<xpUniqTopBase>( instanceFactory::createInstance(name(), "xpUniqTop", "xpUniqTop", "", "xpUniq")))
        ,external("external")
{
    bind(xpUniqTop.get(), &external);
}
// GENERATED_CODE_END
