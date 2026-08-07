//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "ipVariantConfig.h"
#include "srcVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module ip_test_ip_top.testbench;
import ip_test_ip_top.base;
import ip_test_ip_top.external;
import common_shared_types;
import ip_test_ip_top;
import ip_test_src;
import ip;
import ipBridge;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace common_shared_types_ns;
using namespace ip_test_ip_top_ns;
using namespace ip_test_src_ns;
using namespace ip_ns;
using namespace ipBridge_ns;

export class ip_topTestbench: public sc_module, public blockBase, public ip_topChannels {

public:

    std::shared_ptr<ip_topBase> ip_top;
    ip_topExternal external;

    ip_topTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip_topTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (ip_topTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_ip_topTestbench_variants() {
    instanceFactory::registerBlock("ip_topTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_topTestbench>(blockName, variant, bbMode)); }, "", "ip_test");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ip_topTestbench_registered = (register_ip_topTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

ip_topTestbench::ip_topTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("ip_topTestbench", name(), bbMode)
        ,ip_topChannels("Chnl", "tb")
        ,ip_top(std::dynamic_pointer_cast<ip_topBase>( instanceFactory::createInstance(name(), "ip_top", "ip_top", "", "ip_test")))
        ,external("external")
{
    bind(ip_top.get(), &external);
}
// GENERATED_CODE_END
