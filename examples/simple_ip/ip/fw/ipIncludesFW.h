
#ifndef IPINCLUDESFW_H_
#define IPINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=ip --context=../../yaml/ip.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <cstdint>
#include <cstring>
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
namespace fw_ns {
//constants
inline constexpr uint32_t IP_DATA_WIDTH_X2 = 70 * 2;  // Derived width, 2x data (maxValue auto-derived); eval-derived, lives in constants: since no block param consumes it
inline constexpr uint32_t IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;  // Second-level derived width, 4x data
inline constexpr uint32_t IP_MEM_DEPTH_X2 = 16 * 2;  // Derived memory depth, 2x depth
inline constexpr uint32_t IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2;  // Second-level derived memory depth, 4x depth
inline constexpr uint32_t IP_FIXED_NIBBLE_COUNT = 5;  // Fixed array length for non-parameterized type tests
inline constexpr uint32_t IP_FIXED_PAIR_COUNT = 2;  // Fixed nested-structure array length
inline constexpr uint32_t IP_FIXED_WORD_COUNT = 6;  // Derived fixed array length
inline constexpr uint32_t IP_FIXED_DEPTH = 9;  // Fixed depth for widthLog2 and widthLog2minus1 tests
inline constexpr uint32_t IP_REG_ADDR_WIDTH = 32;  // Leaf register-bus address width
inline constexpr uint32_t IP_REG_DATA_WIDTH = 32;  // Leaf register-bus data width

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
namespace fw_ns {
// types
template<typename Config> struct ipDataT { uint64_t word[ 2 ]; }; // [max:128] IP data word, parameterizable
typedef uint8_t enableT; // [1] Single enable bit
template<typename Config> using ipMemAddrT = uint64_t; // [max:5] Index into ipMem (0 .. IP_MEM_DEPTH-1)
template<typename Config> struct ipDerivedWidthT { uint64_t word[ 8 ]; }; // [max:512] Type sized by a second-level eval-derived localparam
template<typename Config> using ipDerivedMemAddrT = uint64_t; // [max:7] Index into second-level derived-depth memory
typedef uint8_t ipFixedT; // [8] Fixed 8-bit byte (non-parameterizable)
typedef uint8_t ipFixedAddrT; // [8] Fixed 8-bit address index (non-parameterizable)
typedef uint8_t ipNibbleT; // [4] Fixed unsigned nibble
typedef int8_t ipSignedNibbleT; // [4] Fixed signed nibble
typedef int8_t ipSigned3T; // [3] Fixed signed 3-bit value
typedef uint8_t ipUnsigned5T; // [5] Fixed unsigned 5-bit value
typedef uint16_t ipUnsigned9T; // [9] Fixed unsigned 9-bit value
typedef uint16_t ipWordT; // [16] Fixed 16-bit word
typedef uint64_t ipWide37T; // [37] Fixed 37-bit value crossing a 32-bit boundary
typedef uint8_t ipFixedCountT; // [4] Fixed count field wide enough for 0..IP_FIXED_DEPTH
typedef uint8_t ipFixedIndexT; // [4] Fixed index field wide enough for 0..IP_FIXED_DEPTH-1
typedef uint32_t ipRegAddrT; // [32] ip leaf register-bus address
typedef uint32_t ipRegDataT; // [32] ip leaf register-bus data

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
namespace fw_ns {
// enums
enum  ipModeT {              //IP operating mode
    IP_MODE_OFF=0,           // Off
    IP_MODE_LOW=1,           // Low power
    IP_MODE_HIGH=2 };        // High performance
inline const char* ipModeT_prt( ipModeT val )
{
    switch( val )
    {
        case IP_MODE_OFF: return( "IP_MODE_OFF" );
        case IP_MODE_LOW: return( "IP_MODE_LOW" );
        case IP_MODE_HIGH: return( "IP_MODE_HIGH" );
    }
    return("!!!BADENUM!!!");
}
enum  ipFixedStatusT {       //Fixed status enum
    IP_STATUS_IDLE=0,        // Idle
    IP_STATUS_BUSY=1,        // Busy
    IP_STATUS_DONE=4 };      // Done
inline const char* ipFixedStatusT_prt( ipFixedStatusT val )
{
    switch( val )
    {
        case IP_STATUS_IDLE: return( "IP_STATUS_IDLE" );
        case IP_STATUS_BUSY: return( "IP_STATUS_BUSY" );
        case IP_STATUS_DONE: return( "IP_STATUS_DONE" );
    }
    return("!!!BADENUM!!!");
}
enum  ipFixedOpcodeT {       //Fixed-width opcode enum
    IP_OP_NOP=0,             // No operation
    IP_OP_LOAD=3,            // Load
    IP_OP_STORE=9 };         // Store
inline const char* ipFixedOpcodeT_prt( ipFixedOpcodeT val )
{
    switch( val )
    {
        case IP_OP_NOP: return( "IP_OP_NOP" );
        case IP_OP_LOAD: return( "IP_OP_LOAD" );
        case IP_OP_STORE: return( "IP_OP_STORE" );
    }
    return("!!!BADENUM!!!");
}

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
namespace fw_ns {
// structures
template<typename Config>
struct ipDataSt {
    ipDataT<Config> data; //Data word
    enableT marker; //Marker bit expected after the data payload

