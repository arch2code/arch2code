// GENERATED_CODE_PARAM --block=core
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "coreTestbench.h"

// === Block factory registration (coreTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_coreTestbench_variants() {
    instanceFactory::registerBlock("coreTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<coreTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _coreTestbench_registered = (register_coreTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

coreTestbench::coreTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("coreTestbench", name(), bbMode)
        ,coreChannels("Chnl", "tb")
        ,core(std::dynamic_pointer_cast<coreBase>( instanceFactory::createInstance(name(), "core", "core", "")))
        ,external("external")
{
    bind(core.get(), &external);
}
// GENERATED_CODE_END
