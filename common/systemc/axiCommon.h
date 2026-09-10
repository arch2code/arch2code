// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_COMMON_H
#define AXI_COMMON_H
#include <cstdint>
#include <optional>
#include <string>

enum _axiResponseT{ AXIRESP_OKAY=0, AXIRESP_EXOKAY=1, AXIRESP_SLVERR=2, AXIRESP_DECERR=3 };
inline const char* _axiResponseT_prt( _axiResponseT val )
{
    switch( val )
    {
        case AXIRESP_OKAY: return( "OKAY" );
        case AXIRESP_EXOKAY: return( "EXOKAY" );
        case AXIRESP_SLVERR: return( "SLVERR" );
        case AXIRESP_DECERR: return( "DECERR" );
    }
    return("!!!BADENUM!!!");
}
enum _axiBurstT{ AXIBURST_FIXED=0, AXIBURST_INCR=1, AXIBURST_WRAP=2 };
inline const char* _axiBurstT_prt( _axiBurstT val )
{
    switch( val )
    {
        case AXIBURST_FIXED: return( "FIXED" );
        case AXIBURST_INCR: return( "INCR" );
        case AXIBURST_WRAP: return( "WRAP" );
    }
    return("!!!BADENUM!!!");
}
typedef uint8_t _axiSizeT; // [3] Bytes in transfer encoded 0=1, 1=2, 2=4, 3=8, 4=16, 5=32, 6=64, 7=128

// AXI transaction ID width. Override with -DAXI_ID_WIDTH=<n>; the storage type,
// the transaction-tracking span and every channel's idWidth follow it.
// Default 4 reproduces the previous hard-coded behaviour exactly.
#ifndef AXI_ID_WIDTH
#define AXI_ID_WIDTH 4
#endif
static constexpr unsigned int axiIdWidth = AXI_ID_WIDTH;
#define AXI_TRANSACTION_ID_MAX (1u << AXI_ID_WIDTH)
#if AXI_ID_WIDTH <= 8
typedef uint8_t _axiIdT; // AXI Id
#elif AXI_ID_WIDTH <= 16
typedef uint16_t _axiIdT;
#else
typedef uint32_t _axiIdT;
#endif
// Below 2 bits, Verilator's `--pins-bv 2` presents the id ports as `bool`
// while the BFM still declares them `sc_bv<idWidth>`, so elaboration fails;
// above 31 bits, AXI_TRANSACTION_ID_MAX's `1u << AXI_ID_WIDTH` overflows.
// Each AXI channel also allocates several vectors of AXI_TRANSACTION_ID_MAX
// entries, so its footprint grows as 2^AXI_ID_WIDTH.
static_assert(AXI_ID_WIDTH >= 2 && AXI_ID_WIDTH <= 31, "AXI_ID_WIDTH must be 2..31");
typedef uint8_t _axiLenT;

struct _axi_transaction_st {
    _axi_transaction_st()
        : id(0), len(0), size(0), transactionNo(0), transactionStr(std::nullopt) {}
    _axi_transaction_st(_axiIdT id_, uint8_t len_, _axiSizeT size_, int no, std::optional<std::string> str = std::nullopt)
        : id(id_), len(len_), size(size_), transactionNo(no), transactionStr(std::move(str)) {}
    _axiIdT id;
    uint8_t len;
    _axiSizeT size;
    uint64_t transactionNo;
    std::optional<std::string> transactionStr;
    _axi_transaction_st(const _axi_transaction_st& other) = default;
    _axi_transaction_st& operator=(const _axi_transaction_st& other) = default;
};

#endif //AXI_COMMON_H
