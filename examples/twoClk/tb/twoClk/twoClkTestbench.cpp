// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=testbench --section=init
import a2c.endOfTest;
#include "twoClkTestbench.h"

// === Block factory registration (twoClkTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_twoClkTestbench_variants() {
    instanceFactory::registerBlock("twoClkTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkTestbench>(blockName, variant, bbMode)); }, "", "twoClk");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkTestbench_registered = (register_twoClkTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

twoClkTestbench::twoClkTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("twoClkTestbench", name(), bbMode)
        ,twoClkChannels("Chnl", "tb")
        ,twoClk(std::dynamic_pointer_cast<twoClkBase>( instanceFactory::createInstance(name(), "twoClk", "twoClk", "", "twoClk")))
        ,external("external")
{
    bind(twoClk.get(), &external);
}
// GENERATED_CODE_END
