import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "nestedTestbench.h"

// === Block factory registration (nestedTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_nestedTestbench_variants() {
    instanceFactory::registerBlock("nestedTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedTestbench>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nestedTestbench_registered = (register_nestedTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

nestedTestbench::nestedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("nestedTestbench", name(), bbMode)
        ,nestedChannels("Chnl", "tb")
        ,nested(std::dynamic_pointer_cast<nestedBase>( instanceFactory::createInstance(name(), "nested", "nested", "", "nested")))
        ,external("external")
{
    bind(nested.get(), &external);
}
// GENERATED_CODE_END
