// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "someRapperTestbench.h"

// === Block factory registration (someRapperTestbench) ===
// Force-link function. Declaration in someRapperTestbench.h.
// Referencing this symbol pulls the registration TU into static links.
void force_link_someRapperTestbench() {}

void register_someRapperTestbench_variants() {
    instanceFactory::registerBlock("someRapperTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<someRapperTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _someRapperTestbench_registered = (register_someRapperTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

someRapperTestbench::someRapperTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("someRapperTestbench", name(), bbMode)
        ,someRapperChannels("Chnl", "tb")
        ,someRapper(std::dynamic_pointer_cast<someRapperBase>((force_link_someRapper(), instanceFactory::createInstance(name(), "someRapper", "someRapper", ""))))
        ,external("external")
{
    bind(someRapper.get(), &external);
}
// GENERATED_CODE_END
