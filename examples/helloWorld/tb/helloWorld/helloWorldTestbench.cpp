import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "helloWorldTestbench.h"

// === Block factory registration (helloWorldTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_helloWorldTestbench_variants() {
    instanceFactory::registerBlock("helloWorldTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<helloWorldTestbench>(blockName, variant, bbMode)); }, "", "helloWorld");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _helloWorldTestbench_registered = (register_helloWorldTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

helloWorldTestbench::helloWorldTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("helloWorldTestbench", name(), bbMode)
        ,helloWorldChannels("Chnl", "tb")
        ,helloWorld(std::dynamic_pointer_cast<helloWorldBase>( instanceFactory::createInstance(name(), "helloWorld", "helloWorld", "", "helloWorld")))
        ,external("external")
{
    bind(helloWorld.get(), &external);
}
// GENERATED_CODE_END
