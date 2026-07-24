
#ifndef SIMPLE_IPINCLUDESFW_H_
#define SIMPLE_IPINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=../../yaml/simple_ip.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
#include "shared_typesIncludesFW.h"
#include "ipIncludesFW.h"
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
typedef uint8_t simpleMarkerT; // [1] Boundary marker bit; matches ipDataSt::marker
typedef uint8_t simpleData8T; // [8] 8-bit boundary payload; matches ipDataSt::data @variant0

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
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

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
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

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //SIMPLE_IPINCLUDESFW_H_
