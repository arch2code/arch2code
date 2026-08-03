import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=dut --variant=dutV0
// GENERATED_CODE_BEGIN --template=testbench --section=init
import a2c.endOfTest;
#include "dutTestbench.h"

// === Block factory registration (dutTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_dutTestbench_variants() {
    instanceFactory::registerBlock("dutTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dutTestbench>(blockName, variant, bbMode)); }, "", "xif");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _dutTestbench_registered = (register_dutTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

dutTestbench::dutTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("dutTestbench", name(), bbMode)
        ,dutChannels<dutDutV0Config>("Chnl", "tb")
        ,dut(std::dynamic_pointer_cast<dutBase<dutDutV0Config>>( instanceFactory::createInstance(name(), "dut", "dut", "dutV0", "xif")))
        ,external("external")
{
    bind(dut.get(), &external);
}
// GENERATED_CODE_END
