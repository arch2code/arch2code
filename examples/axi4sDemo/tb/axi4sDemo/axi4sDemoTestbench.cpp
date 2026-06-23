// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "axi4sDemoTestbench.h"

// === Block factory registration (axi4sDemoTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_axi4sDemoTestbench_variants() {
    instanceFactory::registerBlock("axi4sDemoTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axi4sDemoTestbench>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axi4sDemoTestbench_registered = (register_axi4sDemoTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

axi4sDemoTestbench::axi4sDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("axi4sDemoTestbench", name(), bbMode)
        ,axi4sDemoChannels("Chnl", "tb")
        ,axi4sDemo(std::dynamic_pointer_cast<axi4sDemoBase>( instanceFactory::createInstance(name(), "axi4sDemo", "axi4sDemo", "")))
        ,external("external")
{
    bind(axi4sDemo.get(), &external);
}
// GENERATED_CODE_END
