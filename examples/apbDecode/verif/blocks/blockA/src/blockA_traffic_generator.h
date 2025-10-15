#ifndef BLOCKA_TRAFFIC_GENERATOR_H_
#define BLOCKA_TRAFFIC_GENERATOR_H_

#include "systemc.h"
#include "logging.h"
#include "regAddresses.h"

std::array<aMemSt, MEMORYA_WORDS>  aTableData0_ = {{
    aMemSt(sc_bv<63>(0x0617ed57089d9dd8)), aMemSt(sc_bv<63>(0x00e1111176b48444)), aMemSt(sc_bv<63>(0xc695507f0721c20c)), aMemSt(sc_bv<63>(0xa9787eb627ba61ce)),
    aMemSt(sc_bv<63>(0x3d9316874d65a751)), aMemSt(sc_bv<63>(0x7e14fd9e64eaa6dd)), aMemSt(sc_bv<63>(0x30f6175fdd4a9768)), aMemSt(sc_bv<63>(0xb92c463b00c783d6)),
    aMemSt(sc_bv<63>(0x5f36b26d40beb726)), aMemSt(sc_bv<63>(0x59099386bf2035d0)), aMemSt(sc_bv<63>(0x3de22bac8fdb39c3)), aMemSt(sc_bv<63>(0x03cdcc6b6ba930fc)),
    aMemSt(sc_bv<63>(0x4537798ed3264c5e)), aMemSt(sc_bv<63>(0x438a961f78d16d62)), aMemSt(sc_bv<63>(0x968daae93a7170fe)), aMemSt(sc_bv<63>(0xfb46e2a569dafdf4)),
    aMemSt(sc_bv<63>(0xbe8bd93ad728dfdc)), aMemSt(sc_bv<63>(0x3500da5e40b57a8c)), aMemSt(sc_bv<63>(0x0a6f54c648de9a9c))
}};

std::array<aMemSt, MEMORYA_WORDS>  aTableData1_ = {{
    aMemSt(sc_bv<63>(0x2a782d645e49c378)), aMemSt(sc_bv<63>(0xe13233f8dae11506)), aMemSt(sc_bv<63>(0x0f3a3630616ff2a5)), aMemSt(sc_bv<63>(0x2667b149254fe22d)),
    aMemSt(sc_bv<63>(0x85a44e2af6455b16)), aMemSt(sc_bv<63>(0x61097206ad25b348)), aMemSt(sc_bv<63>(0xd8e59198098f1aed)), aMemSt(sc_bv<63>(0x2ee28680ca8e5c38)),
    aMemSt(sc_bv<63>(0x66e0f88a4203aaf9)), aMemSt(sc_bv<63>(0x0804ff7abdc4fa47)), aMemSt(sc_bv<63>(0xda41c4249404b124)), aMemSt(sc_bv<63>(0xa386ec142781063f)),
    aMemSt(sc_bv<63>(0x7990686237c4bf0a)), aMemSt(sc_bv<63>(0x930d5092fa461fb4)), aMemSt(sc_bv<63>(0x91b3a192d32d1227)), aMemSt(sc_bv<63>(0xc376ab97b1e892c2)),
    aMemSt(sc_bv<63>(0x087d0f121f97f58d)), aMemSt(sc_bv<63>(0xd7d4cd3c2cafb885)), aMemSt(sc_bv<63>(0x84ead5225e181999))
}};