    ipDataSt() { memset(this, 0, sizeof(ipDataSt)); }

    static constexpr uint16_t _bitWidth = Config::IP_DATA_WIDTH + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipDataSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&data, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, marker, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&data, 0, sizeof(data));
        unpack_bits((uint64_t *)&data, 0, (uint64_t *)&_src, _pos, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
        marker = (enableT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    explicit ipDataSt(
        ipDataT<Config> data_,
        enableT marker_) :
        data(data_),
        marker(marker_)
    {}

};
template<typename Config>
struct ipCfgSt {
    ipDataT<Config> threshold; //Threshold value
    ipModeT mode; //Operating mode
    enableT enable; //Enable bit

    ipCfgSt() { memset(this, 0, sizeof(ipCfgSt)); }

    static constexpr uint16_t _bitWidth = Config::IP_DATA_WIDTH + 2 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipCfgSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&threshold, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, mode, 2);
        _pos += 2;
        pack_bits((uint64_t *)&_ret, _pos, enable, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&threshold, 0, sizeof(threshold));
        unpack_bits((uint64_t *)&threshold, 0, (uint64_t *)&_src, _pos, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
        mode = (ipModeT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (2)) - 1));
        _pos += 2;
        enable = (enableT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    explicit ipCfgSt(
        ipDataT<Config> threshold_,
        ipModeT mode_,
        enableT enable_) :
        threshold(threshold_),
        mode(mode_),
        enable(enable_)
    {}

};
template<typename Config>
struct ipMemSt {
    ipDataT<Config> data; //Data word

    ipMemSt() { memset(this, 0, sizeof(ipMemSt)); }

    static constexpr uint16_t _bitWidth = Config::IP_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipMemSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&data, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&data, 0, sizeof(data));
        unpack_bits((uint64_t *)&data, 0, (uint64_t *)&_src, _pos, Config::IP_DATA_WIDTH);
    }
    explicit ipMemSt(
        ipDataT<Config> data_) :
        data(data_)
    {}

};
template<typename Config>
struct ipMemAddrSt {
    ipMemAddrT<Config> address; //Memory address

    ipMemAddrSt() { memset(this, 0, sizeof(ipMemAddrSt)); }

    static constexpr uint16_t _bitWidth = clog2(Config::IP_MEM_DEPTH);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipMemAddrSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, address, clog2(Config::IP_MEM_DEPTH));
        _pos += clog2(Config::IP_MEM_DEPTH);
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ipMemAddrT<Config>)((_src) & ((1ULL << (clog2(Config::IP_MEM_DEPTH))) - 1));
    }
    explicit ipMemAddrSt(
        ipMemAddrT<Config> address_) :
        address(address_)
    {}

};
template<typename Config>
struct ipBurstSt {
    ipDataT<Config> samples[Config::IP_MEM_DEPTH]; //Burst of parameterizable samples

    ipBurstSt() { memset(this, 0, sizeof(ipBurstSt)); }

    static constexpr uint16_t _bitWidth = Config::IP_DATA_WIDTH*Config::IP_MEM_DEPTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[64];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipBurstSt<Config>::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<Config::IP_MEM_DEPTH; i++) {
            pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&samples[i], Config::IP_DATA_WIDTH);
            _pos += Config::IP_DATA_WIDTH;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<Config::IP_MEM_DEPTH; i++) {
            uint16_t _bits = Config::IP_DATA_WIDTH;
            uint16_t _consume;
            memset((uint64_t *)&samples[i], 0, sizeof(samples[i]));
            unpack_bits((uint64_t *)&samples[i], 0, (uint64_t *)&_src, _pos, Config::IP_DATA_WIDTH);
            _pos += Config::IP_DATA_WIDTH;
        }
    }
    explicit ipBurstSt(
        ipDataT<Config> samples_[Config::IP_MEM_DEPTH])
    {
        memcpy(&samples, &samples_, sizeof(samples));
    }

};
template<typename Config>
struct ipDerivedMemAddrSt {
    ipDerivedMemAddrT<Config> address; //Second-level derived-depth memory address

