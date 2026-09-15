
#ifndef XIFINCLUDESFW_H_
#define XIFINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=xif --context=xif.yaml --mode=fw
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
template<uint32_t DATA_WIDTH> using streamDataT_v = uint64_t; // [max:32] Parameterized stream payload word
template<typename Config> using streamDataT = streamDataT_v<Config::DATA_WIDTH>;
typedef uint16_t streamBndryDataT; // [16] Non-parameterized boundary payload word (matches DATA_WIDTH=16)

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
template<uint32_t DATA_WIDTH>
struct streamSt_v {
    streamDataT_v<DATA_WIDTH> data; //Parameterized stream payload

    streamSt_v() { memset(this, 0, sizeof(streamSt_v)); }

    static constexpr uint16_t _bitWidth = DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, streamSt_v<DATA_WIDTH>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, DATA_WIDTH);
        _pos += DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (streamDataT_v<DATA_WIDTH>)((_src) & ((1ULL << (DATA_WIDTH)) - 1));
    }
    explicit streamSt_v(
        streamDataT_v<DATA_WIDTH> data_) :
        data(data_)
    {}

};
template<typename Config> using streamSt = streamSt_v<Config::DATA_WIDTH>;
struct streamBndrySt {
    streamBndryDataT data; //Boundary payload; packed layout matches streamSt<dutV0>

    streamBndrySt() { memset(this, 0, sizeof(streamBndrySt)); }

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, streamBndrySt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (streamBndryDataT)((_src));
    }
    explicit streamBndrySt(
        streamBndryDataT data_) :
        data(data_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //XIFINCLUDESFW_H_
