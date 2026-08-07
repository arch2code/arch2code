
#ifndef HIERVLSHAREDTYPESINCLUDESFW_H_
#define HIERVLSHAREDTYPESINCLUDESFW_H_
// 

// GENERATED_CODE_PARAM --project=hierVlDemo --context=../../yaml/hierVlSharedTypes.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr

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

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
namespace fw_ns {
// types
typedef uint8_t shared_bv8_t; // [8] Shared 8-bit vector
typedef uint32_t shared_bv32_t; // [32] Shared 32-bit vector

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
namespace fw_ns {
// enums

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
namespace fw_ns {
// structures
struct sharedInfoSt {
    shared_bv32_t value; //
    shared_bv8_t tag; //

    sharedInfoSt() { memset(this, 0, sizeof(sharedInfoSt)); }

    static constexpr uint16_t _bitWidth = 32 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sharedInfoSt::_byteWidth);
        _ret = value;
        _ret |= (uint64_t)tag << (32 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        value = (shared_bv32_t)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += 32;
        tag = (shared_bv8_t)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
    }
    explicit sharedInfoSt(
        shared_bv32_t value_,
        shared_bv8_t tag_) :
        value(value_),
        tag(tag_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //HIERVLSHAREDTYPESINCLUDESFW_H_
