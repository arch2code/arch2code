//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeafRouter --mode=module
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
export module uvmReuseLeaf_uvmReuseLeafRouter.block;
import uvmReuseLeaf_uvmReuseLeafRouter.base;
import uvmReuseLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuseLeaf_ns;
export SC_MODULE(uvmReuseLeafRouter), public blockBase, public uvmReuseLeafRouterBase
{
private:
    void routerDecode(void);
    abpBusDecode< uvmReuseAddrSt, uvmReuseDataSt > decoder;

public:

    uvmReuseLeafRouter(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseLeafRouter() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmReuseLeafRouter);

// === Block factory registration (uvmReuseLeafRouter) ===
void register_uvmReuseLeafRouter_variants() {
    instanceFactory::registerBlock("uvmReuseLeafRouter_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeafRouter>(blockName, variant, bbMode)); }, "", "uvmReuseLeaf");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseLeafRouter_registered = (register_uvmReuseLeafRouter_variants(), 0);
} // namespace
// === End block factory registration ===

void uvmReuseLeafRouter::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

uvmReuseLeafRouter::uvmReuseLeafRouter(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseLeafRouter", name(), bbMode)
        ,uvmReuseLeafRouterBase(name(), variant)
        ,decoder(2, 12, apbReg, {
            &apbReg_u_uvmReuseLeaf})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
