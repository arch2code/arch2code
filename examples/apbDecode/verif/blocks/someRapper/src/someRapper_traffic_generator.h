#ifndef SOMERAPPER_TRAFFIC_GENERATOR_H_
#define SOMERAPPER_TRAFFIC_GENERATOR_H_

#include "systemc.h"
#include "logging.h"
#include "regAddresses.h"

std::array<aMemSt, MEMORYA_WORDS>  aTableData1_ = {{
    aMemSt(sc_bv<63>(0x2a782d645e49c378)), aMemSt(sc_bv<63>(0xe13233f8dae11506)), aMemSt(sc_bv<63>(0x0f3a3630616ff2a5)), aMemSt(sc_bv<63>(0x2667b149254fe22d)),
    aMemSt(sc_bv<63>(0x85a44e2af6455b16)), aMemSt(sc_bv<63>(0x61097206ad25b348)), aMemSt(sc_bv<63>(0xd8e59198098f1aed)), aMemSt(sc_bv<63>(0x2ee28680ca8e5c38)),
    aMemSt(sc_bv<63>(0x66e0f88a4203aaf9)), aMemSt(sc_bv<63>(0x0804ff7abdc4fa47)), aMemSt(sc_bv<63>(0xda41c4249404b124)), aMemSt(sc_bv<63>(0xa386ec142781063f)),
    aMemSt(sc_bv<63>(0x7990686237c4bf0a)), aMemSt(sc_bv<63>(0x930d5092fa461fb4)), aMemSt(sc_bv<63>(0x91b3a192d32d1227)), aMemSt(sc_bv<63>(0xc376ab97b1e892c2)),
    aMemSt(sc_bv<63>(0x087d0f121f97f58d)), aMemSt(sc_bv<63>(0xd7d4cd3c2cafb885)), aMemSt(sc_bv<63>(0x84ead5225e181999))
}};

std::array<bMemSt, MEMORYB_WORDS> bTableData_ = {{
    bMemSt( sc_bv<96>("0x76b484440617ed57089d9dd8") ), bMemSt( sc_bv<96>("0xc8ff8ec20931d6702572e705") ), bMemSt( sc_bv<96>("0xa1c194f75de2fd8feac0b9f5") ), bMemSt( sc_bv<96>("0x7af975467c1528603e4ef955") ),
    bMemSt( sc_bv<96>("0x89262060219f5a0041cc6188") ), bMemSt( sc_bv<96>("0xe21f53ec3c3611455ad2be09") ), bMemSt( sc_bv<96>("0x623a16c8fa41bd2a9367bab4") ), bMemSt( sc_bv<96>("0xc4bc0442f58ff58ac4beffac") ),
    bMemSt( sc_bv<96>("0xc117fa4baecd1031cd796369") ), bMemSt( sc_bv<96>("0x99f17a55d972751bda891910") ), bMemSt( sc_bv<96>("0x51b3e994f9bc2f1af5868a13") ), bMemSt( sc_bv<96>("0x7bf98bbd389f32608d1830df") ),
    bMemSt( sc_bv<96>("0x875e1c7d7c312e2df3c7fefd") ), bMemSt( sc_bv<96>("0x7fdb5b74b60a90fcf43cbe7d") ), bMemSt( sc_bv<96>("0x1cafdbce68b477f1960caa88") ), bMemSt( sc_bv<96>("0x79cd3eea2a186cae73070224") ),
    bMemSt( sc_bv<96>("0xd66bcf0278d5001fa6549410") ), bMemSt( sc_bv<96>("0x6c671a52d10776eb08a628bd") ), bMemSt( sc_bv<96>("0xdc60d015ede5d4fb12765983") ), bMemSt( sc_bv<96>("0xbf8e6a8576a10f052d1519b5") ),
    bMemSt( sc_bv<96>("0x1161e49df909b205d7b81839") )
}};

