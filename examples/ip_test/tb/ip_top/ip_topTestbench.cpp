// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "ip_topTestbench.h"

// === Block factory registration (ip_topTestbench) ===
// Force-link function. Declaration in ip_topTestbench.h.
// See plan-block-registration.md "Force-Link Function".
void force_link_ip_topTestbench() {}

void register_ip_topTestbench_variants() {
    instanceFactory::registerBlock("ip_topTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_topTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _ip_topTestbench_registered = (register_ip_topTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

ip_topTestbench::ip_topTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("ip_topTestbench", name(), bbMode)
        ,ip_topChannels("Chnl", "tb")
        ,ip_top(std::dynamic_pointer_cast<ip_topBase>((force_link_ip_top(), instanceFactory::createInstance(name(), "ip_top", "ip_top", ""))))
        ,external("external")
{
    bind(ip_top.get(), &external);
}
// GENERATED_CODE_END
