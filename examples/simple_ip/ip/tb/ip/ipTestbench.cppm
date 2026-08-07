//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --variant=variant0 --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "ipVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module ip.testbench;
import ip.base;
import ip.external;
import ip;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace ip_ns;

export class ipTestbench: public sc_module, public blockBase, public ipChannels<ipVariant0Config> {

public:

    std::shared_ptr<ipBase<ipVariant0Config>> ip;
    ipExternal external;

    ipTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (ipTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_ipTestbench_variants() {
    instanceFactory::registerBlock("ipTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipTestbench>(blockName, variant, bbMode)); }, "", "ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ipTestbench_registered = (register_ipTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

ipTestbench::ipTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("ipTestbench", name(), bbMode)
        ,ipChannels<ipVariant0Config>("Chnl", "tb")
        ,ip(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>( instanceFactory::createInstance(name(), "ip", "ip", "variant0", "ip")))
        ,external("external")
{
    bind(ip.get(), &external);
}
// GENERATED_CODE_END
