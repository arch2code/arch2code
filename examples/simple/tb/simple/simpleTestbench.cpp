// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "simpleTestbench.h"

// === Block factory registration (simpleTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_simpleTestbench_variants() {
    instanceFactory::registerBlock("simpleTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<simpleTestbench>(blockName, variant, bbMode)); }, "", "simple");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _simpleTestbench_registered = (register_simpleTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

simpleTestbench::simpleTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("simpleTestbench", name(), bbMode)
        ,simpleChannels("Chnl", "tb")
        ,simple(std::dynamic_pointer_cast<simpleBase>( instanceFactory::createInstance(name(), "simple", "simple", "", "simple")))
        ,external("external")
{
    bind(simple.get(), &external);
}
// GENERATED_CODE_END
