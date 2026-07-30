//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockB --mode=module
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
#include "hwRegister.h"
#include "hwMemory.h"
// GENERATED_CODE_END
#include "regAddresses.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module apbDecode_blockB.block;
import apbDecode_blockB.base;
import apbDecode;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace apbDecode_ns;

export SC_MODULE(blockB), public blockBase, public blockBBase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< un0BRegSt, 4 > rwUn0B; // A unaligned four bytes Read Write register
    hwRegister< aSizeRegSt, 4 > roB; // A Read Only register

    memories mems;
    //memories
    hwMemory< bMemSt > blockBTable;

    blockB(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockB() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockBBase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(blockB);

// === Block factory registration (blockB) ===
void register_blockB_variants() {
    instanceFactory::registerBlock("blockB_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockB>(blockName, variant, bbMode)); }, "", "apbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _blockB_registered = (register_blockB_variants(), 0);
} // namespace
// === End block factory registration ===

void blockB::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(_a2cRegs, apbReg, (1<<(10))-1); }

blockB::blockB(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockB", name(), bbMode)
        ,blockBBase(name(), variant)
        ,_a2cRegs(log_)
        ,rwUn0B(un0BRegSt::_packedSt(0x0))
        ,roB()
        ,blockBTable(name(), "blockBTable", mems, MEMORYB_WORDS)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_BLOCKB_BLOCKBTABLE = 0x0;
    constexpr uint64_t REG_ADDR_BLOCKB_RWUN0B = 0x200;
    constexpr uint64_t REG_ADDR_BLOCKB_ROB = 0x208;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_BLOCKB_BLOCKBTABLE, bMemSt::_byteWidth, MEMORYB_WORDS, std::string(this->name()) + ".blockBTable", &blockBTable);
    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_BLOCKB_RWUN0B, 3, "rwUn0B", &rwUn0B );
    _a2cRegs.addRegister( REG_ADDR_BLOCKB_ROB, 4, "roB", &roB );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