class someRapper_traffic_generator: public sc_module, public someRapperInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (someRapper_traffic_generator);

    someRapper_traffic_generator(sc_module_name modulename) :
        someRapperInverted("someRapper_traffic_generator"),
        log_("TG")
    {
        SC_THREAD(main_thread);
    }

    typedef sc_bv<37> aRegScT;
    typedef sc_bv<48> un0ARegScT;
    typedef sc_bv<63> aMemScT;
    typedef sc_bv<24> un0BRegScSt;
    typedef sc_bv<29> aSizeRegScT;
    typedef sc_bv<96> bMemScT;

    void main_thread() {

        apbAddrSt addr;
        apbDataSt writeData;
        apbDataSt readData;

        wait(1, SC_US);

        aRegSt roA, roA_;
        aRegScT roASc;

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_ROA + 0x0;
        apbReg->request(false, addr, readData);
        roASc.range(31, 0) = readData.data;

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_ROA + 0x4;
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

        rwUn0A_.fa = 'a';
        rwUn0A_.fb = 0x12345678;
        rwUn0A_.fc = 'c';

        rwUn0ASc = rwUn0A_.sc_pack();

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_RWUN0A + 0x0;
        writeData.data = (apbDataT) rwUn0ASc.range(31, 0).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_RWUN0A + 0x4;
        writeData.data = (apbDataT) rwUn0ASc.range(47, 32).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_RWUN0A + 0x0;
        apbReg->request(false, addr, readData);
        rwUn0ASc.range(31, 0) = readData.data;

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_RWUN0A + 0x4;
        apbReg->request(false, addr, readData);
        rwUn0ASc.range(47, 32) = readData.data;

        rwUn0A.sc_unpack(rwUn0ASc);

        if(rwUn0A == rwUn0A_)
            log_.logPrint( "UBLOCKA.REG_BLOCKA_RWUN0A read success" );
        else
            Q_ASSERT(false, "UBLOCKA.REG_BLOCKA_RWUN0A read fail");

        wait(1, SC_US);

        un0ARegSt roUn0A, roUn0A_;
        un0ARegScT roUn0ASc;

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_ROUN0A + 0x0;
        apbReg->request(false, addr, readData);
        roUn0ASc.range(31, 0) = readData.data;

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_ROUN0A + 0x4;
        apbReg->request(false, addr, readData);
        roUn0ASc.range(47, 32) = readData.data;

        roUn0A_ = rwUn0A_;
        roUn0A.sc_unpack(roUn0ASc);

        if(roUn0A == roUn0A_)
            log_.logPrint( "UBLOCKA.REG_BLOCKA_ROUN0A read success" );
        else
            Q_ASSERT(false, "UBLOCKA.REG_BLOCKA_ROUN0A read fail");

        wait(1, SC_US);

        un0ARegSt extA, extA_;
        un0ARegScT extASc;

        extA_.fa = 'd';
        extA_.fb = 0xbf2035d0;
        extA_.fc = 'e';

        extASc = extA_.sc_pack();

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_EXTA + 0x0;
        writeData.data = (apbDataT) extASc.range(31, 0).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_EXTA + 0x4;
        writeData.data = (apbDataT) extASc.range(47, 32).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_EXTA + 0x0;
        apbReg->request(false, addr, readData);
        extASc.range(31, 0) = readData.data;

        addr.address = BASE_ADDR_UBLOCKA+REG_BLOCKA_EXTA + 0x4;
        apbReg->request(false, addr, readData);
        extASc.range(47, 32) = readData.data;

        extA.sc_unpack(extASc);

        if(extA == extA_)
            log_.logPrint( "UBLOCKA.REG_BLOCKA_EXTA read success" );
        else
            Q_ASSERT(false, "UBLOCKA.REG_BLOCKA_EXTA read fail");

        wait(1, SC_US);

        // Memory BlockATable1
        std::array<aMemSt, MEMORYA_WORDS>  aTableData1;

        // Memory BlockATable1 Write sequential
        for(unsigned int rowId=0; rowId<MEMORYA_WORDS; rowId++)
            writeBlockATable1Mem(rowId, aTableData1_[rowId]);

        // Memory BlockATable1 Read sequential
        for(unsigned int rowId=0; rowId<MEMORYA_WORDS; rowId++)
            readBlockATable1Mem(rowId, aTableData1[rowId]);

        // Compare data from BlockATable1 array
        if(aTableData1 == aTableData1_)
            log_.logPrint( "BlockATable1 write/read sequential success" );
        else
            Q_ASSERT(false, "BlockATable1 write/read sequential fail");

        wait(1, SC_US);

        aSizeRegSt roB, roB_;
        aSizeRegScT roBSc;

        addr.address = BASE_ADDR_UBLOCKB+REG_BLOCKB_ROB + 0x0;
        apbReg->request(false, addr, readData);
        roBSc.range(28, 0) = readData.data;

        roB_.index = 0x1b45f720;
        roB.sc_unpack(roBSc);

        if(roB == roB_)
            log_.logPrint( "UBLOCKB.REG_BLOCKB_ROB read success" );
        else
            Q_ASSERT(false, "UBLOCKB.REG_BLOCKB_ROB read fail");

        wait(1, SC_US);

        un0BRegSt rwUn0B, rwUn0B_;
        un0BRegScSt rwUn0BSc;

        rwUn0B_.fa = 0x08;
        rwUn0B_.fb = 0x656c;

        rwUn0BSc = rwUn0B_.sc_pack();

        addr.address = BASE_ADDR_UBLOCKB+REG_BLOCKB_RWUN0B + 0x0;
        writeData.data = (apbDataT) rwUn0BSc.range(23, 0).to_int();
        apbReg->request(true, addr, writeData);

        addr.address = BASE_ADDR_UBLOCKB+REG_BLOCKB_RWUN0B + 0x0;
        apbReg->request(false, addr, readData);
        rwUn0BSc.range(23, 0) = readData.data;

        rwUn0B.sc_unpack(rwUn0BSc);

        if(rwUn0B == rwUn0B_)
            log_.logPrint( "UBLOCKB.REG_BLOCKB_RWUN0B read success" );
        else
            Q_ASSERT(false, "UBLOCKB.REG_BLOCKB_RWUN0B read fail");

        wait(1, SC_US);

        // Memory blockBTable
        std::array<bMemSt, MEMORYB_WORDS>  bTableData;

        // Memory blockBTable Write sequential
        for(unsigned int rowId=0; rowId<MEMORYB_WORDS; rowId++)
            writeBlockBTableMem(rowId, bTableData_[rowId]);

        // Memory blockBTable Read sequential
        for(unsigned int rowId=0; rowId<MEMORYB_WORDS; rowId++)
            readBlockBTableMem(rowId, bTableData[rowId]);

        // Compare data from blockBTable array
        if(bTableData == bTableData_)
            log_.logPrint( "blockBTable write/read sequential success" );
        else
            Q_ASSERT(false, "blockBTable write/read sequential fail");

        wait(1, SC_US);

    }

    void writeBlockATable1Mem(const int rowId, aMemSt &entry) {
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

    void readBlockATable1Mem(const int rowId, aMemSt &entry) {
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

    void writeBlockBTableMem(const int rowId, bMemSt &entry) {
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

    void readBlockBTableMem(const int rowId, bMemSt &entry) {
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

};

#endif /* SOMERAPPER_TRAFFIC_GENERATOR_H_ */
