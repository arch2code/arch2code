// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AHB_COMMON_H
#define AHB_COMMON_H
#include <cstdint>
#include <optional>
#include <string>

// C++ mirror of interfaces/ahb/ahb_types.yaml.
enum _ahbTransT{ AHBTRANS_IDLE=0, AHBTRANS_BUSY=1, AHBTRANS_NONSEQ=2, AHBTRANS_SEQ=3 };
inline const char* _ahbTransT_prt( _ahbTransT val )
{
    switch( val )
    {
        case AHBTRANS_IDLE: return( "IDLE" );
        case AHBTRANS_BUSY: return( "BUSY" );
        case AHBTRANS_NONSEQ: return( "NONSEQ" );
        case AHBTRANS_SEQ: return( "SEQ" );
    }
    return("!!!BADENUM!!!");
}
enum _ahbBurstT{ AHBBURST_SINGLE=0, AHBBURST_INCR=1, AHBBURST_WRAP4=2, AHBBURST_INCR4=3,
                 AHBBURST_WRAP8=4, AHBBURST_INCR8=5, AHBBURST_WRAP16=6, AHBBURST_INCR16=7 };
inline const char* _ahbBurstT_prt( _ahbBurstT val )
{
    switch( val )
    {
        case AHBBURST_SINGLE: return( "SINGLE" );
        case AHBBURST_INCR: return( "INCR" );
        case AHBBURST_WRAP4: return( "WRAP4" );
        case AHBBURST_INCR4: return( "INCR4" );
        case AHBBURST_WRAP8: return( "WRAP8" );
        case AHBBURST_INCR8: return( "INCR8" );
        case AHBBURST_WRAP16: return( "WRAP16" );
        case AHBBURST_INCR16: return( "INCR16" );
    }
    return("!!!BADENUM!!!");
}
typedef uint8_t _ahbSizeT; // [3] Bytes in transfer encoded 0=1, 1=2, 2=4, 3=8, 4=16, 5=32, 6=64, 7=128
typedef uint8_t _ahbProtT; // [4] bit 0 data/opcode, bit 1 privileged, bit 2 bufferable, bit 3 cacheable

// Pin widths of the fields above.
constexpr unsigned int AHB_TRANS_WIDTH = 2;
constexpr unsigned int AHB_SIZE_WIDTH = 3;
constexpr unsigned int AHB_BURST_WIDTH = 3;
constexpr unsigned int AHB_PROT_WIDTH = 4;

// One transfer between its address phase and its data phase, in address order.
struct _ahb_transfer_st {
    bool write = false;
    uint64_t transactionNo = 0;
    std::optional<std::string> transactionStr;
};

#endif //AHB_COMMON_H
