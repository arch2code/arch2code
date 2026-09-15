
#ifndef XPRTINHINCLUDESFW_H_
#define XPRTINHINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=xpRtInh --context=../../yaml/xpRtInh.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
#include "shared_typesIncludesFW.h"

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
template<uint32_t RT_WIDTH> using cfgDataT_v = uint64_t; // [max:32] xpRtLeaf configuration payload
template<typename Config> using cfgDataT = cfgDataT_v<Config::RT_WIDTH>;

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
namespace fw_ns {
// enums
enum  addr_id_xpRtInhTop {   //Generated type for addressing top instances
    ADDR_ID_XPRTINHTOP_UWRAP=0 }; // uWrap instance address
inline const char* addr_id_xpRtInhTop_prt( addr_id_xpRtInhTop val )
{
    switch( val )
    {
        case ADDR_ID_XPRTINHTOP_UWRAP: return( "ADDR_ID_XPRTINHTOP_UWRAP" );
    }
    return("!!!BADENUM!!!");
}
enum  addr_id_xpRtWrap {     //Generated type for addressing wrap instances
    ADDR_ID_XPRTWRAP_ULEAF=0 }; // uLeaf instance address
inline const char* addr_id_xpRtWrap_prt( addr_id_xpRtWrap val )
{
    switch( val )
    {
        case ADDR_ID_XPRTWRAP_ULEAF: return( "ADDR_ID_XPRTWRAP_ULEAF" );
    }
    return("!!!BADENUM!!!");
}

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
namespace fw_ns {
// structures
template<uint32_t RT_WIDTH>
struct cfgSt_v {
    cfgDataT_v<RT_WIDTH> value; //xpRtLeaf configuration value

    cfgSt_v() { memset(this, 0, sizeof(cfgSt_v)); }

    static constexpr uint16_t _bitWidth = RT_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, cfgSt_v<RT_WIDTH>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, value, RT_WIDTH);
        _pos += RT_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (cfgDataT_v<RT_WIDTH>)((_src) & ((1ULL << (RT_WIDTH)) - 1));
    }
    explicit cfgSt_v(
        cfgDataT_v<RT_WIDTH> value_) :
        value(value_)
    {}

};
template<typename Config> using cfgSt = cfgSt_v<Config::RT_WIDTH>;
} // namespace fw_ns

// GENERATED_CODE_END
#endif //XPRTINHINCLUDESFW_H_
