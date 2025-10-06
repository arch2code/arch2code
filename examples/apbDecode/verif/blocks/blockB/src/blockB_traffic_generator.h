#ifndef BLOCKB_TRAFFIC_GENERATOR_H_
#define BLOCKB_TRAFFIC_GENERATOR_H_

#include "systemc.h"
#include "logging.h"
#include "regAddresses.h"

std::array<bMemSt, MEMORYB_WORDS> bTableData_ = { {
    bMemSt( sc_bv<96>("0x76b484440617ed57089d9dd8") ), bMemSt( sc_bv<96>("0xc8ff8ec20931d6702572e705") ), bMemSt( sc_bv<96>("0xa1c194f75de2fd8feac0b9f5") ), bMemSt( sc_bv<96>("0x7af975467c1528603e4ef955") ),
    bMemSt( sc_bv<96>("0x89262060219f5a0041cc6188") ), bMemSt( sc_bv<96>("0xe21f53ec3c3611455ad2be09") ), bMemSt( sc_bv<96>("0x623a16c8fa41bd2a9367bab4") ), bMemSt( sc_bv<96>("0xc4bc0442f58ff58ac4beffac") ),
    bMemSt( sc_bv<96>("0xc117fa4baecd1031cd796369") ), bMemSt( sc_bv<96>("0x99f17a55d972751bda891910") ), bMemSt( sc_bv<96>("0x51b3e994f9bc2f1af5868a13") ), bMemSt( sc_bv<96>("0x7bf98bbd389f32608d1830df") ),
    bMemSt( sc_bv<96>("0x875e1c7d7c312e2df3c7fefd") ), bMemSt( sc_bv<96>("0x7fdb5b74b60a90fcf43cbe7d") ), bMemSt( sc_bv<96>("0x1cafdbce68b477f1960caa88") ), bMemSt( sc_bv<96>("0x79cd3eea2a186cae73070224") ),
    bMemSt( sc_bv<96>("0xd66bcf0278d5001fa6549410") ), bMemSt( sc_bv<96>("0x6c671a52d10776eb08a628bd") ), bMemSt( sc_bv<96>("0xdc60d015ede5d4fb12765983") ), bMemSt( sc_bv<96>("0xbf8e6a8576a10f052d1519b5") ),
    bMemSt( sc_bv<96>("0x1161e49df909b205d7b81839") )
} };

class blockB_traffic_generator: public sc_module, public blockBInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (blockB_traffic_generator);

    blockB_traffic_generator(sc_module_name modulename) :
        blockBInverted("blockB_traffic_generator"),
        log_("TG")
    {
        SC_THREAD(main_thread);
    }

    typedef sc_bv<96> bMemScT;

    void main_thread() {

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

    void writeBlockBTableMem(const int rowId, bMemSt &entry) {
        apbAddrSt apbAddr;
        apbDataSt apbData;

        bMemScT bMemSc;

        bMemSc = entry.sc_pack();

        apbAddr.address = REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x0;
        apbData.data = bMemSc.range(31, 0).to_int();
        apbReg->request(true, apbAddr, apbData);

        apbAddr.address = REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x4;
        apbData.data = (apbDataT) bMemSc.range(63, 32).to_int();
        apbReg->request(true, apbAddr, apbData);

        apbAddr.address = REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x8;
        apbData.data = (apbDataT) bMemSc.range(95, 64).to_int();
        apbReg->request(true, apbAddr, apbData);

    }

    void readBlockBTableMem(const int rowId, bMemSt &entry) {
        apbAddrSt apbAddr;
        apbDataSt apbData;

        bMemScT bMemSc;

        apbAddr.address = REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x0;
        apbReg->request(false, apbAddr, apbData);
        bMemSc.range(31, 0) = apbData.data;

        apbAddr.address = REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x4;
        apbReg->request(false, apbAddr, apbData);
        bMemSc.range(63, 32) = apbData.data;

        apbAddr.address = REG_BLOCKB_BLOCKBTABLE + rowId * 0x10 + 0x8;
        apbReg->request(false, apbAddr, apbData);
        bMemSc.range(95, 64) = apbData.data;

        entry.sc_unpack(bMemSc);
    }

};

#endif /* BLOCKB_TRAFFIC_GENERATOR_H_ */
