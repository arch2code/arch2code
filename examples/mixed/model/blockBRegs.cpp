//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockBRegs.h"
SC_HAS_PROCESS(blockBRegs);

blockBRegs::registerBlock blockBRegs::registerBlock_; //register the block with the factory

void blockBRegs::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(25-1))-1); }

blockBRegs::blockBRegs(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockBRegs", name(), bbMode)
        ,blockBRegsBase(name(), variant)
        ,regs(log_)
        ,rwD()
        ,roBsize()
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // register registers for FW access
    regs.addRegister( 0x0, 1, "rwD", &rwD );
    regs.addRegister( 0x8, 1, "roBsize", &roBsize );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

