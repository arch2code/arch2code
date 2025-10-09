//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockA.h"
SC_HAS_PROCESS(blockA);

blockA::registerBlock blockA::registerBlock_; //register the block with the factory

void blockA::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(3))-1); }

blockA::blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockA", name(), bbMode)
        ,blockABase(name(), variant)
        ,regs(log_)
        ,roA()
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // register registers for FW access
    regs.addRegister( 0x0, 1, "roA", &roA );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(startTest);
}

void blockA::startTest(void)
{
    startDone->notify();
}
