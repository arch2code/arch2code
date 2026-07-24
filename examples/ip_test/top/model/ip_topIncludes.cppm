
// GENERATED_CODE_PARAM --context=../../top/yaml/ip_top.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module ip_top;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import shared_types;
import src;
import ipLeaf;
import ip;
import ipBridge;
using namespace shared_types_ns;
using namespace src_ns;
using namespace ipLeaf_ns;
using namespace ip_ns;
using namespace ipBridge_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_top_ns {
//constants

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_top_ns {
// types
typedef uint8_t boundaryMarkerT; // [1] Boundary marker bit; matches srcOut*St::marker and ipDataSt::marker
typedef uint8_t srcOut0BoundaryT; // [8] Non-param 8-bit boundary payload; matches uSrc OUT0_DATA_WIDTH=8 / uIp0 IP_DATA_WIDTH=8
struct srcOut1BoundaryT { uint64_t word[ 2 ]; }; // [70] Non-param 70-bit boundary payload; matches uSrc OUT1_DATA_WIDTH=70 / uIp1 IP_DATA_WIDTH=70

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_top_ns {
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

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ip_top_ns {
// structures
struct srcOut0BoundarySt {
    srcOut0BoundaryT data; //8-bit payload; matches srcOut0St::data@variantSrc0 and ipDataSt::data@variant0
    boundaryMarkerT marker; //Marker bit; matches srcOut0St::marker / ipDataSt::marker

    srcOut0BoundarySt() {}

    static constexpr uint16_t _bitWidth = 8 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const srcOut0BoundarySt & rhs) const {
        bool ret = true;
        ret = ret && (marker == rhs.marker);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const srcOut0BoundarySt & v, const std::string & NAME ) {
        sc_trace(tf,v.marker, NAME + ".marker");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  srcOut0BoundarySt const & v ) {
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
    inline sc_bv<srcOut0BoundarySt::_bitWidth> sc_pack(void) const
    {
        sc_bv<srcOut0BoundarySt::_bitWidth> packed_data;
        packed_data.range(7, 0) = data;
        packed_data.range(8, 8) = marker;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<srcOut0BoundarySt::_bitWidth> packed_data)
    {
        data = (srcOut0BoundaryT) packed_data.range(7, 0).to_uint64();
        marker = (boundaryMarkerT) packed_data.range(8, 8).to_uint64();
    }
    explicit srcOut0BoundarySt(sc_bv<srcOut0BoundarySt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit srcOut0BoundarySt(
        srcOut0BoundaryT data_,
        boundaryMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit srcOut0BoundarySt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct srcOut1BoundarySt {
    srcOut1BoundaryT data; //70-bit payload; matches srcOut1St::data@variantSrc0 and ipDataSt::data@variant1
    boundaryMarkerT marker; //Marker bit; matches srcOut1St::marker / ipDataSt::marker

    srcOut1BoundarySt() {}

    static constexpr uint16_t _bitWidth = 70 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const srcOut1BoundarySt & rhs) const {
        bool ret = true;
        ret = ret && (marker == rhs.marker);
        ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
        ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const srcOut1BoundarySt & v, const std::string & NAME ) {
        sc_trace(tf,v.marker, NAME + ".marker");
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  srcOut1BoundarySt const & v ) {
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
    inline sc_bv<srcOut1BoundarySt::_bitWidth> sc_pack(void) const
    {
        sc_bv<srcOut1BoundarySt::_bitWidth> packed_data;
        packed_data.range(63, 0) = data.word[0];
        packed_data.range(69, 64) = data.word[1];
        packed_data.range(70, 70) = marker;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<srcOut1BoundarySt::_bitWidth> packed_data)
    {
        data.word[0] = (uint64_t) packed_data.range(63, 0).to_uint64();
        data.word[1] = (uint64_t) packed_data.range(69, 64).to_uint64();
        marker = (boundaryMarkerT) packed_data.range(70, 70).to_uint64();
    }
    explicit srcOut1BoundarySt(sc_bv<srcOut1BoundarySt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit srcOut1BoundarySt(
        srcOut1BoundaryT data_,
        boundaryMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit srcOut1BoundarySt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace ip_top_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ip_top_test_ns {
class test_ip_top_structs {
public:
    static std::string name(void);
    static void test(void);
private:
    template<typename T>
    static void roundTrip(const char* sName, const std::vector<uint8_t>& patterns) {
        for(auto pattern : patterns) {
            typename T::_packedSt packed;
            memset(&packed, pattern, T::_byteWidth);
            sc_bv<T::_bitWidth> aInit;
            sc_bv<T::_bitWidth> aTest;
            for (int i = 0; i < T::_byteWidth; i++) {
                int end = std::min((i+1)*8-1, T::_bitWidth-1);
                aInit.range(end, i*8) = pattern;
            }
            T a;
            a.sc_unpack(aInit);
            T b;
            b.unpack(packed);
            if (!(b == a)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false, sName);
            }
            uint64_t test;
            memset(&test, pattern, 8);
            b.pack(packed);
            aTest = a.sc_pack();
            if (!(aTest == aInit)) {;
                cout << a.prt();
                cout << aTest;
                Q_ASSERT(false, sName);
            }
            uint64_t *ptr = (uint64_t *)&packed;
            uint16_t bitsLeft = T::_bitWidth;
            do {
                int bits = std::min((uint16_t)64, bitsLeft);
                uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
                if ((*ptr & mask) != (test & mask)) {;
                    cout << a.prt();
                    cout << b.prt();
                    Q_ASSERT(false, sName);
                }
                bitsLeft -= bits;
                ptr++;
            } while(bitsLeft > 0);
        }
    }
};
} // namespace ip_top_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ip_top_test_ns {
using namespace ip_top_ns;
std::string test_ip_top_structs::name(void) { return "test_ip_top_structs"; }
void test_ip_top_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<srcOut0BoundarySt>("srcOut0BoundarySt", patterns);
    roundTrip<srcOut1BoundarySt>("srcOut1BoundarySt", patterns);
}
} // namespace ip_top_test_ns

// GENERATED_CODE_END
