
#ifndef IPBRIDGEINCLUDESFW_H_
#define IPBRIDGEINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --project=ipBridge --context=../../yaml/ipBridge.yaml --mode=fw
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
typedef uint8_t bridgeMarkerT; // [1] 1-bit marker; bit-width matches ipDataSt::marker (packed-form compatibility)
typedef uint8_t data8T; // [8] Fixed 8-bit bridge payload (matches ipDataSt::data under variant0)
struct data70T { uint64_t word[ 2 ]; }; // [70] Fixed 70-bit bridge payload (matches ipDataSt::data under variant1)

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums
enum  addr_id_bridge {       //Generated type for addressing bridge instances
    ADDR_ID_BRIDGE_UBRIDGEIP0=0,   // uBridgeIp0 instance address
    ADDR_ID_BRIDGE_UBRIDGEIP1=1 }; // uBridgeIp1 instance address
inline const char* addr_id_bridge_prt( addr_id_bridge val )
{
    switch( val )
    {
        case ADDR_ID_BRIDGE_UBRIDGEIP0: return( "ADDR_ID_BRIDGE_UBRIDGEIP0" );
        case ADDR_ID_BRIDGE_UBRIDGEIP1: return( "ADDR_ID_BRIDGE_UBRIDGEIP1" );
    }
    return("!!!BADENUM!!!");
}

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct data8St {
    data8T data; //8-bit payload; matches ipDataSt::data under variant0
    bridgeMarkerT marker; //Marker bit; bit-width matches ipDataSt::marker

    data8St() { memset(this, 0, sizeof(data8St)); }

    static constexpr uint16_t _bitWidth = 8 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, data8St::_byteWidth);
        _ret = data;
        _ret |= (uint16_t)marker << (8 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (data8T)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
        _pos += 8;
        marker = (bridgeMarkerT)((_src >> (_pos & 15)) & 1);
    }
    explicit data8St(
        data8T data_,
        bridgeMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};
struct data70St {
    data70T data; //70-bit payload; matches ipDataSt::data under variant1
    bridgeMarkerT marker; //Marker bit; bit-width matches ipDataSt::marker

    data70St() { memset(this, 0, sizeof(data70St)); }

    static constexpr uint16_t _bitWidth = 70 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, data70St::_byteWidth);
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
        marker = (bridgeMarkerT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    explicit data70St(
        data70T data_,
        bridgeMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}

};

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //IPBRIDGEINCLUDESFW_H_
