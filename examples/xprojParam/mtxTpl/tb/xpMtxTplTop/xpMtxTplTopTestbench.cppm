//

// GENERATED_CODE_PARAM --block=xpMtxTplTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
#include "xpMtxTplTopVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module xpMtxTpl_xpMtxTplTop.testbench;
import xpMtxTpl_xpMtxTplTop.base;
import xpMtxTpl_xpMtxTplTop.external;
import xpMtxTpl_xpMtxTplTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace xpMtxTpl_xpMtxTplTop_ns;

export class xpMtxTplTopTestbench: public sc_module, public blockBase, public xpMtxTplTopChannels {

public:

    std::shared_ptr<xpMtxTplTopBase> xpMtxTplTop;
    xpMtxTplTopExternal external;

    xpMtxTplTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxTplTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (xpMtxTplTopTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_xpMtxTplTopTestbench_variants() {
    instanceFactory::registerBlock("xpMtxTplTopTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxTplTopTestbench>(blockName, variant, bbMode)); }, "", "xpMtxTpl");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxTplTopTestbench_registered = (register_xpMtxTplTopTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxTplTopTestbench::xpMtxTplTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("xpMtxTplTopTestbench", name(), bbMode)
        ,xpMtxTplTopChannels("Chnl", "tb")
        ,xpMtxTplTop(std::dynamic_pointer_cast<xpMtxTplTopBase>( instanceFactory::createInstance(name(), "xpMtxTplTop", "xpMtxTplTop", "", "xpMtxTpl")))
        ,external("external")
{
    bind(xpMtxTplTop.get(), &external);
}
// GENERATED_CODE_END
