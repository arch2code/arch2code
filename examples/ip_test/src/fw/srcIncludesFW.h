
#ifndef SRCINCLUDESFW_H_
#define SRCINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=ip_test --context=../../src/yaml/src.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
#include "ipLeafIncludesFW.h"
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

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
namespace fw_ns {
// types
template<uint32_t OUT0_DATA_WIDTH> using srcOut0DataT_v = uint64_t; // [max:16] src out0 data word, parameterizable
template<typename Config> using srcOut0DataT = srcOut0DataT_v<Config::OUT0_DATA_WIDTH>;
template<uint32_t OUT1_DATA_WIDTH> struct srcOut1DataT_v { uint64_t word[ 2 ]; }; // [max:128] src out1 data word, parameterizable
template<typename Config> using srcOut1DataT = srcOut1DataT_v<Config::OUT1_DATA_WIDTH>;
typedef uint8_t srcMarkerT; // [1] src high-word marker bit

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
template<uint32_t OUT0_DATA_WIDTH>
struct srcOut0St_v {
    srcOut0DataT_v<OUT0_DATA_WIDTH> data; //src out0 payload
    srcMarkerT marker; //marker bit copied through the thunker

    srcOut0St_v() { memset(this, 0, sizeof(srcOut0St_v)); }

    static constexpr uint16_t _bitWidth = OUT0_DATA_WIDTH + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, srcOut0St_v<OUT0_DATA_WIDTH>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, OUT0_DATA_WIDTH);
        _pos += OUT0_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, marker, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (srcOut0DataT_v<OUT0_DATA_WIDTH>)((_src >> (_pos & 63)) & ((1ULL << (OUT0_DATA_WIDTH)) - 1));
        _pos += OUT0_DATA_WIDTH;
        marker = (srcMarkerT)((_src >> (_pos & 63)) & 1);
    }
    explicit srcOut0St_v(
        srcOut0DataT_v<OUT0_DATA_WIDTH> data_,
        srcMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};
template<typename Config> using srcOut0St = srcOut0St_v<Config::OUT0_DATA_WIDTH>;
template<uint32_t OUT1_DATA_WIDTH>
struct srcOut1St_v {
    srcOut1DataT_v<OUT1_DATA_WIDTH> data; //src out1 payload
    srcMarkerT marker; //marker bit above bit 64 for the 70-bit variant

    srcOut1St_v() { memset(this, 0, sizeof(srcOut1St_v)); }

    static constexpr uint16_t _bitWidth = OUT1_DATA_WIDTH + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, srcOut1St_v<OUT1_DATA_WIDTH>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&data, OUT1_DATA_WIDTH);
        _pos += OUT1_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, marker, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&data, 0, sizeof(data));
        unpack_bits((uint64_t *)&data, 0, (uint64_t *)&_src, _pos, OUT1_DATA_WIDTH);
        _pos += OUT1_DATA_WIDTH;
        marker = (srcMarkerT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    explicit srcOut1St_v(
        srcOut1DataT_v<OUT1_DATA_WIDTH> data_,
        srcMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};
template<typename Config> using srcOut1St = srcOut1St_v<Config::OUT1_DATA_WIDTH>;
} // namespace fw_ns

// GENERATED_CODE_END
#endif //SRCINCLUDESFW_H_
