//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain --variant=v8 --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module uvmReuse_uvmReuseChain.testbench;
import uvmReuse_uvmReuseChain.base;
import uvmReuse_uvmReuseChain.external;
import uvmReuse.uvmReuseChain.config;
import uvmReuseLeaf;
import uvmReuse;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace uvmReuseLeaf_ns;
using namespace uvmReuse_ns;

export class uvmReuseChainTestbench: public sc_module, public blockBase, public uvmReuseChainChannels<uvmReuse_uvmReuseChainV8Config> {

public:

    std::shared_ptr<uvmReuseChainBase<uvmReuse_uvmReuseChainV8Config>> uvmReuseChain;
    uvmReuseChainExternal external;

    uvmReuseChainTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseChainTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (uvmReuseChainTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_uvmReuseChainTestbench_variants() {
    instanceFactory::registerBlock("uvmReuseChainTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseChainTestbench>(blockName, variant, bbMode)); }, "", "uvmReuse");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseChainTestbench_registered = (register_uvmReuseChainTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

uvmReuseChainTestbench::uvmReuseChainTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("uvmReuseChainTestbench", name(), bbMode)
        ,uvmReuseChainChannels<uvmReuse_uvmReuseChainV8Config>("Chnl", "tb")
        ,uvmReuseChain(std::dynamic_pointer_cast<uvmReuseChainBase<uvmReuse_uvmReuseChainV8Config>>( instanceFactory::createInstance(name(), "uvmReuseChain", "uvmReuseChain", "v8", "uvmReuse")))
        ,external("external")
{
    bind(uvmReuseChain.get(), &external);
}
// GENERATED_CODE_END
