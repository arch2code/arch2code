
// GENERATED_CODE_PARAM --project=ip_test --context=../../src/yaml/src.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module ip_test_src;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import ip_test_ipLeaf;
using namespace ip_test_ipLeaf_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_test_src_ns {
//constants

} // namespace ip_test_src_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_test_src_ns {
// types
template<uint32_t OUT0_DATA_WIDTH> using srcOut0DataT_v = uint64_t; // [max:16] src out0 data word, parameterizable
template<typename Config> using srcOut0DataT = srcOut0DataT_v<Config::OUT0_DATA_WIDTH>;
template<uint32_t OUT1_DATA_WIDTH> struct srcOut1DataT_v { uint64_t word[ 2 ]; }; // [max:128] src out1 data word, parameterizable
template<typename Config> using srcOut1DataT = srcOut1DataT_v<Config::OUT1_DATA_WIDTH>;
typedef uint8_t srcMarkerT; // [1] src high-word marker bit

} // namespace ip_test_src_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_test_src_ns {
// enums

} // namespace ip_test_src_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ip_test_src_ns {
// structures
template<uint32_t OUT0_DATA_WIDTH>
struct srcOut0St_v {
    srcOut0DataT_v<OUT0_DATA_WIDTH> data; //src out0 payload
    srcMarkerT marker; //marker bit copied through the thunker

    srcOut0St_v() {}

