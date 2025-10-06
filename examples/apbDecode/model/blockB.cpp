//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "regAddresses.h"
// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockB.h"
SC_HAS_PROCESS(blockB);

blockB::registerBlock blockB::registerBlock_; //register the block with the factory

void blockB::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(10-1))-1); }

blockB::blockB(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockB", name(), bbMode)
        ,blockBBase(name(), variant)
        ,regs(log_)
        ,rwUn0B()
        ,roB()
        ,blockBTable(name(), "blockBTable", mems, MEMORYB_WORDS)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // register memories for FW access
    regs.addMemory( 0x0, 0x150, std::string(this->name()) + ".blockBTable", &blockBTable);
    // register registers for FW access
    regs.addRegister( 0x200, 3, "rwUn0B", &rwUn0B );
    regs.addRegister( 0x208, 4, "roB", &roB );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
