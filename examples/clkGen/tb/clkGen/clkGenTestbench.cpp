// GENERATED_CODE_PARAM --block=clkGen
// GENERATED_CODE_BEGIN --template=testbench --section=init
import a2c.endOfTest;
#include "clkGenTestbench.h"

// === Block factory registration (clkGenTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_clkGenTestbench_variants() {
    instanceFactory::registerBlock("clkGenTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkGenTestbench>(blockName, variant, bbMode)); }, "", "clkGen");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _clkGenTestbench_registered = (register_clkGenTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

clkGenTestbench::clkGenTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("clkGenTestbench", name(), bbMode)
        ,clkGenChannels("Chnl", "tb")
        ,clkGen(std::dynamic_pointer_cast<clkGenBase>( instanceFactory::createInstance(name(), "clkGen", "clkGen", "", "clkGen")))
        ,external("external")
{
    bind(clkGen.get(), &external);
}
// GENERATED_CODE_END
