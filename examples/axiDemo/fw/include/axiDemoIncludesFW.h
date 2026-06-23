
#ifndef AXIDEMOINCLUDESFW_H_
#define AXIDEMOINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=axiDemo.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
#include "axiStdIncludesFW.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t AXI_ADDRESS_WIDTH = 32;  // The width of the AXI address busses
const uint32_t AXI_DATA_WIDTH = 32;  // The width of the AXI data busses
const uint32_t AXI_STROBE_WIDTH = 4;  // The width of the AXI strobe signals

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint32_t axiAddrT; // [32] Address Width
typedef uint32_t axiDataT; // [32] Width of the data bus.
typedef uint8_t axiStrobeT; // [4] Width of the strobe bus.

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct axiAddrSt {
    axiAddrT addr; //

    axiAddrSt() { memset(this, 0, sizeof(axiAddrSt)); }

    static constexpr uint16_t _bitWidth = AXI_ADDRESS_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, axiAddrSt::_byteWidth);
        _ret = addr;
    }
    inline void unpack(const _packedSt &_src)
    {
        addr = (axiAddrT)((_src));
    }
    explicit axiAddrSt(
        axiAddrT addr_) :
        addr(addr_)
    {}

};
struct axiDataSt {
    axiDataT data; //

    axiDataSt() { memset(this, 0, sizeof(axiDataSt)); }

    static constexpr uint16_t _bitWidth = AXI_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, axiDataSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (axiDataT)((_src));
    }
    explicit axiDataSt(
        axiDataT data_) :
        data(data_)
    {}

};
struct axiStrobeSt {
    axiStrobeT strobe; //

    axiStrobeSt() { memset(this, 0, sizeof(axiStrobeSt)); }

    static constexpr uint16_t _bitWidth = AXI_STROBE_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, axiStrobeSt::_byteWidth);
        _ret = strobe;
    }
    inline void unpack(const _packedSt &_src)
    {
        strobe = (axiStrobeT)((_src) & ((1ULL << 4) - 1));
    }
    explicit axiStrobeSt(
        axiStrobeT strobe_) :
        strobe(strobe_)
    {}

};

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //AXIDEMOINCLUDESFW_H_
