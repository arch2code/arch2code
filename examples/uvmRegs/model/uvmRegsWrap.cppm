//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsWrap --mode=module
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
export module uvmRegs_uvmRegsWrap.block;
import uvmRegs_uvmRegsWrap.base;
import uvmRegs_uvmRegsInner.base;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export SC_MODULE(uvmRegsWrap), public blockBase, public uvmRegsWrapBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<uvmRegsInnerBase> uInner;

    uvmRegsWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmRegsWrap);

// === Block factory registration (uvmRegsWrap) ===
void register_uvmRegsWrap_variants() {
    instanceFactory::registerBlock("uvmRegsWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsWrap>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegsWrap_registered = (register_uvmRegsWrap_variants(), 0);
} // namespace
// === End block factory registration ===

uvmRegsWrap::uvmRegsWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsWrap", name(), bbMode)
        ,uvmRegsWrapBase(name(), variant)
        ,uInner(std::dynamic_pointer_cast<uvmRegsInnerBase>(instanceFactory::createInstance(name(), "uInner", "uvmRegsInner", "", "uvmRegs")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uInner->apbReg(apbReg);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
