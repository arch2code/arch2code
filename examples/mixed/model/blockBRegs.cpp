//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockBRegs.h"
SC_HAS_PROCESS(blockBRegs);

// === Block factory registration (blockBRegs) ===
void force_link_blockBRegs() {}

void register_blockBRegs_variants() {
    instanceFactory::registerBlock("blockBRegs_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockBRegs>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _blockBRegs_registered = (register_blockBRegs_variants(), 0);
} // namespace
// === End block factory registration ===

void blockBRegs::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(9))-1); }

blockBRegs::blockBRegs(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockBRegs", name(), bbMode)
        ,blockBRegsBase(name(), variant)
        ,regs(log_)
        ,rwD(dRegSt::_packedSt(0x0))
        ,roBsize()
        ,blockBTable1_adapter(blockBTable1)
        ,blockBTableExt_adapter(blockBRegsBase::blockBTableExt)
        ,blockBTable37Bit_adapter(blockBRegsBase::blockBTable37Bit)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_BLOCKB_BLOCKBTABLE1 = 0x0;
    constexpr uint64_t REG_ADDR_BLOCKB_BLOCKBTABLE37BIT = 0x80;
    constexpr uint64_t REG_ADDR_BLOCKB_BLOCKBTABLEEXT = 0x100;
    constexpr uint64_t REG_ADDR_BLOCKB_RWD = 0x140;
    constexpr uint64_t REG_ADDR_BLOCKB_ROBSIZE = 0x148;

    // register memories for FW access
    regs.addMemory( REG_ADDR_BLOCKB_BLOCKBTABLE1, bigSt::_byteWidth, BSIZE, std::string(this->name()) + ".blockBTable1", &blockBTable1_adapter);
    regs.addMemory( REG_ADDR_BLOCKB_BLOCKBTABLE37BIT, test37BitRegSt::_byteWidth, BSIZE, std::string(this->name()) + ".blockBTable37Bit", &blockBTable37Bit_adapter);
    regs.addMemory( REG_ADDR_BLOCKB_BLOCKBTABLEEXT, seeSt::_byteWidth, BSIZE, std::string(this->name()) + ".blockBTableExt", &blockBTableExt_adapter);
    // register registers for FW access
    regs.addRegister( REG_ADDR_BLOCKB_RWD, 1, "rwD", &rwD );
    regs.addRegister( REG_ADDR_BLOCKB_ROBSIZE, 1, "roBsize", &roBsize );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

