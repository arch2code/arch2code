
#ifndef APBDECODEINCLUDESFW_H_
#define APBDECODEINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=apbDecode.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
inline constexpr uint32_t ASIZE = 29;  // The size of A
inline constexpr uint32_t DWORD = 32;  // size of a double word
inline constexpr uint32_t MEMORYA_WORDS = 19;  // Address wordlines for memory A
inline constexpr uint32_t MEMORYA_WORDS_LOG2 = 5;  // Address wordlines for memory A log2
inline constexpr uint32_t MEMORYA_WIDTH = 63;  // Bit width of content for memory A, more than 32, less than 64
inline constexpr uint32_t MEMORYB_WORDS = 21;  // Address wordlines for memory B
inline constexpr uint32_t MEMORYB_WORDS_LOG2 = 5;  // Address wordlines for memory B log2

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint64_t thirtySevenBitT; // [37] Used as a thirty seven bit register structure
typedef uint32_t aSizeT; // [29] type of width ASIZE
typedef uint32_t apbAddrT; // [32] for addressing register via APB
typedef uint32_t apbDataT; // [32] for the data sent or received via APB
typedef uint8_t aAddrBitsT; // [5] size of memory A address in bits
typedef uint64_t aDataBitsT; // [63] size of memory A data in bits
typedef uint8_t bAddrBitsT; // [5] size of memory B address in bits
typedef uint8_t u8T; // [8] Byte integral type
typedef uint16_t u16T; // [16] sixteen bit integral type
typedef uint32_t u32T; // [32] thirty two bit integral type
typedef uint64_t u64T; // [64] sixty four bit integral type

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums
enum  addr_id_top {          //Generated type for addressing top instances
    ADDR_ID_TOP_UBLOCKA=0,   // uBlockA instance address
    ADDR_ID_TOP_UBLOCKB=1 }; // uBlockB instance address
inline const char* addr_id_top_prt( addr_id_top val )
{
    switch( val )
    {
        case ADDR_ID_TOP_UBLOCKA: return( "ADDR_ID_TOP_UBLOCKA" );
        case ADDR_ID_TOP_UBLOCKB: return( "ADDR_ID_TOP_UBLOCKB" );
    }
    return("!!!BADENUM!!!");
}

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct aRegSt {
    thirtySevenBitT a; //

    aRegSt() { memset(this, 0, sizeof(aRegSt)); }

    static constexpr uint16_t _bitWidth = 37;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aRegSt::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (thirtySevenBitT)((_src) & ((1ULL << 37) - 1));
    }
    explicit aRegSt(
        thirtySevenBitT a_) :
        a(a_)
    {}

};
struct un0BRegSt {
    u16T fb; //[23:8] - byte 3-4
    u8T fa; //[7:0] - byte 0-2

    un0BRegSt() { memset(this, 0, sizeof(un0BRegSt)); }

    static constexpr uint16_t _bitWidth = 16 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, un0BRegSt::_byteWidth);
        _ret = fb;
        _ret |= (uint32_t)fa << (16 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        fb = (u16T)((_src >> (_pos & 31)) & ((1ULL << 16) - 1));
        _pos += 16;
        fa = (u8T)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
    }
    explicit un0BRegSt(
        u16T fb_,
        u8T fa_) :
        fb(fb_),
        fa(fa_)
    {}

};
struct un0ARegSt {
    u8T fc; //[47:40] - byte 8-11
    u32T fb; //[39:8] - byte 4-7
    u8T fa; //[7:0] - byte 0-3

    un0ARegSt() { memset(this, 0, sizeof(un0ARegSt)); }

    static constexpr uint16_t _bitWidth = 8 + 32 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, un0ARegSt::_byteWidth);
        _ret = fc;
        _ret |= (uint64_t)fb << (8 & 63);
        _ret |= (uint64_t)fa << (40 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        fc = (u8T)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
        _pos += 8;
        fb = (u32T)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += 32;
        fa = (u8T)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
    }
    explicit un0ARegSt(
        u8T fc_,
        u32T fb_,
        u8T fa_) :
        fc(fc_),
        fb(fb_),
        fa(fa_)
    {}

};
struct aSizeRegSt {
    aSizeT index; //

    aSizeRegSt() { memset(this, 0, sizeof(aSizeRegSt)); }

    static constexpr uint16_t _bitWidth = ASIZE;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aSizeRegSt::_byteWidth);
        _ret = index;
    }
    inline void unpack(const _packedSt &_src)
    {
        index = (aSizeT)((_src) & ((1ULL << 29) - 1));
    }
    explicit aSizeRegSt(
        aSizeT index_) :
        index(index_)
    {}

};
struct apbAddrSt {
    apbAddrT address; //

    apbAddrSt() { memset(this, 0, sizeof(apbAddrSt)); }

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, apbAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (apbAddrT)((_src));
    }
    explicit apbAddrSt(
        apbAddrT address_) :
        address(address_)
    {}

};
struct apbDataSt {
    apbDataT data; //

    apbDataSt() { memset(this, 0, sizeof(apbDataSt)); }

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, apbDataSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (apbDataT)((_src));
    }
    explicit apbDataSt(
        apbDataT data_) :
        data(data_)
    {}

};
struct aMemAddrSt {
    aAddrBitsT address; //

    aMemAddrSt() { memset(this, 0, sizeof(aMemAddrSt)); }

    static constexpr uint16_t _bitWidth = MEMORYA_WORDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aMemAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (aAddrBitsT)((_src) & ((1ULL << 5) - 1));
    }
    explicit aMemAddrSt(
        aAddrBitsT address_) :
        address(address_)
    {}

};
struct aMemSt {
    aDataBitsT data; //

    aMemSt() { memset(this, 0, sizeof(aMemSt)); }

    static constexpr uint16_t _bitWidth = MEMORYA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aMemSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (aDataBitsT)((_src) & ((1ULL << 63) - 1));
    }
    explicit aMemSt(
        aDataBitsT data_) :
        data(data_)
    {}

};
struct bMemAddrSt {
    bAddrBitsT address; //

    bMemAddrSt() { memset(this, 0, sizeof(bMemAddrSt)); }

    static constexpr uint16_t _bitWidth = MEMORYB_WORDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, bMemAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (bAddrBitsT)((_src) & ((1ULL << 5) - 1));
    }
    explicit bMemAddrSt(
        bAddrBitsT address_) :
        address(address_)
    {}

};
struct bMemSt {
    u32T data[3]; //

    bMemSt() { memset(this, 0, sizeof(bMemSt)); }

    static constexpr uint16_t _bitWidth = 32*3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, bMemSt::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            pack_bits((uint64_t *)&_ret, _pos, data[i], 32);
            _pos += 32;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            uint16_t _bits = 32;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            data[i] = (u32T)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 32) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                data[i] = (u32T)(data[i] | ((_src[ _pos >> 6 ] << _consume) & ((1ULL << 32) - 1)));
                _pos += _bits;
            }
        }
    }
    explicit bMemSt(
        u32T data_[3])
    {
        memcpy(&data, &data_, sizeof(data));
    }

};

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //APBDECODEINCLUDESFW_H_
