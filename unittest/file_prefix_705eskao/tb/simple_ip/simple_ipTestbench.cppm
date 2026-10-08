//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple_ip --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module simple_ip.testbench;
import simple_ip.base;
import simple_ip.external;
import common_shared_types;
import simple_ip;
import ip;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace common_shared_types_ns;
using namespace simple_ip_ns;
using namespace ip_ns;

export class simple_ipTestbench: public sc_module, public blockBase, public simple_ipChannels {

public:

    std::shared_ptr<simple_ipBase> simple_ip;
    simple_ipExternal external;

    simple_ipTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simple_ipTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (simple_ipTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_simple_ipTestbench_variants() {
    instanceFactory::registerBlock("simple_ipTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<simple_ipTestbench>(blockName, variant, bbMode)); }, "", "simple_ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _simple_ipTestbench_registered = (register_simple_ipTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

simple_ipTestbench::simple_ipTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("simple_ipTestbench", name(), bbMode)
        ,simple_ipChannels("Chnl", "tb")
        ,simple_ip(std::dynamic_pointer_cast<simple_ipBase>( instanceFactory::createInstance(name(), "simple_ip", "simple_ip", "", "simple_ip")))
        ,external("external")
{
    bind(simple_ip.get(), &external);
}
// GENERATED_CODE_END
