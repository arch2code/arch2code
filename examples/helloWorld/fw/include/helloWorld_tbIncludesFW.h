
#ifndef HELLOWORLD_TBINCLUDESFW_H_
#define HELLOWORLD_TBINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=helloWorld_tb.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
inline constexpr uint32_t BUFFER_SIZE = 64;  // Buffer size

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint8_t byteT; // [8] Byte
typedef uint64_t qwordT; // [64] 64 bits

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct test_st {
    byteT a; //

    test_st() { memset(this, 0, sizeof(test_st)); }

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test_st::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (byteT)((_src));
    }
    explicit test_st(
        byteT a_) :
        a(a_)
    {}

};
struct test_no_tracker_st {
    byteT a; //

    test_no_tracker_st() { memset(this, 0, sizeof(test_no_tracker_st)); }

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test_no_tracker_st::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (byteT)((_src));
    }
    explicit test_no_tracker_st(
        byteT a_) :
        a(a_)
    {}

};
struct data_st {
    qwordT b; //

    data_st() { memset(this, 0, sizeof(data_st)); }

    static constexpr uint16_t _bitWidth = 64;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, data_st::_byteWidth);
        _ret = b;
    }
    inline void unpack(const _packedSt &_src)
    {
        b = (qwordT)((_src));
    }
    explicit data_st(
        qwordT b_) :
        b(b_)
    {}

};

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //HELLOWORLD_TBINCLUDESFW_H_
