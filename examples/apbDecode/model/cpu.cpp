//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "regAddresses.h"
// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "cpu.h"
SC_HAS_PROCESS(cpu);

cpu::registerBlock cpu::registerBlock_; //register the block with the factory

cpu::cpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("cpu", name(), bbMode)
        ,cpuBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(registerTest);
};

void cpu::registerTest(void)
{
    apbAddrSt addr;
    apbDataSt writeData;
    apbDataSt readData;
    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_RWUN0B;
    writeData.data = 0x1;
    apbReg->request(true, addr, writeData);
    apbReg->request(false, addr, readData);
    Q_ASSERT(readData.data == writeData.data, "readData.data == writeData.data");
    apbReg->request(false, addr, readData);
    writeData.data = 0x0;
    apbReg->request(true, addr, writeData);
    apbReg->request(false, addr, readData);
    Q_ASSERT(readData.data == writeData.data, "readData.data == writeData.data");
    addr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_EXTA + 0x0;
    apbReg->request(false, addr, readData);
    addr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_EXTA + 0x4;
    apbReg->request(false, addr, readData);

    memAccessTest();

}

std::array<aMemSt, MEMORYA_WORDS>  aTableData0_ = {{
    aMemSt(sc_bv<63>(0x0617ed57089d9dd8)), aMemSt(sc_bv<63>(0x00e1111176b48444)), aMemSt(sc_bv<63>(0xc695507f0721c20c)), aMemSt(sc_bv<63>(0xa9787eb627ba61ce)),
    aMemSt(sc_bv<63>(0x3d9316874d65a751)), aMemSt(sc_bv<63>(0x7e14fd9e64eaa6dd)), aMemSt(sc_bv<63>(0x30f6175fdd4a9768)), aMemSt(sc_bv<63>(0xb92c463b00c783d6)),
    aMemSt(sc_bv<63>(0x5f36b26d40beb726)), aMemSt(sc_bv<63>(0x59099386bf2035d0)), aMemSt(sc_bv<63>(0x3de22bac8fdb39c3)), aMemSt(sc_bv<63>(0x03cdcc6b6ba930fc)),
    aMemSt(sc_bv<63>(0x4537798ed3264c5e)), aMemSt(sc_bv<63>(0x438a961f78d16d62)), aMemSt(sc_bv<63>(0x968daae93a7170fe)), aMemSt(sc_bv<63>(0xfb46e2a569dafdf4)),
    aMemSt(sc_bv<63>(0xbe8bd93ad728dfdc)), aMemSt(sc_bv<63>(0x3500da5e40b57a8c)), aMemSt(sc_bv<63>(0x0a6f54c648de9a9c))
}};

typedef sc_bv<63> aMemScT;
typedef sc_bv<96> bMemScT;

void cpu::memAccessTest(void)
{
    apbAddrSt addr;
    apbDataSt writeData;
    apbDataSt readData;

    // Memory blockATable0
    std::array<aMemSt, MEMORYA_WORDS>  aTableData0;

    // Memory blockATable0 Write sequential
    for(unsigned int rowId=0; rowId<MEMORYA_WORDS; rowId++)
        writeBlockATable0Mem(rowId, aTableData0_[rowId]);

    // Memory blockATable0 Read sequential
    for(unsigned int rowId=0; rowId<MEMORYA_WORDS; rowId++)
        readBlockATable0Mem(rowId, aTableData0[rowId]);

    // Compare data from blockATable0 array
    if(aTableData0 == aTableData0_)
        log_.logPrint( "blockATable0 write/read sequential success" );
    else
        Q_ASSERT(false, "blockATable0 write/read sequential fail");

    bMemSt bMemEntry, bMemEntry_;

    bMemEntry_.data[0] = 0x1234abcd;
    bMemEntry_.data[1] = 0x1ef66da9;
    bMemEntry_.data[2] = 0x39f5e44f;

    writeBlockBTableMem(0x5, bMemEntry_);
    readBlockBTableMem(0x5, bMemEntry);

    // Compare data from blockBTable array
    if(bMemEntry == bMemEntry_)
        log_.logPrint( "blockBTable write/read single success" );
    else
        Q_ASSERT(false, "blockBTable write/read single fail");


    aMemSt aMemEntry, aMemEntry_;

    aMemEntry_.data = 0x2a782d645e49c378; // From blockA HW @ 0x5

    readBlockATable1Mem(0x5, aMemEntry);

    // Compare data from blockA1Table array
    if(aMemEntry == aMemEntry_)
        log_.logPrint( "blockA1Table write/read single success" );
    else
        Q_ASSERT(false, "blockA1Table write/read single fail");

}