    ipDerivedMemAddrSt() { memset(this, 0, sizeof(ipDerivedMemAddrSt)); }

    static constexpr uint16_t _bitWidth = clog2(((Config::IP_MEM_DEPTH * 2) * 2));
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipDerivedMemAddrSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, address, clog2(((Config::IP_MEM_DEPTH * 2) * 2)));
        _pos += clog2(((Config::IP_MEM_DEPTH * 2) * 2));
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ipDerivedMemAddrT<Config>)((_src) & ((1ULL << (clog2(((Config::IP_MEM_DEPTH * 2) * 2)))) - 1));
    }
    explicit ipDerivedMemAddrSt(
        ipDerivedMemAddrT<Config> address_) :
        address(address_)
    {}

};
struct ipFixedSt {
    ipFixedT b; //Fixed byte

    ipFixedSt() { memset(this, 0, sizeof(ipFixedSt)); }

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedSt::_byteWidth);
        _ret = b;
    }
    inline void unpack(const _packedSt &_src)
    {
        b = (ipFixedT)((_src));
    }
    explicit ipFixedSt(
        ipFixedT b_) :
        b(b_)
    {}

};
struct ipFixedAddrSt {
    ipFixedAddrT a; //Fixed-width address

    ipFixedAddrSt() { memset(this, 0, sizeof(ipFixedAddrSt)); }

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedAddrSt::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (ipFixedAddrT)((_src));
    }
    explicit ipFixedAddrSt(
        ipFixedAddrT a_) :
        a(a_)
    {}

};
struct ipFixedHeaderSt {
    ipNibbleT tag; //Fixed packet tag
    ipFixedStatusT status; //Fixed status
    ipFixedOpcodeT opcode; //Fixed opcode

    ipFixedHeaderSt() { memset(this, 0, sizeof(ipFixedHeaderSt)); }

    static constexpr uint16_t _bitWidth = 4 + 3 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedHeaderSt::_byteWidth);
        _ret = tag;
        _ret |= (uint16_t)status << (4 & 15);
        _ret |= (uint16_t)opcode << (7 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        tag = (ipNibbleT)((_src >> (_pos & 15)) & ((1ULL << 4) - 1));
        _pos += 4;
        status = (ipFixedStatusT)((_src >> (_pos & 15)) & ((1ULL << 3) - 1));
        _pos += 3;
        opcode = (ipFixedOpcodeT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
    }
    explicit ipFixedHeaderSt(
        ipNibbleT tag_,
        ipFixedStatusT status_,
        ipFixedOpcodeT opcode_) :
        tag(tag_),
        status(status_),
        opcode(opcode_)
    {}

};
struct ipFixedSignedSt {
    ipUnsigned9T lane; //Unsigned 9-bit field
    ipUnsigned5T magnitude; //Unsigned 5-bit field
    ipSignedNibbleT offset; //Signed 4-bit field
    ipSigned3T tiny; //Signed 3-bit field

    ipFixedSignedSt() { memset(this, 0, sizeof(ipFixedSignedSt)); }

    static constexpr uint16_t _bitWidth = 9 + 5 + 4 + 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedSignedSt::_byteWidth);
        _ret = lane;
        _ret |= (uint32_t)magnitude << (9 & 31);
        _ret |= ((uint32_t)(offset & ((1ULL << (4)) - 1))) << (14 & 31);
        _ret |= ((uint32_t)(tiny & ((1ULL << (3)) - 1))) << (18 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        lane = (ipUnsigned9T)((_src >> (_pos & 31)) & ((1ULL << 9) - 1));
        _pos += 9;
        magnitude = (ipUnsigned5T)((_src >> (_pos & 31)) & ((1ULL << 5) - 1));
        _pos += 5;
        offset = (ipSignedNibbleT)((_src >> (_pos & 31)) & ((1ULL << 4) - 1));
        _pos += 4;
        // Sign extension for signed type
        if (offset & (1ULL << (4 - 1))) {
            offset = (ipSignedNibbleT)(offset | ~((1ULL << (4)) - 1));
        }
        tiny = (ipSigned3T)((_src >> (_pos & 31)) & ((1ULL << 3) - 1));
        _pos += 3;
        // Sign extension for signed type
        if (tiny & (1ULL << (3 - 1))) {
            tiny = (ipSigned3T)(tiny | ~((1ULL << (3)) - 1));
        }
    }
    explicit ipFixedSignedSt(
        ipUnsigned9T lane_,
        ipUnsigned5T magnitude_,
        ipSignedNibbleT offset_,
        ipSigned3T tiny_) :
        lane(lane_),
        magnitude(magnitude_),
        offset(offset_),
        tiny(tiny_)
    {}

};
struct ipFixedArraySt {
    ipWordT words[IP_FIXED_PAIR_COUNT]; //Fixed word array
    ipNibbleT nibbles[IP_FIXED_NIBBLE_COUNT]; //Fixed nibble array

