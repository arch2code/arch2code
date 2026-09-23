//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkTable --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
#include "addressMap.h"
#include "hwMemory.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module twoClk_twoClkTable.block;
import twoClk_twoClkTable.base;
import twoClk;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace twoClk_ns;
export SC_MODULE(twoClkTable), public blockBase, public twoClkTableBase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    memories mems;
    //memories
    hwMemory< twoClkTblSt > tbl;

    twoClkTable(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkTable() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        twoClkTableBase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(twoClkTable);

// === Block factory registration (twoClkTable) ===
void register_twoClkTable_variants() {
    instanceFactory::registerBlock("twoClkTable_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkTable>(blockName, variant, bbMode)); }, "", "twoClk");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkTable_registered = (register_twoClkTable_variants(), 0);
} // namespace
// === End block factory registration ===

void twoClkTable::regHandler(void) { //handle register decode
    registerHandler< twoClkRegAddrSt, twoClkRegDataSt >(_a2cRegs, twoClkReg, (1<<(6))-1); }

twoClkTable::twoClkTable(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClkTable", name(), bbMode)
        ,twoClkTableBase(name(), variant)
        ,_a2cRegs(log_)
        ,tbl(name(), "tbl", mems, TWO_CLK_TBL_WORDS)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_TWOCLKTABLE_TBL = 0x0;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_TWOCLKTABLE_TBL, twoClkTblSt::_byteWidth, TWO_CLK_TBL_WORDS, std::string(this->name()) + ".tbl", &tbl);
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    // tbl is entirely firmware-accessed through the generated handler above; no user logic.
};

