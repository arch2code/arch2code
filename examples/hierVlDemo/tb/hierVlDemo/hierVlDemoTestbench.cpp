import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=hierVlDemo
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "hierVlDemoTestbench.h"

// === Block factory registration (hierVlDemoTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_hierVlDemoTestbench_variants() {
    instanceFactory::registerBlock("hierVlDemoTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<hierVlDemoTestbench>(blockName, variant, bbMode)); }, "", "hierVlDemo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _hierVlDemoTestbench_registered = (register_hierVlDemoTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

hierVlDemoTestbench::hierVlDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("hierVlDemoTestbench", name(), bbMode)
        ,hierVlDemoChannels("Chnl", "tb")
        ,hierVlDemo(std::dynamic_pointer_cast<hierVlDemoBase>( instanceFactory::createInstance(name(), "hierVlDemo", "hierVlDemo", "", "hierVlDemo")))
        ,external("external")
{
    bind(hierVlDemo.get(), &external);
}
// GENERATED_CODE_END
