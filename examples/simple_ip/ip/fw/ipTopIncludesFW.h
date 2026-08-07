
#ifndef IPTOPINCLUDESFW_H_
#define IPTOPINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=ip --context=../../yaml/ipTop.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
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
typedef uint8_t ipStdMarkerT; // [1] Boundary marker bit; matches ipDataSt::marker
typedef uint8_t ipStdData8T; // [8] Non-param 8-bit boundary payload; matches ipDataSt::data @variant0

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
namespace fw_ns {
// enums
enum  addr_id_ipstd {        //Generated type for addressing ipStd instances
    ADDR_ID_IPSTD_UIP=0 };   // uIp instance address
inline const char* addr_id_ipstd_prt( addr_id_ipstd val )
{
    switch( val )
    {
        case ADDR_ID_IPSTD_UIP: return( "ADDR_ID_IPSTD_UIP" );
    }
    return("!!!BADENUM!!!");
}

} // namespace fw_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
namespace fw_ns {
// structures
struct ipStdData8St {
    ipStdData8T data; //8-bit payload; matches ipDataSt::data @variant0
    ipStdMarkerT marker; //Marker bit; matches ipDataSt::marker

    ipStdData8St() { memset(this, 0, sizeof(ipStdData8St)); }

    static constexpr uint16_t _bitWidth = 8 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipStdData8St::_byteWidth);
        _ret = data;
        _ret |= (uint16_t)marker << (8 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (ipStdData8T)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
        _pos += 8;
        marker = (ipStdMarkerT)((_src >> (_pos & 15)) & 1);
    }
    explicit ipStdData8St(
        ipStdData8T data_,
        ipStdMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};
} // namespace fw_ns

// GENERATED_CODE_END
#endif //IPTOPINCLUDESFW_H_
