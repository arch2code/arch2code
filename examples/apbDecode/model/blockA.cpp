//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockA.h"
SC_HAS_PROCESS(blockA);

// === Block factory registration (blockA) ===
void force_link_blockA() {}

void register_blockA_variants() {
    instanceFactory::registerBlock("blockA_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockA>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _blockA_registered = (register_blockA_variants(), 0);
} // namespace
// === End block factory registration ===

void blockA::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(_a2cRegs, apbReg, (1<<(10))-1); }

blockA::blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockA", name(), bbMode)
        ,blockABase(name(), variant)
        ,_a2cRegs(log_)
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
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_BLOCKA_BLOCKATABLE0 = 0x0;
    constexpr uint64_t REG_ADDR_BLOCKA_BLOCKATABLE1 = 0x100;
    constexpr uint64_t REG_ADDR_BLOCKA_ROA = 0x200;
    constexpr uint64_t REG_ADDR_BLOCKA_RWUN0A = 0x208;
    constexpr uint64_t REG_ADDR_BLOCKA_ROUN0A = 0x210;
    constexpr uint64_t REG_ADDR_BLOCKA_EXTA = 0x218;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_BLOCKA_BLOCKATABLE0, aMemSt::_byteWidth, MEMORYA_WORDS, std::string(this->name()) + ".blockATable0", &blockATable0);
    _a2cRegs.addMemory( REG_ADDR_BLOCKA_BLOCKATABLE1, aMemSt::_byteWidth, MEMORYA_WORDS, std::string(this->name()) + ".blockATable1", &blockATable1);
    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_ROA, 5, "roA", &roA );
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_RWUN0A, 6, "rwUn0A", &rwUn0A );
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_ROUN0A, 6, "roUn0A", &roUn0A );
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_EXTA, 6, "extA", &extA );
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
