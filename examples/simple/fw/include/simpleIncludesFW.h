
#ifndef SIMPLEINCLUDESFW_H_
#define SIMPLEINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=simple.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
inline constexpr uint32_t NUM_TAGS = 32;  // number of tags
inline constexpr uint32_t NUM_TAGS_LOG2 = 5;  // log2 of number of tags

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint8_t tag; // [5] tag

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
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

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //SIMPLEINCLUDESFW_H_
