
#ifndef COREINCLUDESFW_H_
#define COREINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --project=hier --context=../../core/yaml/core.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
namespace fw_ns::hier_core {}
namespace fw_ns { using namespace hier_core; }

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <cstdint>
#include <cstring>
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
namespace fw_ns::hier_core {
//constants
inline constexpr uint32_t W = 8;  // data width

} // namespace fw_ns::hier_core
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
namespace fw_ns::hier_core {
// types
typedef uint8_t dat; // [8] data word

} // namespace fw_ns::hier_core
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
namespace fw_ns::hier_core {
// enums

} // namespace fw_ns::hier_core
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
namespace fw_ns::hier_core {
// structures
struct dat_st {
    dat d; /* [7:0] */ //data

    dat_st() { memset(this, 0, sizeof(dat_st)); }

    static constexpr uint16_t _bitWidth = W;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, dat_st::_byteWidth);
        _ret = d;
    }
    inline void unpack(const _packedSt &_src)
    {
        d = (dat)((_src));
    }
    explicit dat_st(
        dat d_) :
        d(d_)
    {}

};
} // namespace fw_ns::hier_core

// GENERATED_CODE_END
#endif //COREINCLUDESFW_H_
