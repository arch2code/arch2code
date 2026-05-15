// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "mixedTestbench.h"

// === Block factory registration (mixedTestbench) ===
// Force-link function. Declaration in mixedTestbench.h.
// Referencing this symbol pulls the registration TU into static links.
void force_link_mixedTestbench() {}

void register_mixedTestbench_variants() {
    instanceFactory::registerBlock("mixedTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<mixedTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _mixedTestbench_registered = (register_mixedTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

mixedTestbench::mixedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("mixedTestbench", name(), bbMode)
        ,mixedChannels("Chnl", "tb")
        ,mixed(std::dynamic_pointer_cast<mixedBase>((force_link_mixed(), instanceFactory::createInstance(name(), "mixed", "mixed", ""))))
        ,external("external")
{
    bind(mixed.get(), &external);
}
// GENERATED_CODE_END
