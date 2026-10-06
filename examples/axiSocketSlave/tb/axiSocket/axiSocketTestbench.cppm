//

// GENERATED_CODE_PARAM --block=axiSocket --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module axiSocketSlave_axiSocket.testbench;
import axiSocketSlave_axiSocket.base;
import axiSocketSlave_axiSocket.external;
import axiSocketSlave_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace axiSocketSlave_tb_ns;

export class axiSocketTestbench: public sc_module, public blockBase, public axiSocketChannels {

public:

    std::shared_ptr<axiSocketBase> axiSocket;
    axiSocketExternal external;

    axiSocketTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
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