    static constexpr uint16_t _bitWidth = OUT0_DATA_WIDTH + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const srcOut0St_v<OUT0_DATA_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (marker == rhs.marker);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const srcOut0St_v<OUT0_DATA_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.marker, NAME + ".marker");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  srcOut0St_v const & v ) {
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
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, OUT0_DATA_WIDTH);
        _pos += OUT0_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, marker, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (srcOut0DataT_v<OUT0_DATA_WIDTH>)((_src >> (_pos & 63)) & (~0ULL >> (64 - (OUT0_DATA_WIDTH))));
        _pos += OUT0_DATA_WIDTH;
        marker = (srcMarkerT)((_src >> (_pos & 63)) & 1);
    }
    inline sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "srcOut0St", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit srcOut0St_v(const sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit srcOut0St_v(
        srcOut0DataT_v<OUT0_DATA_WIDTH> data_,
        srcMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit srcOut0St_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using srcOut0St = srcOut0St_v<Config::OUT0_DATA_WIDTH>;
template<uint32_t OUT1_DATA_WIDTH>
struct srcOut1St_v {
    srcOut1DataT_v<OUT1_DATA_WIDTH> data; //src out1 payload
    srcMarkerT marker; //marker bit above bit 64 for the 70-bit variant

    srcOut1St_v() {}

    static constexpr uint16_t _bitWidth = OUT1_DATA_WIDTH + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline bool operator == (const srcOut1St_v<OUT1_DATA_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (marker == rhs.marker);
        ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
        ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const srcOut1St_v<OUT1_DATA_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.marker, NAME + ".marker");
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  srcOut1St_v const & v ) {
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
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&data, OUT1_DATA_WIDTH);
        _pos += OUT1_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, marker, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&data, 0, sizeof(data));
        unpack_bits((uint64_t *)&data, 0, (uint64_t *)&_src, _pos, OUT1_DATA_WIDTH);
        _pos += OUT1_DATA_WIDTH;
        marker = (srcMarkerT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    inline sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)(_packed[i >> 1] >> ((i & 1) * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "srcOut1St", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> &packed_data)
    {
        _packedSt _words{};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _words[i >> 1] |= (uint64_t)packed_data.get_word(i) << ((i & 1) * 32);
        }
        unpack(_words);
    }
    explicit srcOut1St_v(const sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit srcOut1St_v(
        srcOut1DataT_v<OUT1_DATA_WIDTH> data_,
        srcMarkerT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit srcOut1St_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using srcOut1St = srcOut1St_v<Config::OUT1_DATA_WIDTH>;
} // namespace ip_test_src_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ip_test_src_ns {
template<uint32_t OUT0_DATA_WIDTH> inline sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> testRefPack(const srcOut0St_v<OUT0_DATA_WIDTH> &x);
template<uint32_t OUT0_DATA_WIDTH> inline void testRefUnpack(srcOut0St_v<OUT0_DATA_WIDTH> &x, const sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> &packed_data);
template<uint32_t OUT1_DATA_WIDTH> inline sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> testRefPack(const srcOut1St_v<OUT1_DATA_WIDTH> &x);
template<uint32_t OUT1_DATA_WIDTH> inline void testRefUnpack(srcOut1St_v<OUT1_DATA_WIDTH> &x, const sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> &packed_data);
template<uint32_t OUT0_DATA_WIDTH> inline sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> testRefPack(const srcOut0St_v<OUT0_DATA_WIDTH> &x)
{
    sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+OUT0_DATA_WIDTH-1, _pos) = x.data;
    _pos += OUT0_DATA_WIDTH;
    packed_data.range(_pos+1-1, _pos) = x.marker;
    _pos += 1;
    return packed_data;
}
template<uint32_t OUT0_DATA_WIDTH> inline void testRefUnpack(srcOut0St_v<OUT0_DATA_WIDTH> &x, const sc_bv<srcOut0St_v<OUT0_DATA_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.data = (srcOut0DataT_v<OUT0_DATA_WIDTH>) packed_data.range(_pos+OUT0_DATA_WIDTH-1, _pos).to_uint64();
    _pos += OUT0_DATA_WIDTH;
    x.marker = (srcMarkerT) packed_data.range(_pos+1-1, _pos).to_uint64();
    _pos += 1;
}
template<uint32_t OUT1_DATA_WIDTH> inline sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> testRefPack(const srcOut1St_v<OUT1_DATA_WIDTH> &x)
{
    sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    if (OUT1_DATA_WIDTH > 0) {
        uint16_t _bits = std::min((uint16_t)64, (uint16_t)(OUT1_DATA_WIDTH - 0));
        packed_data.range(_pos + 0 + _bits - 1, _pos + 0) = x.data.word[0];
    }
    if (OUT1_DATA_WIDTH > 64) {
        uint16_t _bits = std::min((uint16_t)64, (uint16_t)(OUT1_DATA_WIDTH - 64));
        packed_data.range(_pos + 64 + _bits - 1, _pos + 64) = x.data.word[1];
    }
    _pos += OUT1_DATA_WIDTH;
    packed_data.range(_pos+1-1, _pos) = x.marker;
    _pos += 1;
    return packed_data;
}
template<uint32_t OUT1_DATA_WIDTH> inline void testRefUnpack(srcOut1St_v<OUT1_DATA_WIDTH> &x, const sc_bv<srcOut1St_v<OUT1_DATA_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    memset((uint64_t *)&x.data, 0, sizeof(x.data));
    if (OUT1_DATA_WIDTH > 0) {
        uint16_t _bits = std::min((uint16_t)64, (uint16_t)(OUT1_DATA_WIDTH - 0));
        x.data.word[0] = (uint64_t) packed_data.range(_pos + 0 + _bits - 1, _pos + 0).to_uint64();
    }
    if (OUT1_DATA_WIDTH > 64) {
        uint16_t _bits = std::min((uint16_t)64, (uint16_t)(OUT1_DATA_WIDTH - 64));
        x.data.word[1] = (uint64_t) packed_data.range(_pos + 64 + _bits - 1, _pos + 64).to_uint64();
    }
    _pos += OUT1_DATA_WIDTH;
    x.marker = (srcMarkerT) packed_data.range(_pos+1-1, _pos).to_uint64();
    _pos += 1;
}
} // namespace ip_test_src_ns
export namespace ip_test_src_test_ns {
class test_src_structs {
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
} // namespace ip_test_src_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ip_test_src_test_ns {
using namespace ip_test_src_ns;
struct srcTestConfigDefault {
    static constexpr uint32_t OUT0_DATA_WIDTH = 8;
    static constexpr uint32_t OUT1_DATA_WIDTH = 70;
};
struct srcTestConfigMid {
    static constexpr uint32_t OUT0_DATA_WIDTH = 8;
    static constexpr uint32_t OUT1_DATA_WIDTH = 64;
};
struct srcTestConfigMax {
    static constexpr uint32_t OUT0_DATA_WIDTH = 16;
    static constexpr uint32_t OUT1_DATA_WIDTH = 128;
};
std::string test_src_structs::name(void) { return "test_src_structs"; }
void test_src_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<srcOut0St<srcTestConfigDefault>>("srcOut0St", patterns);
    roundTrip<srcOut0St<srcTestConfigMid>>("srcOut0St", patterns);
    roundTrip<srcOut0St<srcTestConfigMax>>("srcOut0St", patterns);
    roundTrip<srcOut1St<srcTestConfigDefault>>("srcOut1St", patterns);
    roundTrip<srcOut1St<srcTestConfigMid>>("srcOut1St", patterns);
    roundTrip<srcOut1St<srcTestConfigMax>>("srcOut1St", patterns);
}
} // namespace ip_test_src_test_ns

// GENERATED_CODE_END
