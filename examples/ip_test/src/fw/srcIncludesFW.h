
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
template<typename Config> using srcOut0DataT = uint64_t; // [max:16] src out0 data word, parameterizable
template<typename Config> struct srcOut1DataT { uint64_t word[ 2 ]; }; // [max:128] src out1 data word, parameterizable
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
template<typename Config>
struct srcOut0St {
    srcOut0DataT<Config> data; //src out0 payload
    srcMarkerT marker; //marker bit copied through the thunker

    srcOut0St() { memset(this, 0, sizeof(srcOut0St)); }

    static constexpr uint16_t _bitWidth = Config::OUT0_DATA_WIDTH + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, srcOut0St<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::OUT0_DATA_WIDTH);
        _pos += Config::OUT0_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, marker, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (srcOut0DataT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::OUT0_DATA_WIDTH)) - 1));
        _pos += Config::OUT0_DATA_WIDTH;
        marker = (srcMarkerT)((_src >> (_pos & 63)) & 1);
    }
    explicit srcOut0St(
        srcOut0DataT<Config> data_,
        srcMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};
template<typename Config>
struct srcOut1St {
    srcOut1DataT<Config> data; //src out1 payload
    srcMarkerT marker; //marker bit above bit 64 for the 70-bit variant

    srcOut1St() { memset(this, 0, sizeof(srcOut1St)); }

    static constexpr uint16_t _bitWidth = Config::OUT1_DATA_WIDTH + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, srcOut1St<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&data, Config::OUT1_DATA_WIDTH);
        _pos += Config::OUT1_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, marker, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&data, 0, sizeof(data));
        unpack_bits((uint64_t *)&data, 0, (uint64_t *)&_src, _pos, Config::OUT1_DATA_WIDTH);
        _pos += Config::OUT1_DATA_WIDTH;
        marker = (srcMarkerT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    explicit srcOut1St(
        srcOut1DataT<Config> data_,
        srcMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //SRCINCLUDESFW_H_
