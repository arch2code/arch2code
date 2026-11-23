//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeafSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmReuseLeaf_uvmReuseLeafSink.block;
import uvmReuseLeaf_uvmReuseLeafSink.base;
import uvmReuseLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuseLeaf_ns;
export SC_MODULE(uvmReuseLeafSink), public blockBase, public uvmReuseLeafSinkBase
{
private:

public:

    uvmReuseLeafSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseLeafSink() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmReuseLeafSink);

// === Block factory registration (uvmReuseLeafSink) ===
void register_uvmReuseLeafSink_variants() {
    instanceFactory::registerBlock("uvmReuseLeafSink_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeafSink>(blockName, variant, bbMode)); }, "", "uvmReuseLeaf");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseLeafSink_registered = (register_uvmReuseLeafSink_variants(), 0);
} // namespace
// === End block factory registration ===

uvmReuseLeafSink::uvmReuseLeafSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseLeafSink", name(), bbMode)
        ,uvmReuseLeafSinkBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
