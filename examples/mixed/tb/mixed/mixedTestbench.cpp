// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "mixedTestbench.h"

// === Block factory registration (mixedTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_mixedTestbench_variants() {
    instanceFactory::registerBlock("mixedTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<mixedTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _mixedTestbench_registered = (register_mixedTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

mixedTestbench::mixedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("mixedTestbench", name(), bbMode)
        ,mixedChannels("Chnl", "tb")
        ,mixed(std::dynamic_pointer_cast<mixedBase>( instanceFactory::createInstance(name(), "mixed", "mixed", "")))
        ,external("external")
{
    bind(mixed.get(), &external);
}
// GENERATED_CODE_END
