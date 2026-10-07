//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkTable --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
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
    hwMemory< twoClkLutSt > lut;
    hwMemory< twoClkStatsSt > stats;

    twoClkTable(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkTable() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        twoClkTableBase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members

private:
    void sweep(void);
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
    registerHandler< twoClkRegAddrSt, twoClkRegDataSt >(_a2cRegs, twoClkReg, (1<<(7))-1); }

twoClkTable::twoClkTable(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClkTable", name(), bbMode)
        ,twoClkTableBase(name(), variant)
        ,_a2cRegs(log_)
        ,tbl(name(), "tbl", mems, TWO_CLK_TBL_WORDS)
        ,lut(name(), "lut", mems, TWO_CLK_LUT_WORDS, HWMEMORYTYPE_NORMAL, HWMEMORYFWACCESS_WO)
        ,stats(name(), "stats", mems, TWO_CLK_LUT_WORDS, HWMEMORYTYPE_NORMAL, HWMEMORYFWACCESS_RO)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_TWOCLKTABLE_TBL = 0x0;
    constexpr uint64_t REG_ADDR_TWOCLKTABLE_LUT = 0x40;
    constexpr uint64_t REG_ADDR_TWOCLKTABLE_STATS = 0x50;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_TWOCLKTABLE_TBL, twoClkTblSt::_byteWidth, TWO_CLK_TBL_WORDS, std::string(this->name()) + ".tbl", &tbl);
    _a2cRegs.addMemory( REG_ADDR_TWOCLKTABLE_LUT, twoClkLutSt::_byteWidth, TWO_CLK_LUT_WORDS, std::string(this->name()) + ".lut", &lut);
    _a2cRegs.addMemory( REG_ADDR_TWOCLKTABLE_STATS, twoClkStatsSt::_byteWidth, TWO_CLK_LUT_WORDS, std::string(this->name()) + ".stats", &stats);
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    // tbl is reached only by firmware, through the generated handler above.
    SC_THREAD(sweep);
};

// One row per clkSlow period, as the RTL sweep does: stats[i] = lut[i] + 1,
// wrapping at the field width.
void twoClkTable::sweep(void)
{
    for (uint64_t i = 0; ; i = (i + 1) % TWO_CLK_LUT_WORDS) {
        wait(TWO_CLK_SLOW_PERIOD_NS, SC_NS);
        twoClkStatsSt s;
        s.val = (twoClkLutValT)(lut.read(i).val + 1);
        stats.write(i, s);
    }
}

