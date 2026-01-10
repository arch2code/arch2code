//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockBRegs.h"
SC_HAS_PROCESS(blockBRegs);

blockBRegs::registerBlock blockBRegs::registerBlock_; //register the block with the factory

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
    // register memories for FW access
    regs.addMemory( 0x0, 0x50, std::string(this->name()) + ".blockBTable1", &blockBTable1_adapter);
    regs.addMemory( 0x80, 0x50, std::string(this->name()) + ".blockBTable37Bit", &blockBTable37Bit_adapter);
    regs.addMemory( 0xd0, 0x28, std::string(this->name()) + ".blockBTableExt", &blockBTableExt_adapter);
    // register registers for FW access
    regs.addRegister( 0xf8, 1, "rwD", &rwD );
    regs.addRegister( 0x100, 1, "roBsize", &roBsize );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

