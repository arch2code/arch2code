
// GENERATED_CODE_PARAM --project=xpSktIp --context=../../yaml/xpSktIp.yaml --mode=module
//

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpSktIp;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpSktIp_ns {
//constants

} // namespace xpSktIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpSktIp_ns {
// types
template<uint32_t SK_PIXEL_WIDTH> using skPixelT_v = uint64_t; // [max:16] Parameterizable pixel word
template<typename Config> using skPixelT = skPixelT_v<Config::SK_PIXEL_WIDTH>;
typedef uint8_t skTagT; // [8] Sample sequence tag

} // namespace xpSktIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpSktIp_ns {
// enums

} // namespace xpSktIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpSktIp_ns {
// structures
template<uint32_t SK_PIXEL_WIDTH>
struct skSampleSt_v {
    skPixelT_v<SK_PIXEL_WIDTH> data; //Parameterizable pixel payload
    skTagT tag; //Sample sequence tag

    skSampleSt_v() {}

    static constexpr uint16_t _bitWidth = SK_PIXEL_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const skSampleSt_v<SK_PIXEL_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const skSampleSt_v<SK_PIXEL_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  skSampleSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:02x} data:0x{:02x}",
           (uint64_t) tag,
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, SK_PIXEL_WIDTH);
        _pos += SK_PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (skPixelT_v<SK_PIXEL_WIDTH>)((_src >> (_pos & 63)) & (~0ULL >> (64 - (SK_PIXEL_WIDTH))));
        _pos += SK_PIXEL_WIDTH;
        tag = (skTagT)((_src >> (_pos & 63)) & (~0ULL >> (64 - (8))));
    }
    inline sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "skSampleSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit skSampleSt_v(const sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit skSampleSt_v(
        skPixelT_v<SK_PIXEL_WIDTH> data_,
        skTagT tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit skSampleSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using skSampleSt = skSampleSt_v<Config::SK_PIXEL_WIDTH>;
} // namespace xpSktIp_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpSktIp_ns {
template<uint32_t SK_PIXEL_WIDTH> inline sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> testRefPack(const skSampleSt_v<SK_PIXEL_WIDTH> &x);
template<uint32_t SK_PIXEL_WIDTH> inline void testRefUnpack(skSampleSt_v<SK_PIXEL_WIDTH> &x, const sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> &packed_data);
template<uint32_t SK_PIXEL_WIDTH> inline sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> testRefPack(const skSampleSt_v<SK_PIXEL_WIDTH> &x)
{
    sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+SK_PIXEL_WIDTH-1, _pos) = x.data;
    _pos += SK_PIXEL_WIDTH;
    packed_data.range(_pos+8-1, _pos) = x.tag;
    _pos += 8;
    return packed_data;
}
template<uint32_t SK_PIXEL_WIDTH> inline void testRefUnpack(skSampleSt_v<SK_PIXEL_WIDTH> &x, const sc_bv<skSampleSt_v<SK_PIXEL_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.data = (skPixelT_v<SK_PIXEL_WIDTH>) packed_data.range(_pos+SK_PIXEL_WIDTH-1, _pos).to_uint64();
    _pos += SK_PIXEL_WIDTH;
    x.tag = (skTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
    _pos += 8;
}
} // namespace xpSktIp_ns
export namespace xpSktIp_test_ns {
class test_xpSktIp_structs {
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
} // namespace xpSktIp_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpSktIp_test_ns {
using namespace xpSktIp_ns;
struct xpSktIpTestConfigDefault {
    static constexpr uint32_t SK_PIXEL_WIDTH = 8;
};
struct xpSktIpTestConfigMax {
    static constexpr uint32_t SK_PIXEL_WIDTH = 16;
};
std::string test_xpSktIp_structs::name(void) { return "test_xpSktIp_structs"; }
void test_xpSktIp_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<skSampleSt<xpSktIpTestConfigDefault>>("skSampleSt", patterns);
    roundTrip<skSampleSt<xpSktIpTestConfigMax>>("skSampleSt", patterns);
}
} // namespace xpSktIp_test_ns

// GENERATED_CODE_END
