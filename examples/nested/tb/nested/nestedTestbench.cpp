// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "nestedTestbench.h"

// === Block factory registration (nestedTestbench) ===
// Force-link function. Declaration in nestedTestbench.h.
// Referencing this symbol pulls the registration TU into static links.
void force_link_nestedTestbench() {}

void register_nestedTestbench_variants() {
    instanceFactory::registerBlock("nestedTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _nestedTestbench_registered = (register_nestedTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

nestedTestbench::nestedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("nestedTestbench", name(), bbMode)
        ,nestedChannels("Chnl", "tb")
        ,nested(std::dynamic_pointer_cast<nestedBase>((force_link_nested(), instanceFactory::createInstance(name(), "nested", "nested", ""))))
        ,external("external")
{
    bind(nested.get(), &external);
}
// GENERATED_CODE_END
