import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=bridgeStdTop
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "bridgeStdTopTestbench.h"

// === Block factory registration (bridgeStdTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_bridgeStdTopTestbench_variants() {
    instanceFactory::registerBlock("bridgeStdTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeStdTopTestbench>(blockName, variant, bbMode)); }, "", "ipBridge");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _bridgeStdTopTestbench_registered = (register_bridgeStdTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

bridgeStdTopTestbench::bridgeStdTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("bridgeStdTopTestbench", name(), bbMode)
        ,bridgeStdTopChannels("Chnl", "tb")
        ,bridgeStdTop(std::dynamic_pointer_cast<bridgeStdTopBase>( instanceFactory::createInstance(name(), "bridgeStdTop", "bridgeStdTop", "", "ipBridge")))
        ,external("external")
{
    bind(bridgeStdTop.get(), &external);
}
// GENERATED_CODE_END
