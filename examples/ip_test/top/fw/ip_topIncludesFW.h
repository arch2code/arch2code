
#ifndef IP_TOPINCLUDESFW_H_
#define IP_TOPINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --project=ip_test --context=../../top/yaml/ip_top.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
#include "shared_typesIncludesFW.h"
#include "srcIncludesFW.h"
#include "ipLeafIncludesFW.h"
#include "ipIncludesFW.h"
#include "ipBridgeIncludesFW.h"
#include "bitTwiddling.h"

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
typedef uint8_t boundaryMarkerT; // [1] Boundary marker bit; matches srcOut*St::marker and ipDataSt::marker
typedef uint8_t srcOut0BoundaryT; // [8] Non-param 8-bit boundary payload; matches uSrc OUT0_DATA_WIDTH=8 / uIp0 IP_DATA_WIDTH=8
struct srcOut1BoundaryT { uint64_t word[ 2 ]; }; // [70] Non-param 70-bit boundary payload; matches uSrc OUT1_DATA_WIDTH=70 / uIp1 IP_DATA_WIDTH=70

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums
enum  addr_id_top {          //Generated type for addressing top instances
    ADDR_ID_TOP_UIP0=0,      // uIp0 instance address
    ADDR_ID_TOP_UIP1=1,      // uIp1 instance address
    ADDR_ID_TOP_UBRIDGE=2 }; // uBridge instance address
inline const char* addr_id_top_prt( addr_id_top val )
{
    switch( val )
    {
        case ADDR_ID_TOP_UIP0: return( "ADDR_ID_TOP_UIP0" );
        case ADDR_ID_TOP_UIP1: return( "ADDR_ID_TOP_UIP1" );
        case ADDR_ID_TOP_UBRIDGE: return( "ADDR_ID_TOP_UBRIDGE" );
    }
    return("!!!BADENUM!!!");
}

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct srcOut0BoundarySt {
    srcOut0BoundaryT data; //8-bit payload; matches srcOut0St::data@variantSrc0 and ipDataSt::data@variant0
    boundaryMarkerT marker; //Marker bit; matches srcOut0St::marker / ipDataSt::marker

    srcOut0BoundarySt() { memset(this, 0, sizeof(srcOut0BoundarySt)); }

    static constexpr uint16_t _bitWidth = 8 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, srcOut0BoundarySt::_byteWidth);
        _ret = data;
        _ret |= (uint16_t)marker << (8 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (srcOut0BoundaryT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
        _pos += 8;
        marker = (boundaryMarkerT)((_src >> (_pos & 15)) & 1);
    }
    explicit srcOut0BoundarySt(
        srcOut0BoundaryT data_,
        boundaryMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};
struct srcOut1BoundarySt {
    srcOut1BoundaryT data; //70-bit payload; matches srcOut1St::data@variantSrc0 and ipDataSt::data@variant1
    boundaryMarkerT marker; //Marker bit; matches srcOut1St::marker / ipDataSt::marker

    srcOut1BoundarySt() { memset(this, 0, sizeof(srcOut1BoundarySt)); }

    static constexpr uint16_t _bitWidth = 70 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, srcOut1BoundarySt::_byteWidth);
        pack_bits((uint64_t *)&_ret, 0, (uint64_t *)&data, 70);
        _ret[ 1 ] |= ((uint64_t)marker << (70 & 63));
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data.word[0] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        data.word[1] = ((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 6) - 1));
        _pos += 6;
        marker = (boundaryMarkerT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    explicit srcOut1BoundarySt(
        srcOut1BoundaryT data_,
        boundaryMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //IP_TOPINCLUDESFW_H_
