//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "regAddresses.h"
// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockB.h"
SC_HAS_PROCESS(blockB);

blockB::registerBlock blockB::registerBlock_; //register the block with the factory

void blockB::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(10))-1); }

blockB::blockB(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockB", name(), bbMode)
        ,blockBBase(name(), variant)
        ,regs(log_)
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
    regs.addMemory( REG_ADDR_BLOCKB_BLOCKBTABLE, bMemSt::_byteWidth, MEMORYB_WORDS, std::string(this->name()) + ".blockBTable", &blockBTable);
    // register registers for FW access
    regs.addRegister( REG_ADDR_BLOCKB_RWUN0B, 3, "rwUn0B", &rwUn0B );
    regs.addRegister( REG_ADDR_BLOCKB_ROB, 4, "roB", &roB );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
