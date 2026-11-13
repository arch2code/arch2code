//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsRouter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "apbBusDecode.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmRegs_uvmRegsRouter.block;
import uvmRegs_uvmRegsRouter.base;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export SC_MODULE(uvmRegsRouter), public blockBase, public uvmRegsRouterBase
{
private:
    void routerDecode(void);
    abpBusDecode< uvmRegsAddrSt, uvmRegsDataSt > decoder;

public:

    uvmRegsRouter(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsRouter() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmRegsRouter);

// === Block factory registration (uvmRegsRouter) ===
void register_uvmRegsRouter_variants() {
    instanceFactory::registerBlock("uvmRegsRouter_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsRouter>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegsRouter_registered = (register_uvmRegsRouter_variants(), 0);
} // namespace
// === End block factory registration ===

void uvmRegsRouter::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

uvmRegsRouter::uvmRegsRouter(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsRouter", name(), bbMode)
        ,uvmRegsRouterBase(name(), variant)
        ,decoder(8, 12, apbReg, {
            &apbReg_uScale0,
            &apbReg_uScale1,
            &apbReg_uScale1,
            &apbReg_uStat,
            &apbReg_uBridge,
            &apbReg_uWrap})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
