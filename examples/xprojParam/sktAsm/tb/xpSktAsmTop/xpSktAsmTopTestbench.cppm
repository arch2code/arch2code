//

// GENERATED_CODE_PARAM --block=xpSktAsmTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpSktAsm_xpSktAsmTop.testbench;
import xpSktAsm_xpSktAsmTop.base;
import xpSktAsm_xpSktAsmTop.external;
import xpSktIp;
import xpSktAsm_xpSktAsmTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpSktIp_ns;
using namespace xpSktAsm_xpSktAsmTop_ns;

export class xpSktAsmTopTestbench: public sc_module, public blockBase, public xpSktAsmTopChannels {

public:

    std::shared_ptr<xpSktAsmTopBase> xpSktAsmTop;
    xpSktAsmTopExternal external;

    xpSktAsmTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpSktAsmTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpSktAsmTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpSktAsmTopTestbench_variants() {
    instanceFactory::registerBlock("xpSktAsmTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSktAsmTopTestbench>(blockName, variant, bbMode)); }, "", "xpSktAsm");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpSktAsmTopTestbench_registered = (register_xpSktAsmTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpSktAsmTopTestbench::xpSktAsmTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpSktAsmTopTestbench", name(), bbMode)
        ,xpSktAsmTopChannels("Chnl", "tb")
        ,xpSktAsmTop(std::dynamic_pointer_cast<xpSktAsmTopBase>( instanceFactory::createInstance(name(), "xpSktAsmTop", "xpSktAsmTop", "", "xpSktAsm")))
        ,external("external")
{
    bind(xpSktAsmTop.get(), &external);
}
// GENERATED_CODE_END
