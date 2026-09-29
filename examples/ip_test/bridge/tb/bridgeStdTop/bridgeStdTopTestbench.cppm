//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module ipBridge_bridgeStdTop.testbench;
import ipBridge_bridgeStdTop.base;
import ipBridge_bridgeStdTop.external;
import ipBridge;
import common_shared_types;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace ipBridge_ns;
using namespace common_shared_types_ns;

export class bridgeStdTopTestbench: public sc_module, public blockBase, public bridgeStdTopChannels {

public:

    std::shared_ptr<bridgeStdTopBase> bridgeStdTop;
    bridgeStdTopExternal external;

    bridgeStdTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bridgeStdTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (bridgeStdTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_bridgeStdTopTestbench_variants() {
    instanceFactory::registerBlock("bridgeStdTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeStdTopTestbench>(blockName, variant, bbMode)); }, "", "ipBridge");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _bridgeStdTopTestbench_registered = (register_bridgeStdTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

bridgeStdTopTestbench::bridgeStdTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("bridgeStdTopTestbench", name(), bbMode)
        ,bridgeStdTopChannels("Chnl", "tb")
        ,bridgeStdTop(std::dynamic_pointer_cast<bridgeStdTopBase>( instanceFactory::createInstance(name(), "bridgeStdTop", "bridgeStdTop", "", "ipBridge")))
        ,external("external")
{
    bind(bridgeStdTop.get(), &external);
}
// GENERATED_CODE_END
