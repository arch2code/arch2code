
#ifndef IPLEAFINCLUDESFW_H_
#define IPLEAFINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=ip_test --context=../../leaf/yaml/ipLeaf.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
namespace fw_ns::ip_test_ipLeaf {}
namespace fw_ns { using namespace ip_test_ipLeaf; }
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <cstdint>
#include <cstring>
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
namespace fw_ns::ip_test_ipLeaf {
//constants

} // namespace fw_ns::ip_test_ipLeaf
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
namespace fw_ns::ip_test_ipLeaf {
// types
template<uint32_t LEAF_MEM_DEPTH> using ipLeafMemAddrT_v = uint64_t; // [max:3] Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)
template<typename Config> using ipLeafMemAddrT = ipLeafMemAddrT_v<Config::LEAF_MEM_DEPTH>;
template<uint32_t LEAF_DATA_WIDTH> using ipLeafDataT_v = uint64_t; // [max:16] ipLeaf data word, parameterizable
template<typename Config> using ipLeafDataT = ipLeafDataT_v<Config::LEAF_DATA_WIDTH>;

} // namespace fw_ns::ip_test_ipLeaf
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
namespace fw_ns::ip_test_ipLeaf {
// enums

} // namespace fw_ns::ip_test_ipLeaf
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
namespace fw_ns::ip_test_ipLeaf {
// structures
template<uint32_t LEAF_DATA_WIDTH>
struct ipLeafMemSt_v {
    ipLeafDataT_v<LEAF_DATA_WIDTH> data; //Leaf memory word

    ipLeafMemSt_v() { memset(this, 0, sizeof(ipLeafMemSt_v)); }

    static constexpr uint16_t _bitWidth = LEAF_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipLeafMemSt_v<LEAF_DATA_WIDTH>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, LEAF_DATA_WIDTH);
        _pos += LEAF_DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (ipLeafDataT_v<LEAF_DATA_WIDTH>)((_src) & ((1ULL << (LEAF_DATA_WIDTH)) - 1));
    }
    explicit ipLeafMemSt_v(
        ipLeafDataT_v<LEAF_DATA_WIDTH> data_) :
        data(data_)
    {}

};
template<typename Config> using ipLeafMemSt = ipLeafMemSt_v<Config::LEAF_DATA_WIDTH>;
template<uint32_t LEAF_MEM_DEPTH>
struct ipLeafMemAddrSt_v {
    ipLeafMemAddrT_v<LEAF_MEM_DEPTH> address; //Leaf memory address

    ipLeafMemAddrSt_v() { memset(this, 0, sizeof(ipLeafMemAddrSt_v)); }

    static constexpr uint16_t _bitWidth = clog2(LEAF_MEM_DEPTH);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, address, clog2(LEAF_MEM_DEPTH));
        _pos += clog2(LEAF_MEM_DEPTH);
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ipLeafMemAddrT_v<LEAF_MEM_DEPTH>)((_src) & ((1ULL << (clog2(LEAF_MEM_DEPTH))) - 1));
    }
    explicit ipLeafMemAddrSt_v(
        ipLeafMemAddrT_v<LEAF_MEM_DEPTH> address_) :
        address(address_)
    {}

};
template<typename Config> using ipLeafMemAddrSt = ipLeafMemAddrSt_v<Config::LEAF_MEM_DEPTH>;
} // namespace fw_ns::ip_test_ipLeaf

// GENERATED_CODE_END
#endif //IPLEAFINCLUDESFW_H_
