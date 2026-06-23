// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "axiDemoTestbench.h"

// === Block factory registration (axiDemoTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_axiDemoTestbench_variants() {
    instanceFactory::registerBlock("axiDemoTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiDemoTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axiDemoTestbench_registered = (register_axiDemoTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

axiDemoTestbench::axiDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("axiDemoTestbench", name(), bbMode)
        ,axiDemoChannels("Chnl", "tb")
        ,axiDemo(std::dynamic_pointer_cast<axiDemoBase>( instanceFactory::createInstance(name(), "axiDemo", "axiDemo", "")))
        ,external("external")
{
    bind(axiDemo.get(), &external);
}
// GENERATED_CODE_END
