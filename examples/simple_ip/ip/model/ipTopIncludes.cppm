
// GENERATED_CODE_PARAM --project=ip --context=../../yaml/ipTop.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module ip_ipTop;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import ip;
using namespace ip_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_ipTop_ns {
//constants

} // namespace ip_ipTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_ipTop_ns {
// types
typedef uint8_t ipStdMarkerT; // [1] Boundary marker bit; matches ipDataSt::marker
typedef uint8_t ipStdData8T; // [8] Non-param 8-bit boundary payload; matches ipDataSt::data @variant0

} // namespace ip_ipTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_ipTop_ns {
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

} // namespace ip_ipTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ip_ipTop_ns {
// structures
struct ipStdData8St {
    ipStdData8T data; //8-bit payload; matches ipDataSt::data @variant0
    ipStdMarkerT marker; //Marker bit; matches ipDataSt::marker

    ipStdData8St() {}

    static constexpr uint16_t _bitWidth = 8 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const ipStdData8St & rhs) const {
        bool ret = true;
        ret = ret && (marker == rhs.marker);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipStdData8St & v, const std::string & NAME ) {
        sc_trace(tf,v.marker, NAME + ".marker");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  ipStdData8St const & v ) {
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
    inline sc_bv<ipStdData8St::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipStdData8St::_bitWidth> packed_data;
        packed_data.range(7, 0) = data;
        packed_data.range(8, 8) = marker;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipStdData8St::_bitWidth> packed_data)
    {
        data = (ipStdData8T) packed_data.range(7, 0).to_uint64();
        marker = (ipStdMarkerT) packed_data.range(8, 8).to_uint64();
    }
    explicit ipStdData8St(sc_bv<ipStdData8St::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipStdData8St(
        ipStdData8T data_,
        ipStdMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit ipStdData8St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace ip_ipTop_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ip_ipTop_test_ns {
class test_ipTop_structs {
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
} // namespace ip_ipTop_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ip_ipTop_test_ns {
using namespace ip_ipTop_ns;
std::string test_ipTop_structs::name(void) { return "test_ipTop_structs"; }
void test_ipTop_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<ipStdData8St>("ipStdData8St", patterns);
}
} // namespace ip_ipTop_test_ns

// GENERATED_CODE_END
