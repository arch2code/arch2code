//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockA.h"
SC_HAS_PROCESS(blockA);

blockA::registerBlock blockA::registerBlock_; //register the block with the factory

void blockA::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(10))-1); }

blockA::blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockA", name(), bbMode)
        ,blockABase(name(), variant)
        ,regs(log_)
        ,roA()
        ,rwUn0A(un0ARegSt::_packedSt(0x1234abcdef))
        ,roUn0A()
        ,extA()
        ,blockATable0(name(), "blockATable0", mems, MEMORYA_WORDS)
        ,blockATableX(name(), "blockATableX", mems, MEMORYA_WORDS)
        ,blockATable1(name(), "blockATable1", mems, MEMORYA_WORDS)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // register memories for FW access
    regs.addMemory( 0x0, aMemSt::_byteWidth, MEMORYA_WORDS, std::string(this->name()) + ".blockATable0", &blockATable0);
    regs.addMemory( 0x100, aMemSt::_byteWidth, MEMORYA_WORDS, std::string(this->name()) + ".blockATable1", &blockATable1);
    // register registers for FW access
    regs.addRegister( 0x200, 5, "roA", &roA );
    regs.addRegister( 0x208, 6, "rwUn0A", &rwUn0A );
    regs.addRegister( 0x210, 6, "roUn0A", &roUn0A );
    regs.addRegister( 0x218, 6, "extA", &extA );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(LocalRegAccess);
};

// Local register/memory access api using native data types
void blockA::LocalRegAccess() {

    // Register
    un0ARegSt arw;

    arw.fa = 'a';
    arw.fb = 0xfefe1234;
    arw.fc = 'c';

    extA.write(arw);

    // Memory
    aMemSt readData, writeData;

    writeData.data = 0x2a782d645e49c378;

    blockATable1[0x5].data = writeData.data;
    readData = blockATable1[0x5];

    Q_ASSERT(readData == writeData, "readData.data == writeData.data");

};
