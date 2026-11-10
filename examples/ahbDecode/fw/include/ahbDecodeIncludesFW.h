
#ifndef AHBDECODEINCLUDESFW_H_
#define AHBDECODEINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=ahbDecode --context=ahbDecode.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
namespace fw_ns::ahbDecode {}
namespace fw_ns { using namespace ahbDecode; }

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <cstdint>
#include <cstring>
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
namespace fw_ns::ahbDecode {
//constants
inline constexpr uint32_t DWORD = 32;  // Register bus width
inline constexpr uint32_t TBL_WORDS = 8;  // Rows in leafA's table

} // namespace fw_ns::ahbDecode
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
namespace fw_ns::ahbDecode {
// types
typedef uint32_t ahbAddrT; // [32] AHB address
typedef uint32_t ahbDataT; // [32] AHB data
typedef uint16_t u16T; // [16] sixteen bit integral type
typedef uint32_t u32T; // [32] thirty two bit integral type
typedef uint8_t tblAddrT; // [3] leafA table row

} // namespace fw_ns::ahbDecode
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
namespace fw_ns::ahbDecode {
// enums
enum  addr_id_ahb_top {      //Generated type for addressing top instances
    ADDR_ID_AHB_TOP_ULEAFA=0,   // uLeafA instance address
    ADDR_ID_AHB_TOP_ULEAFB=1,   // uLeafB instance address
    ADDR_ID_AHB_TOP_USUBSYS=2 }; // uSubSys instance address
inline const char* addr_id_ahb_top_prt( addr_id_ahb_top val )
{
    switch( val )
    {
        case ADDR_ID_AHB_TOP_ULEAFA: return( "ADDR_ID_AHB_TOP_ULEAFA" );
        case ADDR_ID_AHB_TOP_ULEAFB: return( "ADDR_ID_AHB_TOP_ULEAFB" );
        case ADDR_ID_AHB_TOP_USUBSYS: return( "ADDR_ID_AHB_TOP_USUBSYS" );
    }
    return("!!!BADENUM!!!");
}
enum  addr_id_ahb_sub {      //Generated type for addressing sub instances
    ADDR_ID_AHB_SUB_ULEAFC=0 }; // uLeafC instance address
inline const char* addr_id_ahb_sub_prt( addr_id_ahb_sub val )
{
    switch( val )
    {
        case ADDR_ID_AHB_SUB_ULEAFC: return( "ADDR_ID_AHB_SUB_ULEAFC" );
    }
    return("!!!BADENUM!!!");
}

} // namespace fw_ns::ahbDecode
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
namespace fw_ns::ahbDecode {
// structures
struct ahbAddrSt {
    ahbAddrT address; /* [31:0] */ //

    ahbAddrSt() { memset(this, 0, sizeof(ahbAddrSt)); }

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ahbAddrT)((_src));
    }
    explicit ahbAddrSt(
        ahbAddrT address_) :
        address(address_)
    {}

};
struct ahbDataSt {
    ahbDataT data; /* [31:0] */ //

    ahbDataSt() { memset(this, 0, sizeof(ahbDataSt)); }

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (ahbDataT)((_src));
    }
    explicit ahbDataSt(
        ahbDataT data_) :
        data(data_)
    {}

};
struct cfgRegSt {
    u32T value; /* [31:0] */ //

    cfgRegSt() { memset(this, 0, sizeof(cfgRegSt)); }

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = value;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (u32T)((_src));
    }
    explicit cfgRegSt(
        u32T value_) :
        value(value_)
    {}

};
struct statRegSt {
    u16T value; /* [15:0] */ //

    statRegSt() { memset(this, 0, sizeof(statRegSt)); }

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = value;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (u16T)((_src));
    }
    explicit statRegSt(
        u16T value_) :
        value(value_)
    {}

};
struct cmdRegSt {
    u16T value; /* [15:0] */ //

    cmdRegSt() { memset(this, 0, sizeof(cmdRegSt)); }

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = value;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (u16T)((_src));
    }
    explicit cmdRegSt(
        u16T value_) :
        value(value_)
    {}

};
struct tblSt {
    u32T data; /* [31:0] */ //

    tblSt() { memset(this, 0, sizeof(tblSt)); }

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (u32T)((_src));
    }
    explicit tblSt(
        u32T data_) :
        data(data_)
    {}

};
struct tblAddrSt {
    tblAddrT address; /* [2:0] */ //

    tblAddrSt() { memset(this, 0, sizeof(tblAddrSt)); }

    static constexpr uint16_t _bitWidth = 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (tblAddrT)((_src) & ((1ULL << 3) - 1));
    }
    explicit tblAddrSt(
        tblAddrT address_) :
        address(address_)
    {}

};
} // namespace fw_ns::ahbDecode

// GENERATED_CODE_END
#endif //AHBDECODEINCLUDESFW_H_
