//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeafCpu --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmReuseLeaf_uvmReuseLeafCpu.block;
import uvmReuseLeaf_uvmReuseLeafCpu.base;
import uvmReuseLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuseLeaf_ns;
export SC_MODULE(uvmReuseLeafCpu), public blockBase, public uvmReuseLeafCpuBase
{
private:

public:

    uvmReuseLeafCpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseLeafCpu() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmReuseLeafCpu);

// === Block factory registration (uvmReuseLeafCpu) ===
void register_uvmReuseLeafCpu_variants() {
    instanceFactory::registerBlock("uvmReuseLeafCpu_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeafCpu>(blockName, variant, bbMode)); }, "", "uvmReuseLeaf");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseLeafCpu_registered = (register_uvmReuseLeafCpu_variants(), 0);
} // namespace
// === End block factory registration ===

uvmReuseLeafCpu::uvmReuseLeafCpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseLeafCpu", name(), bbMode)
        ,uvmReuseLeafCpuBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