    ipFixedArraySt() { memset(this, 0, sizeof(ipFixedArraySt)); }

    static constexpr uint16_t _bitWidth = 16*IP_FIXED_PAIR_COUNT + 4*IP_FIXED_NIBBLE_COUNT;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedArraySt::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            pack_bits((uint64_t *)&_ret, _pos, words[i], 16);
            _pos += 16;
        }
        for(unsigned int i=0; i<IP_FIXED_NIBBLE_COUNT; i++) {
            pack_bits((uint64_t *)&_ret, _pos, nibbles[i], 4);
            _pos += 4;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            uint16_t _bits = 16;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            words[i] = (ipWordT)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                words[i] = (ipWordT)(words[i] | ((_src << _consume) & ((1ULL << 16) - 1)));
                _pos += _bits;
            }
        }
        for(unsigned int i=0; i<IP_FIXED_NIBBLE_COUNT; i++) {
            uint16_t _bits = 4;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            nibbles[i] = (ipNibbleT)((_src >> (_pos & 63)) & ((1ULL << 4) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                nibbles[i] = (ipNibbleT)(nibbles[i] | ((_src << _consume) & ((1ULL << 4) - 1)));
                _pos += _bits;
            }
        }
    }
    explicit ipFixedArraySt(
        ipWordT words_[IP_FIXED_PAIR_COUNT],
        ipNibbleT nibbles_[IP_FIXED_NIBBLE_COUNT])
    {
        memcpy(&words, &words_, sizeof(words));
        memcpy(&nibbles, &nibbles_, sizeof(nibbles));
    }

};
struct ipFixedLog2St {
    ipFixedIndexT index; //Fixed widthLog2minus1 index
    ipFixedCountT count; //Fixed widthLog2 count

    ipFixedLog2St() { memset(this, 0, sizeof(ipFixedLog2St)); }

    static constexpr uint16_t _bitWidth = clog2(IP_FIXED_DEPTH) + clog2(IP_FIXED_DEPTH+1);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedLog2St::_byteWidth);
        _ret = index;
        _ret |= (uint8_t)count << (4 & 7);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        index = (ipFixedIndexT)((_src >> (_pos & 7)) & ((1ULL << 4) - 1));
        _pos += 4;
        count = (ipFixedCountT)((_src >> (_pos & 7)) & ((1ULL << 4) - 1));
    }
    explicit ipFixedLog2St(
        ipFixedIndexT index_,
        ipFixedCountT count_) :
        index(index_),
        count(count_)
    {}

};
struct ipFixedNestedSt {
    ipWide37T wideValue; //Wide fixed value
    ipFixedLog2St log2Fields; //Nested fixed log2 fields
    ipFixedArraySt arrays[IP_FIXED_PAIR_COUNT]; //Nested fixed arrays
    ipFixedSignedSt signedFields; //Nested signed and narrow fields
    ipFixedHeaderSt header; //Nested fixed header

    ipFixedNestedSt() { memset(this, 0, sizeof(ipFixedNestedSt)); }

