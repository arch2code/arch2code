//

// GENERATED_CODE_PARAM --block=pySocket --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module pySocket.testbench;
import pySocket.base;
import pySocket.external;
import pySocket_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace pySocket_tb_ns;

export class pySocketTestbench: public sc_module, public blockBase, public pySocketChannels {

public:

    std::shared_ptr<pySocketBase> pySocket;
    pySocketExternal external;

    pySocketTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocketTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
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
