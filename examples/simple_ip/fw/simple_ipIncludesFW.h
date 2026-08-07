
#ifndef SIMPLE_IPINCLUDESFW_H_
#define SIMPLE_IPINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=simple_ip --context=../../yaml/simple_ip.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
#include "shared_typesIncludesFW.h"
#include "ipIncludesFW.h"
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
typedef uint8_t simpleMarkerT; // [1] Boundary marker bit; matches ipDataSt::marker
typedef uint8_t simpleData8T; // [8] 8-bit boundary payload; matches ipDataSt::data @variant0

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
namespace fw_ns {
// enums
enum  addr_id_top {          //Generated type for addressing top instances
    ADDR_ID_TOP_UIP=0 };     // uIp instance address
inline const char* addr_id_top_prt( addr_id_top val )
{
    switch( val )
    {
        case ADDR_ID_TOP_UIP: return( "ADDR_ID_TOP_UIP" );
    }
    return("!!!BADENUM!!!");
}

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
namespace fw_ns {
// structures
struct simpleData8St {
    simpleData8T data; //8-bit payload @variant0
    simpleMarkerT marker; //marker bit

    simpleData8St() { memset(this, 0, sizeof(simpleData8St)); }

    static constexpr uint16_t _bitWidth = 8 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, simpleData8St::_byteWidth);
        _ret = data;
        _ret |= (uint16_t)marker << (8 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (simpleData8T)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
        _pos += 8;
        marker = (simpleMarkerT)((_src >> (_pos & 15)) & 1);
    }
    explicit simpleData8St(
        simpleData8T data_,
        simpleMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //SIMPLE_IPINCLUDESFW_H_
