//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ahbRouter --mode=module
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
export module ahbDecode_ahbRouter.block;
import ahbDecode_ahbRouter.base;
import ahbDecode;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ahbDecode_ns;
export SC_MODULE(ahbRouter), public blockBase, public ahbRouterBase
{
private:
    void routerDecode(void);
    regBusDecode< ahbAddrSt, ahbDataSt, ahb_in_if, ahb_out_if > decoder;

public:

    ahbRouter(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ahbRouter() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(ahbRouter);

// === Block factory registration (ahbRouter) ===
void register_ahbRouter_variants() {
    instanceFactory::registerBlock("ahbRouter_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ahbRouter>(blockName, variant, bbMode)); }, "", "ahbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ahbRouter_registered = (register_ahbRouter_variants(), 0);
} // namespace
// === End block factory registration ===

void ahbRouter::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread(true);
}

ahbRouter::ahbRouter(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ahbRouter", name(), bbMode)
        ,ahbRouterBase(name(), variant)
        ,decoder(4, 12, ahbReg, {
            &ahbReg_uLeafA,
            &ahbReg_uLeafB,
            &ahbReg_uSubSys})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
