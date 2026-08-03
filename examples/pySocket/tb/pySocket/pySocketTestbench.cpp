import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "pySocketTestbench.h"

// === Block factory registration (pySocketTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_pySocketTestbench_variants() {
    instanceFactory::registerBlock("pySocketTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocketTestbench>(blockName, variant, bbMode)); }, "", "pySocket");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _pySocketTestbench_registered = (register_pySocketTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

pySocketTestbench::pySocketTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("pySocketTestbench", name(), bbMode)
        ,pySocketChannels("Chnl", "tb")
        ,pySocket(std::dynamic_pointer_cast<pySocketBase>( instanceFactory::createInstance(name(), "pySocket", "pySocket", "", "pySocket")))
        ,external("external")
{
    bind(pySocket.get(), &external);
}
// GENERATED_CODE_END
