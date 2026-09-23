//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
#include "apbBusDecode.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module twoClk_twoClkDecode.block;
import twoClk_twoClkDecode.base;
import twoClk;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace twoClk_ns;
export SC_MODULE(twoClkDecode), public blockBase, public twoClkDecodeBase
{
private:
    void routerDecode(void);
    abpBusDecode< twoClkRegAddrSt, twoClkRegDataSt > decoder;

public:

    twoClkDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkDecode() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(twoClkDecode);

// === Block factory registration (twoClkDecode) ===
void register_twoClkDecode_variants() {
    instanceFactory::registerBlock("twoClkDecode_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkDecode>(blockName, variant, bbMode)); }, "", "twoClk");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkDecode_registered = (register_twoClkDecode_variants(), 0);
} // namespace
// === End block factory registration ===

void twoClkDecode::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

twoClkDecode::twoClkDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClkDecode", name(), bbMode)
        ,twoClkDecodeBase(name(), variant)
        ,decoder(4, 16, twoClkReg, {
            &twoClkReg_uTable})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

