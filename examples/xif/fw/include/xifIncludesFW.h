
#ifndef XIFINCLUDESFW_H_
#define XIFINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --project=xif --context=xif.yaml --mode=fw
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
template<typename Config> using streamDataT = uint64_t; // [max:32] Parameterized stream payload word
typedef uint16_t streamBndryDataT; // [16] Non-parameterized boundary payload word (matches DATA_WIDTH=16)

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
template<typename Config>
struct streamSt {
    streamDataT<Config> data; //Parameterized stream payload

    streamSt() { memset(this, 0, sizeof(streamSt)); }

    static constexpr uint16_t _bitWidth = Config::DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, streamSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::DATA_WIDTH);
        _pos += Config::DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (streamDataT<Config>)((_src) & ((1ULL << (Config::DATA_WIDTH)) - 1));
    }
    explicit streamSt(
        streamDataT<Config> data_) :
        data(data_)
    {}

};
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

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //XIFINCLUDESFW_H_
