
#ifndef SIMPLEINCLUDESFW_H_
#define SIMPLEINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=simple --context=simple.yaml --mode=fw
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
inline constexpr uint32_t NUM_TAGS = 32;  // number of tags
inline constexpr uint32_t NUM_TAGS_LOG2 = 5;  // log2 of number of tags

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
namespace fw_ns {
// types
typedef uint8_t tag; // [5] tag

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
struct tag_st {
    tag tagId; //tag id

    tag_st() { memset(this, 0, sizeof(tag_st)); }

    static constexpr uint16_t _bitWidth = NUM_TAGS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tag_st::_byteWidth);
        _ret = tagId;
    }
    inline void unpack(const _packedSt &_src)
    {
        tagId = (tag)((_src) & ((1ULL << 5) - 1));
    }
    explicit tag_st(
        tag tagId_) :
        tagId(tagId_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //SIMPLEINCLUDESFW_H_
