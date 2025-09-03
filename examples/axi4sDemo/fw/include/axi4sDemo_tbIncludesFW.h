
#ifndef AXI4SDEMO_TBINCLUDESFW_H_
#define AXI4SDEMO_TBINCLUDESFW_H_
// 

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=axi4sDemo_tb.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint8_t bv4_t; // [4] Bit Vector 4 bits
typedef uint8_t bv8_t; // [8] Bit Vector 8 bits
typedef uint16_t bv16_t; // [16] Bit Vector 16 bits
typedef uint64_t bv64_t; // [64] Bit Vector 64 bits
struct bv256_t { uint64_t word[ 4 ]; }; // [256] Bit Vector 256 bits

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct data_t1_t {
    bv256_t data; //

    data_t1_t() { memset(this, 0, sizeof(data_t1_t)); }

    static constexpr uint16_t _bitWidth = 256;
    static constexpr uint16_t _byteWidth = 32;
    typedef uint64_t _packedSt[4];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, data_t1_t::_byteWidth);
        pack_bits((uint64_t *)&_ret, 0, (uint64_t *)&data, 256);
    }
    inline void unpack(_packedSt &_src)
    {
        uint16_t _pos{0};
        data.word[0] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        data.word[1] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        data.word[2] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        data.word[3] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
    }
    explicit data_t1_t(
        bv256_t data_) :
        data(data_)
    {}

};
struct tid_t1_t {
    bv4_t tid; //

    tid_t1_t() { memset(this, 0, sizeof(tid_t1_t)); }

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tid_t1_t::_byteWidth);
        _ret = tid;
    }
    inline void unpack(_packedSt &_src)
    {
        tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    explicit tid_t1_t(
        bv4_t tid_) :
        tid(tid_)
    {}

};
struct tdest_t1_t {
    bv4_t tid; //

    tdest_t1_t() { memset(this, 0, sizeof(tdest_t1_t)); }

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tdest_t1_t::_byteWidth);
        _ret = tid;
    }
    inline void unpack(_packedSt &_src)
    {
        tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    explicit tdest_t1_t(
        bv4_t tid_) :
        tid(tid_)
    {}

};
struct tuser_t1_t {
    bv16_t parity; //

    tuser_t1_t() { memset(this, 0, sizeof(tuser_t1_t)); }

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tuser_t1_t::_byteWidth);
        _ret = parity;
    }
    inline void unpack(_packedSt &_src)
    {
        parity = (bv16_t)((_src));
    }
    explicit tuser_t1_t(
        bv16_t parity_) :
        parity(parity_)
    {}

};
struct data_t2_t {
    bv64_t data; //

    data_t2_t() { memset(this, 0, sizeof(data_t2_t)); }

    static constexpr uint16_t _bitWidth = 64;
    static constexpr uint16_t _byteWidth = 8;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, data_t2_t::_byteWidth);
        _ret = data;
    }
    inline void unpack(_packedSt &_src)
    {
        data = (bv64_t)((_src));
    }
    explicit data_t2_t(
        bv64_t data_) :
        data(data_)
    {}

};
struct tid_t2_t {
    bv4_t tid; //

    tid_t2_t() { memset(this, 0, sizeof(tid_t2_t)); }

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tid_t2_t::_byteWidth);
        _ret = tid;
    }
    inline void unpack(_packedSt &_src)
    {
        tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    explicit tid_t2_t(
        bv4_t tid_) :
        tid(tid_)
    {}

};
struct tdest_t2_t {
    bv4_t tid; //

    tdest_t2_t() { memset(this, 0, sizeof(tdest_t2_t)); }

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tdest_t2_t::_byteWidth);
        _ret = tid;
    }
    inline void unpack(_packedSt &_src)
    {
        tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    explicit tdest_t2_t(
        bv4_t tid_) :
        tid(tid_)
    {}

};
struct tuser_t2_t {
    bv4_t parity; //

    tuser_t2_t() { memset(this, 0, sizeof(tuser_t2_t)); }

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tuser_t2_t::_byteWidth);
        _ret = parity;
    }
    inline void unpack(_packedSt &_src)
    {
        parity = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    explicit tuser_t2_t(
        bv4_t parity_) :
        parity(parity_)
    {}

};

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //AXI4SDEMO_TBINCLUDESFW_H_