    static constexpr uint16_t _bitWidth = 37 + ipFixedLog2St::_bitWidth + ipFixedArraySt::_bitWidth*IP_FIXED_PAIR_COUNT
                                          + ipFixedSignedSt::_bitWidth + ipFixedHeaderSt::_bitWidth;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedNestedSt::_byteWidth);
        _ret[ 0 ] = wideValue;
        {
            ipFixedLog2St::_packedSt _tmp{0};
            log2Fields.pack(_tmp);
            pack_bits((uint64_t *)&_ret, 37, _tmp, ipFixedLog2St::_bitWidth);
        }
        uint16_t _pos{45};
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            ipFixedArraySt::_packedSt _tmp{0};
            arrays[i].pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, _tmp, ipFixedArraySt::_bitWidth);
            _pos += ipFixedArraySt::_bitWidth;
        }
        {
            ipFixedSignedSt::_packedSt _tmp{0};
            signedFields.pack(_tmp);
            pack_bits((uint64_t *)&_ret, 149, _tmp, ipFixedSignedSt::_bitWidth);
        }
        {
            ipFixedHeaderSt::_packedSt _tmp{0};
            header.pack(_tmp);
            pack_bits((uint64_t *)&_ret, 170, _tmp, ipFixedHeaderSt::_bitWidth);
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        wideValue = (ipWide37T)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 37) - 1));
        _pos += 37;
        {
            uint64_t _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipFixedLog2St::_bitWidth);
            log2Fields.unpack(*((ipFixedLog2St::_packedSt*)&_tmp));
        }
        _pos += ipFixedLog2St::_bitWidth;
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            uint16_t _bits = ipFixedArraySt::_bitWidth;
            uint16_t _consume;
            {
                ipFixedArraySt::_packedSt _tmp{0};
                unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipFixedArraySt::_bitWidth);
                arrays[i].unpack(_tmp);
            }
            _pos += ipFixedArraySt::_bitWidth;
        }
        {
            uint64_t _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipFixedSignedSt::_bitWidth);
            signedFields.unpack(*((ipFixedSignedSt::_packedSt*)&_tmp));
        }
        _pos += ipFixedSignedSt::_bitWidth;
        {
            uint64_t _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipFixedHeaderSt::_bitWidth);
            header.unpack(*((ipFixedHeaderSt::_packedSt*)&_tmp));
        }
    }
    explicit ipFixedNestedSt(
        ipWide37T wideValue_,
        ipFixedLog2St log2Fields_,
        ipFixedArraySt arrays_[IP_FIXED_PAIR_COUNT],
        ipFixedSignedSt signedFields_,
        ipFixedHeaderSt header_) :
        wideValue(wideValue_),
        log2Fields(log2Fields_),
        signedFields(signedFields_),
        header(header_)
    {
        memcpy(&arrays, &arrays_, sizeof(arrays));
    }

};
template<typename Config>
struct ipParamNestedSt {
    ipDataSt<Config> payloads[IP_FIXED_PAIR_COUNT]; //Parameterizable nested sub-struct array
    ipCfgSt<Config> cfg; //Single nested parameterizable config sub-struct

    ipParamNestedSt() { memset(this, 0, sizeof(ipParamNestedSt)); }

    static constexpr uint16_t _bitWidth = ipDataSt<Config>::_bitWidth*IP_FIXED_PAIR_COUNT + ipCfgSt<Config>::_bitWidth;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[7];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipParamNestedSt<Config>::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            typename ipDataSt<Config>::_packedSt _tmp{0};
            payloads[i].pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&_tmp, ipDataSt<Config>::_bitWidth);
            _pos += ipDataSt<Config>::_bitWidth;
        }
        {
            typename ipCfgSt<Config>::_packedSt _tmp{0};
            cfg.pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&_tmp, ipCfgSt<Config>::_bitWidth);
            _pos += ipCfgSt<Config>::_bitWidth;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            uint16_t _bits = ipDataSt<Config>::_bitWidth;
            uint16_t _consume;
            {
                typename ipDataSt<Config>::_packedSt _tmp{0};
                unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipDataSt<Config>::_bitWidth);
                payloads[i].unpack(_tmp);
            }
            _pos += ipDataSt<Config>::_bitWidth;
        }
        {
            typename ipCfgSt<Config>::_packedSt _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipCfgSt<Config>::_bitWidth);
            cfg.unpack(_tmp);
        }
    }
    explicit ipParamNestedSt(
        ipDataSt<Config> payloads_[IP_FIXED_PAIR_COUNT],
        ipCfgSt<Config> cfg_) :
        cfg(cfg_)
    {
        memcpy(&payloads, &payloads_, sizeof(payloads));
    }

};
struct ipRegAddrSt {
    ipRegAddrT address; //

    ipRegAddrSt() { memset(this, 0, sizeof(ipRegAddrSt)); }

    static constexpr uint16_t _bitWidth = IP_REG_ADDR_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipRegAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ipRegAddrT)((_src));
    }
    explicit ipRegAddrSt(
        ipRegAddrT address_) :
        address(address_)
    {}

};
struct ipRegDataSt {
    ipRegDataT data; //

    ipRegDataSt() { memset(this, 0, sizeof(ipRegDataSt)); }

    static constexpr uint16_t _bitWidth = IP_REG_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipRegDataSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (ipRegDataT)((_src));
    }
    explicit ipRegDataSt(
        ipRegDataT data_) :
        data(data_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //IPINCLUDESFW_H_
