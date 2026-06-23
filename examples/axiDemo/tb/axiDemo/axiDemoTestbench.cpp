// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "axiDemoTestbench.h"

// === Block factory registration (axiDemoTestbench) ===
// Force-link function. Declaration in axiDemoTestbench.h.
// Referencing this symbol pulls the registration TU into static links.
void force_link_axiDemoTestbench() {}

void register_axiDemoTestbench_variants() {
    instanceFactory::registerBlock("axiDemoTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiDemoTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _axiDemoTestbench_registered = (register_axiDemoTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

axiDemoTestbench::axiDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("axiDemoTestbench", name(), bbMode)
        ,axiDemoChannels("Chnl", "tb")
        ,axiDemo(std::dynamic_pointer_cast<axiDemoBase>((force_link_axiDemo(), instanceFactory::createInstance(name(), "axiDemo", "axiDemo", ""))))
        ,external("external")
{
    bind(axiDemo.get(), &external);
}
// GENERATED_CODE_END
