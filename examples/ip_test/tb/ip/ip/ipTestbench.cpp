// GENERATED_CODE_PARAM --block=ip --variant=variant0
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "ipTestbench.h"

// === Block factory registration (ipTestbench) ===
// Force-link function. Declaration in ipTestbench.h.
// Referencing this symbol pulls the registration TU into static links.
void force_link_ipTestbench() {}

void register_ipTestbench_variants() {
    instanceFactory::registerBlock("ipTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _ipTestbench_registered = (register_ipTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

ipTestbench::ipTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("ipTestbench", name(), bbMode)
        ,ipChannels<ipVariant0Config>("Chnl", "tb")
        ,ip(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>( instanceFactory::createInstance(name(), "ip", "ip", "variant0")))
        ,external("external")
{
    bind(ip.get(), &external);
}
// GENERATED_CODE_END
