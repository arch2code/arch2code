
// GENERATED_CODE_PARAM --project=ip_test --context=../../top/yaml/ip_top.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module ip_test_ip_top;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import common_shared_types;
import ip_test_src;
import ip_test_ipLeaf;
import ip;
import ipBridge;
using namespace common_shared_types_ns;
using namespace ip_test_src_ns;
using namespace ip_test_ipLeaf_ns;
using namespace ip_ns;
using namespace ipBridge_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_test_ip_top_ns {
//constants

} // namespace ip_test_ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_test_ip_top_ns {
// types
typedef uint8_t boundaryMarkerT; // [1] Boundary marker bit; matches srcOut*St::marker and ipDataSt::marker
typedef uint8_t srcOut0BoundaryT; // [8] Non-param 8-bit boundary payload; matches uSrc OUT0_DATA_WIDTH=8 / uIp0 IP_DATA_WIDTH=8
struct srcOut1BoundaryT { uint64_t word[ 2 ]; }; // [70] Non-param 70-bit boundary payload; matches uSrc OUT1_DATA_WIDTH=70 / uIp1 IP_DATA_WIDTH=70

} // namespace ip_test_ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_test_ip_top_ns {
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

} // namespace ip_test_ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ip_test_ip_top_ns {
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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "srcOut0BoundarySt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<srcOut0BoundarySt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit srcOut0BoundarySt(const sc_bv<srcOut0BoundarySt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)(_packed[i >> 1] >> ((i & 1) * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "srcOut1BoundarySt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<srcOut1BoundarySt::_bitWidth> &packed_data)
    {
        _packedSt _words{};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _words[i >> 1] |= (uint64_t)packed_data.get_word(i) << ((i & 1) * 32);
        }
        unpack(_words);
    }
    explicit srcOut1BoundarySt(const sc_bv<srcOut1BoundarySt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit srcOut1BoundarySt(
        srcOut1BoundaryT data_,
        boundaryMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit srcOut1BoundarySt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace ip_test_ip_top_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ip_test_ip_top_ns {
inline sc_bv<srcOut0BoundarySt::_bitWidth> testRefPack(const srcOut0BoundarySt &x);
inline void testRefUnpack(srcOut0BoundarySt &x, const sc_bv<srcOut0BoundarySt::_bitWidth> &packed_data);
inline sc_bv<srcOut1BoundarySt::_bitWidth> testRefPack(const srcOut1BoundarySt &x);
inline void testRefUnpack(srcOut1BoundarySt &x, const sc_bv<srcOut1BoundarySt::_bitWidth> &packed_data);
inline sc_bv<srcOut0BoundarySt::_bitWidth> testRefPack(const srcOut0BoundarySt &x)
{
    sc_bv<srcOut0BoundarySt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.data;
    packed_data.range(8+1-1, 8) = x.marker;
    return packed_data;
}
inline void testRefUnpack(srcOut0BoundarySt &x, const sc_bv<srcOut0BoundarySt::_bitWidth> &packed_data)
{
    x.data = (srcOut0BoundaryT) packed_data.range(0+8-1, 0).to_uint64();
    x.marker = (boundaryMarkerT) packed_data.range(8+1-1, 8).to_uint64();
}
inline sc_bv<srcOut1BoundarySt::_bitWidth> testRefPack(const srcOut1BoundarySt &x)
{
    sc_bv<srcOut1BoundarySt::_bitWidth> packed_data;
    packed_data.range(0+63, 0+0) = x.data.word[0];
    packed_data.range(0+69, 0+64) = x.data.word[1];
    packed_data.range(70+1-1, 70) = x.marker;
    return packed_data;
}
inline void testRefUnpack(srcOut1BoundarySt &x, const sc_bv<srcOut1BoundarySt::_bitWidth> &packed_data)
{
    x.data.word[0] = (uint64_t) packed_data.range(0+63, 0+0).to_uint64();
    x.data.word[1] = (uint64_t) packed_data.range(0+69, 0+64).to_uint64();
    x.marker = (boundaryMarkerT) packed_data.range(70+1-1, 70).to_uint64();
}
} // namespace ip_test_ip_top_ns
export namespace ip_test_ip_top_test_ns {
class test_ip_top_structs {
public:
    static std::string name(void);
    static void test(void);
private:
    template<typename T>
    static void roundTrip(const char* sName, const std::vector<uint8_t>& patterns) {
        for(auto pattern : patterns) {
            roundTripBytes<T>(sName, pattern, 0);
        }
        // Bytes that differ by position expose a field placed a whole number of bytes off.
        roundTripBytes<T>(sName, 0x5b, 0x35);
    }
    template<typename T>
    static void roundTripBytes(const char* sName, uint8_t first, uint8_t step) {
        using P = typename T::_packedSt;
        P words{};
        sc_bv<T::_bitWidth> aInit;
        for (int i = 0; i < T::_byteWidth; i++) {
            uint8_t byte = (uint8_t)(first + i * step);
            int end = std::min((i+1)*8-1, T::_bitWidth-1);
            aInit.range(end, i*8) = byte;
            if constexpr (std::is_array_v<P>) {
                words[i / 8] |= (uint64_t)byte << ((i % 8) * 8);
            } else {
                words |= (P)((uint64_t)byte << (i * 8));
            }
        }
        T ref;
        testRefUnpack(ref, aInit);
        Q_ASSERT(testRefPack(ref) == aInit, std::string(sName) + ": testRefPack(testRefUnpack(pattern)) is not the pattern");
        T b;
        b.unpack(words);
        if (!(b == ref)) {
            cout << ref.prt() << endl << b.prt() << endl;
            Q_ASSERT(false, std::string(sName) + ": unpack() differs from the reference layout");
        }
        T c;
        c.sc_unpack(aInit);
        if (!(c == ref)) {
            cout << ref.prt() << endl << c.prt() << endl;
            Q_ASSERT(false, std::string(sName) + ": sc_unpack() differs from the reference layout");
        }
        P out;
        ref.pack(out);
        sc_bv<T::_bitWidth> outBits;
        for (int i = 0; i < T::_bitWidth; i++) {
            uint64_t word;
            if constexpr (std::is_array_v<P>) {
                word = out[i / 64];
            } else {
                word = (uint64_t)out;
            }
            outBits[i] = (bool)((word >> (i % 64)) & 1);
        }
        if (!(outBits == aInit)) {
            cout << ref.prt() << endl << outBits << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": pack() differs from the reference layout");
        }
        sc_bv<T::_bitWidth> scPacked = ref.sc_pack();
        if (!(scPacked == aInit)) {
            cout << ref.prt() << endl << scPacked << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": sc_pack() differs from the reference layout");
        }
        b.pack(out);
        for (int i = 0; i < T::_bitWidth; i++) {
            uint64_t word;
            if constexpr (std::is_array_v<P>) {
                word = out[i / 64];
            } else {
                word = (uint64_t)out;
            }
            outBits[i] = (bool)((word >> (i % 64)) & 1);
        }
        if (!(outBits == aInit)) {
            cout << b.prt() << endl << outBits << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": pack(unpack(pattern)) is not the pattern");
        }
    }
};
} // namespace ip_test_ip_top_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ip_test_ip_top_test_ns {
using namespace ip_test_ip_top_ns;
std::string test_ip_top_structs::name(void) { return "test_ip_top_structs"; }
void test_ip_top_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<srcOut0BoundarySt>("srcOut0BoundarySt", patterns);
    roundTrip<srcOut1BoundarySt>("srcOut1BoundarySt", patterns);
}
} // namespace ip_test_ip_top_test_ns

// GENERATED_CODE_END
