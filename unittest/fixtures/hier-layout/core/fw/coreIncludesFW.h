
#ifndef COREINCLUDESFW_H_
#define COREINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=../../core/yaml/core.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t W = 8;  // data width

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint8_t dat; // [8] data word

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct dat_st {
    dat d; //data

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

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //COREINCLUDESFW_H_
