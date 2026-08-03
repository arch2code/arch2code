import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "simple_ipTestbench.h"

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
