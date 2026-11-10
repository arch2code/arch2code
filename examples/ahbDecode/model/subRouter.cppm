//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subRouter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "ahb_channel.h"
#include "regBusDecode.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module ahbDecode_subRouter.block;
import ahbDecode_subRouter.base;
import ahbDecode;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ahbDecode_ns;
export SC_MODULE(subRouter), public blockBase, public subRouterBase
{
private:
    void routerDecode(void);
    regBusDecode< ahbAddrSt, ahbDataSt, ahb_in_if, ahb_out_if > decoder;

public:

    subRouter(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subRouter() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(subRouter);

// === Block factory registration (subRouter) ===
void register_subRouter_variants() {
    instanceFactory::registerBlock("subRouter_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<subRouter>(blockName, variant, bbMode)); }, "", "ahbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _subRouter_registered = (register_subRouter_variants(), 0);
} // namespace
// === End block factory registration ===

void subRouter::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread(true);
}

subRouter::subRouter(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subRouter", name(), bbMode)
        ,subRouterBase(name(), variant)
        ,decoder(4, 8, ahbReg, {
            &ahbReg_uLeafC})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
