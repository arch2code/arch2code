//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkCpu --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
// GENERATED_CODE_END
#include "regAddresses.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module twoClk_twoClkCpu.block;
import twoClk_twoClkCpu.base;
import twoClk;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace twoClk_ns;
export SC_MODULE(twoClkCpu), public blockBase, public twoClkCpuBase
{
private:

public:

    twoClkCpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkCpu() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    // This cpu has no steady traffic to tickle a watchdog with, so it is a
    // voter only: it casts its vote once its own tbl write/read/compare pass
    // has run.
    endOfTest eot_{true};

    void regAccessTest(void);
    void writeTblRow(const int rowId, twoClkTblSt &entry);
    void readTblRow(const int rowId, twoClkTblSt &entry);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(twoClkCpu);

// === Block factory registration (twoClkCpu) ===
void register_twoClkCpu_variants() {
    instanceFactory::registerBlock("twoClkCpu_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkCpu>(blockName, variant, bbMode)); }, "", "twoClk");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkCpu_registered = (register_twoClkCpu_variants(), 0);
} // namespace
// === End block factory registration ===

twoClkCpu::twoClkCpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClkCpu", name(), bbMode)
        ,twoClkCpuBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(regAccessTest);
};

typedef sc_bv<twoClkTblSt::_bitWidth> twoClkTblScT;

// One distinct row per TWO_CLK_TBL_WORDS entry: not row * constant, so a
// shifted or duplicated row shows up as a mismatch rather than another value
// the same formula would also have produced.
std::array<twoClkTblSt, TWO_CLK_TBL_WORDS> tblData_ = {{
    twoClkTblSt(twoClkTblScT(0x0a1b2c3d4e5fULL)),
    twoClkTblSt(twoClkTblScT(0x123456789abcULL)),
    twoClkTblSt(twoClkTblScT(0xdeadbeefcafeULL)),
    twoClkTblSt(twoClkTblScT(0x0f1e2d3c4b5aULL)),
    twoClkTblSt(twoClkTblScT(0x998877665544ULL)),
    twoClkTblSt(twoClkTblScT(0x001122334455ULL)),
    twoClkTblSt(twoClkTblScT(0xaabbccddeeffULL)),
    twoClkTblSt(twoClkTblScT(0x555500aa55ffULL)),
}};

void twoClkCpu::writeTblRow(const int rowId, twoClkTblSt &entry)
{
    twoClkRegAddrSt addr;
    twoClkRegDataSt data;
    twoClkTblScT packed = entry.sc_pack();

    addr.address = BASE_ADDR_UTABLE + REG_TWOCLKTABLE_TBL + rowId * 0x8 + 0x0;
    data.data = packed.range(31, 0).to_int();
    twoClkReg->request(true, addr, data);

    addr.address = BASE_ADDR_UTABLE + REG_TWOCLKTABLE_TBL + rowId * 0x8 + 0x4;
    data.data = (twoClkRegDataT) packed.range(47, 32).to_int();
    twoClkReg->request(true, addr, data);
}

void twoClkCpu::readTblRow(const int rowId, twoClkTblSt &entry)
{
    twoClkRegAddrSt addr;
    twoClkRegDataSt data;
    twoClkTblScT packed;

    addr.address = BASE_ADDR_UTABLE + REG_TWOCLKTABLE_TBL + rowId * 0x8 + 0x0;
    twoClkReg->request(false, addr, data);
    packed.range(31, 0) = data.data;

    addr.address = BASE_ADDR_UTABLE + REG_TWOCLKTABLE_TBL + rowId * 0x8 + 0x4;
    twoClkReg->request(false, addr, data);
    packed.range(47, 32) = data.data;

    entry.sc_unpack(packed);
}

// tbl's memory domain (clkSlow/rstSlow_n) leaves reset later than the
// register bus domain (clk/rst_n) that this cpu issues on. An access that
// reaches the bridge before rstSlow_n releases completes with pslverr, and
// the request() API has no error return, so that access is silently lost.
// Waiting past both resets before the first access avoids it.

void twoClkCpu::regAccessTest(void)
{
    wait(TWO_CLK_RESET_SETTLE_NS, SC_NS);

    for (unsigned int rowId = 0; rowId < TWO_CLK_TBL_WORDS; rowId++)
        writeTblRow(rowId, tblData_[rowId]);

    std::array<twoClkTblSt, TWO_CLK_TBL_WORDS> tblReadBack;
    for (unsigned int rowId = 0; rowId < TWO_CLK_TBL_WORDS; rowId++)
        readTblRow(rowId, tblReadBack[rowId]);

    if (tblReadBack == tblData_)
        log_.logPrint(std::format("{} tbl write/read sequential success", this->name()), LOG_IMPORTANT);
    else
        Q_ASSERT(false, "twoClkCpu tbl write/read sequential fail");

    eot_.setEndOfTest(true);
}

