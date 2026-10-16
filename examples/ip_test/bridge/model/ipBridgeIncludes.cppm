
// GENERATED_CODE_PARAM --project=ipBridge --context=../../yaml/ipBridge.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module ipBridge;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import common_shared_types;
import ip;
using namespace common_shared_types_ns;
using namespace ip_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ipBridge_ns {
//constants

} // namespace ipBridge_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ipBridge_ns {
// types
typedef uint8_t bridgeMarkerT; // [1] 1-bit marker; bit-width matches ipDataSt::marker (packed-form compatibility)
typedef uint8_t data8T; // [8] Fixed 8-bit bridge payload (matches ipDataSt::data under variant0)
struct data70T { uint64_t word[ 2 ]; }; // [70] Fixed 70-bit bridge payload (matches ipDataSt::data under variant1)

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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "data8St", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<data8St::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit data8St(const sc_bv<data8St::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        marker = (bridgeMarkerT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    inline sc_bv<data70St::_bitWidth> sc_pack(void) const
    {
        sc_bv<data70St::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)(_packed[i >> 1] >> ((i & 1) * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "data70St", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<data70St::_bitWidth> &packed_data)
    {
        _packedSt _words{};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _words[i >> 1] |= (uint64_t)packed_data.get_word(i) << ((i & 1) * 32);
        }
        unpack(_words);
    }
    explicit data70St(const sc_bv<data70St::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
inline sc_bv<data8St::_bitWidth> testRefPack(const data8St &x);
inline void testRefUnpack(data8St &x, const sc_bv<data8St::_bitWidth> &packed_data);
inline sc_bv<data70St::_bitWidth> testRefPack(const data70St &x);
inline void testRefUnpack(data70St &x, const sc_bv<data70St::_bitWidth> &packed_data);
inline sc_bv<data8St::_bitWidth> testRefPack(const data8St &x)
{
    sc_bv<data8St::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.data;
    packed_data.range(8+1-1, 8) = x.marker;
    return packed_data;
}
inline void testRefUnpack(data8St &x, const sc_bv<data8St::_bitWidth> &packed_data)
{
    x.data = (data8T) packed_data.range(0+8-1, 0).to_uint64();
    x.marker = (bridgeMarkerT) packed_data.range(8+1-1, 8).to_uint64();
}
inline sc_bv<data70St::_bitWidth> testRefPack(const data70St &x)
{
    sc_bv<data70St::_bitWidth> packed_data;
    packed_data.range(0+63, 0+0) = x.data.word[0];
    packed_data.range(0+69, 0+64) = x.data.word[1];
    packed_data.range(70+1-1, 70) = x.marker;
    return packed_data;
}
inline void testRefUnpack(data70St &x, const sc_bv<data70St::_bitWidth> &packed_data)
{
    x.data.word[0] = (uint64_t) packed_data.range(0+63, 0+0).to_uint64();
    x.data.word[1] = (uint64_t) packed_data.range(0+69, 0+64).to_uint64();
    x.marker = (bridgeMarkerT) packed_data.range(70+1-1, 70).to_uint64();
}
} // namespace ipBridge_ns
export namespace ipBridge_test_ns {
class test_ipBridge_structs {
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
} // namespace ipBridge_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ipBridge_test_ns {
using namespace ipBridge_ns;
std::string test_ipBridge_structs::name(void) { return "test_ipBridge_structs"; }
void test_ipBridge_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<data8St>("data8St", patterns);
    roundTrip<data70St>("data70St", patterns);
}
} // namespace ipBridge_test_ns

// GENERATED_CODE_END
