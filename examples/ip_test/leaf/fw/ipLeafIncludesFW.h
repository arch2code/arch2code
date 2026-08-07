
#ifndef IPLEAFINCLUDESFW_H_
#define IPLEAFINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=ip_test --context=../../leaf/yaml/ipLeaf.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
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
template<typename Config> using ipLeafMemAddrT = uint64_t; // [max:3] Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)
template<typename Config> using ipLeafDataT = uint64_t; // [max:16] ipLeaf data word, parameterizable

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
struct ipLeafMemSt {
    ipLeafDataT<Config> data; //Leaf memory word

    ipLeafMemSt() { memset(this, 0, sizeof(ipLeafMemSt)); }

    static constexpr uint16_t _bitWidth = Config::LEAF_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipLeafMemSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::LEAF_DATA_WIDTH);
        _pos += Config::LEAF_DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (ipLeafDataT<Config>)((_src) & ((1ULL << (Config::LEAF_DATA_WIDTH)) - 1));
    }
    explicit ipLeafMemSt(
        ipLeafDataT<Config> data_) :
        data(data_)
    {}

};
template<typename Config>
struct ipLeafMemAddrSt {
    ipLeafMemAddrT<Config> address; //Leaf memory address

    ipLeafMemAddrSt() { memset(this, 0, sizeof(ipLeafMemAddrSt)); }

    static constexpr uint16_t _bitWidth = clog2(Config::LEAF_MEM_DEPTH);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipLeafMemAddrSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, address, clog2(Config::LEAF_MEM_DEPTH));
        _pos += clog2(Config::LEAF_MEM_DEPTH);
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ipLeafMemAddrT<Config>)((_src) & ((1ULL << (clog2(Config::LEAF_MEM_DEPTH))) - 1));
    }
    explicit ipLeafMemAddrSt(
        ipLeafMemAddrT<Config> address_) :
        address(address_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //IPLEAFINCLUDESFW_H_
