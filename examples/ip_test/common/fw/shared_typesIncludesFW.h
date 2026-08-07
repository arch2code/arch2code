
#ifndef SHARED_TYPESINCLUDESFW_H_
#define SHARED_TYPESINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=common --context=../../yaml/shared_types.yaml --mode=fw
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
inline constexpr uint32_t DWORD = 32;  // Width of an APB dword

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
namespace fw_ns {
// types
typedef uint32_t apbAddrT; // [32] APB address
typedef uint32_t apbDataT; // [32] APB data

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
struct apbAddrSt {
    apbAddrT address; //

    apbAddrSt() { memset(this, 0, sizeof(apbAddrSt)); }

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, apbAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (apbAddrT)((_src));
    }
    explicit apbAddrSt(
        apbAddrT address_) :
        address(address_)
    {}

};
struct apbDataSt {
    apbDataT data; //

    apbDataSt() { memset(this, 0, sizeof(apbDataSt)); }

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, apbDataSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (apbDataT)((_src));
    }
    explicit apbDataSt(
        apbDataT data_) :
        data(data_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //SHARED_TYPESINCLUDESFW_H_