void cpu::writeBlockATable0Mem(const int rowId, aMemSt &entry) {
    apbAddrSt apbAddr;
    apbDataSt apbData;

    aMemScT aMemSc;

    aMemSc = entry.sc_pack();

    apbAddr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_BLOCKATABLE0 + rowId * 0x8 + 0x0;
    apbData.data = aMemSc.range(31, 0).to_int();
    apbReg->request(true, apbAddr, apbData);

    apbAddr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_BLOCKATABLE0 + rowId * 0x8 + 0x4;
    apbData.data = (apbDataT) aMemSc.range(62, 32).to_int();
    apbReg->request(true, apbAddr, apbData);
}

void cpu::readBlockATable0Mem(const int rowId, aMemSt &entry) {
    apbAddrSt apbAddr;
    apbDataSt apbData;

    aMemScT aMemSc;

    apbAddr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_BLOCKATABLE0 + rowId * 0x8 + 0x0;
    apbReg->request(false, apbAddr, apbData);
    aMemSc.range(31, 0) = apbData.data;

    apbAddr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_BLOCKATABLE0 + rowId * 0x8 + 0x4;
    apbReg->request(false, apbAddr, apbData);
    aMemSc.range(62, 32) = apbData.data;

    entry.sc_unpack(aMemSc);
}

void cpu::writeBlockATable1Mem(const int rowId, aMemSt &entry) {
    apbAddrSt apbAddr;
    apbDataSt apbData;

    aMemScT aMemSc;

    aMemSc = entry.sc_pack();

    apbAddr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_BLOCKATABLE1 + rowId * 0x8 + 0x0;
    apbData.data = aMemSc.range(31, 0).to_int();
    apbReg->request(true, apbAddr, apbData);

    apbAddr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_BLOCKATABLE1 + rowId * 0x8 + 0x4;
    apbData.data = (apbDataT) aMemSc.range(62, 32).to_int();
    apbReg->request(true, apbAddr, apbData);
}

void cpu::readBlockATable1Mem(const int rowId, aMemSt &entry) {
    apbAddrSt apbAddr;
    apbDataSt apbData;

    aMemScT aMemSc;

    apbAddr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_BLOCKATABLE1 + rowId * 0x8 + 0x0;
    apbReg->request(false, apbAddr, apbData);
    aMemSc.range(31, 0) = apbData.data;

    apbAddr.address = BASE_ADDR_UBLOCKA + REG_BLOCKA_BLOCKATABLE1 + rowId * 0x8 + 0x4;
    apbReg->request(false, apbAddr, apbData);
    aMemSc.range(62, 32) = apbData.data;

    entry.sc_unpack(aMemSc);
}

void cpu::writeBlockBTableMem(const int rowId, bMemSt &entry) {
    apbAddrSt apbAddr;
    apbDataSt apbData;

    bMemScT bMemSc;

    bMemSc = entry.sc_pack();

    apbAddr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x0;
    apbData.data = bMemSc.range(31, 0).to_int();
    apbReg->request(true, apbAddr, apbData);

    apbAddr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x4;
    apbData.data = (apbDataT) bMemSc.range(63, 32).to_int();
    apbReg->request(true, apbAddr, apbData);

    apbAddr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x8;
    apbData.data = (apbDataT) bMemSc.range(95, 64).to_int();
    apbReg->request(true, apbAddr, apbData);
}

void cpu::readBlockBTableMem(const int rowId, bMemSt &entry) {
    apbAddrSt apbAddr;
    apbDataSt apbData;

    bMemScT bMemSc;

    apbAddr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x0;
    apbReg->request(false, apbAddr, apbData);
    bMemSc.range(31, 0) = apbData.data;

    apbAddr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x4;
    apbReg->request(false, apbAddr, apbData);
    bMemSc.range(63, 32) = apbData.data;

    apbAddr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x8;
    apbReg->request(false, apbAddr, apbData);
    bMemSc.range(95, 64) = apbData.data;

    entry.sc_unpack(bMemSc);
}