class blockA_traffic_generator: public sc_module, public blockAInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (blockA_traffic_generator);

    blockA_traffic_generator(sc_module_name modulename) :
        blockAInverted("blockA_traffic_generator"),
        log_("TG")
    {
        SC_THREAD(main_thread);
    }

    typedef sc_bv<37> aRegScT;
    typedef sc_bv<48> un0ARegScT;
    typedef sc_bv<63> aMemScT;

    void main_thread() {
        apbAddrSt addr;
        apbDataSt writeData;
        apbDataSt readData;

        wait(1, SC_US);

        aRegSt roA, roA_;
        aRegScT roASc;

        addr.address = REG_BLOCKA_ROA + 0x0;
        apbReg->request(false, addr, readData);
        roASc.range(31, 0) = readData.data;

        addr.address = REG_BLOCKA_ROA + 0x4;
        apbReg->request(false, addr, readData);
        roASc.range(36, 32) = readData.data;

        roA_.a = 0x1063686172;
        roA.sc_unpack(roASc);

        if(roA == roA_)
            log_.logPrint( "UBLOCKA.REG_BLOCKA_ROA read success" );
        else
            Q_ASSERT(false, "UBLOCKA.REG_BLOCKA_ROA read fail");

        wait(1, SC_US);

        un0ARegSt rwUn0A, rwUn0A_;
        un0ARegScT rwUn0ASc;

        // Reset value check

        rwUn0A_ = un0ARegSt((un0ARegSt::_packedSt)0x1234abcdefUL);

        addr.address = REG_BLOCKA_RWUN0A + 0x0;
        apbReg->request(false, addr, readData);
        rwUn0ASc.range(31, 0) = readData.data;

        addr.address = REG_BLOCKA_RWUN0A + 0x4;
        apbReg->request(false, addr, readData);
        rwUn0ASc.range(47, 32) = readData.data;

        rwUn0A.sc_unpack(rwUn0ASc);

        if(rwUn0A == rwUn0A_)
            log_.logPrint( "UBLOCKA.REG_BLOCKA_RWUN0A read default success" );
        else
            Q_ASSERT(false, "UBLOCKA.REG_BLOCKA_RWUN0A read default fail");

        wait(1, SC_US);

        rwUn0A_.fa = 'a';
        rwUn0A_.fb = 0x12345678;
        rwUn0A_.fc = 'c';

        rwUn0ASc = rwUn0A_.sc_pack();

        addr.address = REG_BLOCKA_RWUN0A + 0x0;
        writeData.data = (apbDataT) rwUn0ASc.range(31, 0).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = REG_BLOCKA_RWUN0A + 0x4;
        writeData.data = (apbDataT) rwUn0ASc.range(47, 32).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = REG_BLOCKA_RWUN0A + 0x0;
        apbReg->request(false, addr, readData);
        rwUn0ASc.range(31, 0) = readData.data;

        addr.address = REG_BLOCKA_RWUN0A + 0x4;
        apbReg->request(false, addr, readData);
        rwUn0ASc.range(47, 32) = readData.data;

        rwUn0A.sc_unpack(rwUn0ASc);

        if(rwUn0A == rwUn0A_)
            log_.logPrint( "REG_BLOCKA_RWUN0A read success" );
        else
            Q_ASSERT(false, "REG_BLOCKA_RWUN0A read fail");

        wait(1, SC_US);

        un0ARegSt roUn0A, roUn0A_;
        un0ARegScT roUn0ASc;

        addr.address = REG_BLOCKA_ROUN0A + 0x0;
        apbReg->request(false, addr, readData);
        roUn0ASc.range(31, 0) = readData.data;

        addr.address = REG_BLOCKA_ROUN0A + 0x4;
        apbReg->request(false, addr, readData);
        roUn0ASc.range(47, 32) = readData.data;

        roUn0A_ = rwUn0A_;
        roUn0A.sc_unpack(roUn0ASc);

        if(roUn0A == roUn0A_)
            log_.logPrint( "REG_BLOCKA_ROUN0A read success" );
        else
            Q_ASSERT(false, "REG_BLOCKA_ROUN0A read fail");

        wait(1, SC_US);

        un0ARegSt extA, extA_;
        un0ARegScT extASc;

        extA_.fa = 'd';
        extA_.fb = 0xbf2035d0;
        extA_.fc = 'e';

        extASc = extA_.sc_pack();

        addr.address = REG_BLOCKA_EXTA + 0x0;
        writeData.data = (apbDataT) extASc.range(31, 0).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = REG_BLOCKA_EXTA + 0x4;
        writeData.data = (apbDataT) extASc.range(47, 32).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = REG_BLOCKA_EXTA + 0x0;
        apbReg->request(false, addr, readData);
        extASc.range(31, 0) = readData.data;

        addr.address = REG_BLOCKA_EXTA + 0x4;
        apbReg->request(false, addr, readData);
        extASc.range(47, 32) = readData.data;

        extA.sc_unpack(extASc);

        if(extA == extA_)
            log_.logPrint( "REG_BLOCKA_EXTA read success" );
        else
            Q_ASSERT(false, "REG_BLOCKA_EXTA read fail");

        wait(1, SC_US);

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

        wait(1, SC_US);

        // Memory blockATable1
        std::array<aMemSt, MEMORYA_WORDS>  aTableData1;

        // Memory blockATable1 Write sequential
        for(unsigned int rowId=0; rowId<MEMORYA_WORDS; rowId++)
            writeBlockATable1Mem(rowId, aTableData1_[rowId]);

        // Memory blockATable1 Read sequential
        for(unsigned int rowId=0; rowId<MEMORYA_WORDS; rowId++)
            readBlockATable1Mem(rowId, aTableData1[rowId]);

        // Compare data from blockATable1 array
        if(aTableData1 == aTableData1_)
            log_.logPrint( "blockATable1 write/read sequential success" );
        else
            Q_ASSERT(false, "blockATable1 write/read sequential fail");

    }

    void writeBlockATable0Mem(const int rowId, aMemSt &entry) {
        apbAddrSt apbAddr;
        apbDataSt apbData;

        aMemScT aMemSc;

        aMemSc = entry.sc_pack();

        apbAddr.address = REG_BLOCKA_BLOCKATABLE0 + rowId * 0x8 + 0x0;
        apbData.data = aMemSc.range(31, 0).to_int();
        apbReg->request(true, apbAddr, apbData);

        apbAddr.address = REG_BLOCKA_BLOCKATABLE0 + rowId * 0x8 + 0x4;
        apbData.data = (apbDataT) aMemSc.range(62, 32).to_int();
        apbReg->request(true, apbAddr, apbData);

    }

    void readBlockATable0Mem(const int rowId, aMemSt &entry) {
        apbAddrSt apbAddr;
        apbDataSt apbData;

        aMemScT aMemSc;

        apbAddr.address = REG_BLOCKA_BLOCKATABLE0 + rowId * 0x8 + 0x0;
        apbReg->request(false, apbAddr, apbData);
        aMemSc.range(31, 0) = apbData.data;

        apbAddr.address = REG_BLOCKA_BLOCKATABLE0 + rowId * 0x8 + 0x4;
        apbReg->request(false, apbAddr, apbData);
        aMemSc.range(62, 32) = apbData.data;

        entry.sc_unpack(aMemSc);
    }

    void writeBlockATable1Mem(const int rowId, aMemSt &entry) {
        apbAddrSt apbAddr;
        apbDataSt apbData;

        aMemScT aMemSc;

        aMemSc = entry.sc_pack();

        apbAddr.address = REG_BLOCKA_BLOCKATABLE1 + rowId * 0x8 + 0x0;
        apbData.data = aMemSc.range(31, 0).to_int();
        apbReg->request(true, apbAddr, apbData);

        apbAddr.address = REG_BLOCKA_BLOCKATABLE1 + rowId * 0x8 + 0x4;
        apbData.data = (apbDataT) aMemSc.range(62, 32).to_int();
        apbReg->request(true, apbAddr, apbData);

    }

    void readBlockATable1Mem(const int rowId, aMemSt &entry) {
        apbAddrSt apbAddr;
        apbDataSt apbData;

        aMemScT aMemSc;

        apbAddr.address = REG_BLOCKA_BLOCKATABLE1 + rowId * 0x8 + 0x0;
        apbReg->request(false, apbAddr, apbData);
        aMemSc.range(31, 0) = apbData.data;

        apbAddr.address = REG_BLOCKA_BLOCKATABLE1 + rowId * 0x8 + 0x4;
        apbReg->request(false, apbAddr, apbData);
        aMemSc.range(62, 32) = apbData.data;

        entry.sc_unpack(aMemSc);
    }

};

#endif /* BLOCKA_TRAFFIC_GENERATOR_H_ */
