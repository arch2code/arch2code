
// GENERATED_CODE_PARAM --context=ipBridge.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module ipBridge;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ipBridge_ns {
//constants

} // namespace ipBridge_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ipBridge_ns {
// types
typedef uint8_t bridgeMarkerT; // [1] Stage 8.2 1-bit marker; bit-width matches ipDataSt::marker (Stage 6.2 packed-form compatibility)
typedef uint8_t data8T; // [8] Stage 8.2 fixed 8-bit Q10-bridge payload (matches ipDataSt::data under variant0)
struct data70T { uint64_t word[ 2 ]; }; // [70] Stage 8.2 fixed 70-bit Q10-bridge payload (matches ipDataSt::data under variant1)

} // namespace ipBridge_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ipBridge_ns {
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

} // namespace ipBridge_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ipBridge_ns {
// structures
struct data8St {
    data8T data; //8-bit payload; matches ipDataSt::data under variant0
    bridgeMarkerT marker; //Marker bit; bit-width matches ipDataSt::marker

    data8St() {}

    static constexpr uint16_t _bitWidth = 8 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const data8St & rhs) const {
        bool ret = true;
        ret = ret && (marker == rhs.marker);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const data8St & v, const std::string & NAME ) {
        sc_trace(tf,v.marker, NAME + ".marker");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  data8St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("marker:0x{:01x} data:0x{:02x}",
           (uint64_t) marker,
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
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
    inline sc_bv<data8St::_bitWidth> sc_pack(void) const
    {
        sc_bv<data8St::_bitWidth> packed_data;
        packed_data.range(7, 0) = data;
        packed_data.range(8, 8) = marker;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<data8St::_bitWidth> packed_data)
    {
        data = (data8T) packed_data.range(7, 0).to_uint64();
        marker = (bridgeMarkerT) packed_data.range(8, 8).to_uint64();
    }
    explicit data8St(sc_bv<data8St::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit data8St(
        data8T data_,
        bridgeMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit data8St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct data70St {
    data70T data; //70-bit payload; matches ipDataSt::data under variant1
    bridgeMarkerT marker; //Marker bit; bit-width matches ipDataSt::marker

    data70St() {}

    static constexpr uint16_t _bitWidth = 70 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const data70St & rhs) const {
        bool ret = true;
        ret = ret && (marker == rhs.marker);
        ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
        ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const data70St & v, const std::string & NAME ) {
        sc_trace(tf,v.marker, NAME + ".marker");
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  data70St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("marker:0x{:01x} data:0x{:02x}{:016x}",
           (uint64_t) marker,
           data.word[1],
           data.word[0]
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
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
    inline sc_bv<data70St::_bitWidth> sc_pack(void) const
    {
        sc_bv<data70St::_bitWidth> packed_data;
        packed_data.range(63, 0) = data.word[0];
        packed_data.range(69, 64) = data.word[1];
        packed_data.range(70, 70) = marker;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<data70St::_bitWidth> packed_data)
    {
        data.word[0] = (uint64_t) packed_data.range(63, 0).to_uint64();
        data.word[1] = (uint64_t) packed_data.range(69, 64).to_uint64();
        marker = (bridgeMarkerT) packed_data.range(70, 70).to_uint64();
    }
    explicit data70St(sc_bv<data70St::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit data70St(
        data70T data_,
        bridgeMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit data70St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace ipBridge_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ipBridge_ns {
template<typename Config>
class test_ipBridge_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace ipBridge_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ipBridge_ns {
template<typename Config>
std::string test_ipBridge_structs<Config>::name(void) { return "test_ipBridge_structs"; }
template<typename Config>
void test_ipBridge_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        data8St::_packedSt packed;
        memset(&packed, pattern, data8St::_byteWidth);
        sc_bv<data8St::_bitWidth> aInit;
        sc_bv<data8St::_bitWidth> aTest;
        for (int i = 0; i < data8St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, data8St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        data8St a;
        a.sc_unpack(aInit);
        data8St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"data8St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"data8St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = data8St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"data8St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        data70St::_packedSt packed;
        memset(&packed, pattern, data70St::_byteWidth);
        sc_bv<data70St::_bitWidth> aInit;
        sc_bv<data70St::_bitWidth> aTest;
        for (int i = 0; i < data70St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, data70St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        data70St a;
        a.sc_unpack(aInit);
        data70St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"data70St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"data70St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = data70St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"data70St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace ipBridge_ns

// GENERATED_CODE_END
