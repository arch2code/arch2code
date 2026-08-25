// GENERATED_CODE_PARAM --block=axiSocket
// GENERATED_CODE_BEGIN --template=testbench --section=init
import a2c.endOfTest;
#include "axiSocketTestbench.h"

// === Block factory registration (axiSocketTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_axiSocketTestbench_variants() {
    instanceFactory::registerBlock("axiSocketTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiSocketTestbench>(blockName, variant, bbMode)); }, "", "axiSocketSlave");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axiSocketTestbench_registered = (register_axiSocketTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

axiSocketTestbench::axiSocketTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("axiSocketTestbench", name(), bbMode)
        ,axiSocketChannels("Chnl", "tb")
        ,axiSocket(std::dynamic_pointer_cast<axiSocketBase>( instanceFactory::createInstance(name(), "axiSocket", "axiSocket", "", "axiSocketSlave")))
        ,external("external")
{
    bind(axiSocket.get(), &external);
}
// GENERATED_CODE_END
