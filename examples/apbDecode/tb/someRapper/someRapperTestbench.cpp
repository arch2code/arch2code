import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "someRapperTestbench.h"

// === Block factory registration (someRapperTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_someRapperTestbench_variants() {
    instanceFactory::registerBlock("someRapperTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<someRapperTestbench>(blockName, variant, bbMode)); }, "", "apbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _someRapperTestbench_registered = (register_someRapperTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

someRapperTestbench::someRapperTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("someRapperTestbench", name(), bbMode)
        ,someRapperChannels("Chnl", "tb")
        ,someRapper(std::dynamic_pointer_cast<someRapperBase>( instanceFactory::createInstance(name(), "someRapper", "someRapper", "", "apbDecode")))
        ,external("external")
{
    bind(someRapper.get(), &external);
}
// GENERATED_CODE_END
