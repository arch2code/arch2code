
// GENERATED_CODE_PARAM --project=xpInhVar --context=../../yaml/xpInhCont.yaml --mode=module
//

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpInhVar_xpInhCont;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpInhVar_xpInhCont_ns {
//constants

} // namespace xpInhVar_xpInhCont_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpInhVar_xpInhCont_ns {
// types
template<uint32_t INH_WIDTH> using inhPixelT_v = uint64_t; // [max:32] Parameterizable pixel word
template<typename Config> using inhPixelT = inhPixelT_v<Config::INH_WIDTH>;
typedef uint8_t inhTagT; // [8] Sample sequence tag; lowest packed position
typedef uint8_t inhAlgoT; // [8] Algorithm the leaf instance resolved, stamped into the payload
typedef uint8_t inhMarkT; // [8] Trailing marker

} // namespace xpInhVar_xpInhCont_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpInhVar_xpInhCont_ns {
// enums

} // namespace xpInhVar_xpInhCont_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpInhVar_xpInhCont_ns {
// structures
template<uint32_t INH_WIDTH>
struct inhSt_v {
    inhMarkT mark; //Trailing marker
    inhPixelT_v<INH_WIDTH> data; //Parameterizable pixel payload
    inhAlgoT algo; //INH_ALGO the leaf instance resolved
    inhTagT tag; //Sample sequence tag

    inhSt_v() {}

    static constexpr uint16_t _bitWidth = 8 + INH_WIDTH + 8 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const inhSt_v<INH_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (algo == rhs.algo);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const inhSt_v<INH_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.algo, NAME + ".algo");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  inhSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:02x} algo:0x{:02x} data:0x{:02x} mark:0x{:02x}",
           (uint64_t) tag,
           (uint64_t) algo,
           (uint64_t) data,
           (uint64_t) mark
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, mark, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, data, INH_WIDTH);
        _pos += INH_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, algo, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (inhMarkT)((_src >> (_pos & 63)) & (~0ULL >> (64 - (8))));
        _pos += 8;
        data = (inhPixelT_v<INH_WIDTH>)((_src >> (_pos & 63)) & (~0ULL >> (64 - (INH_WIDTH))));
        _pos += INH_WIDTH;
        algo = (inhAlgoT)((_src >> (_pos & 63)) & (~0ULL >> (64 - (8))));
        _pos += 8;
        tag = (inhTagT)((_src >> (_pos & 63)) & (~0ULL >> (64 - (8))));
    }
    inline sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "inhSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit inhSt_v(const sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit inhSt_v(
        inhMarkT mark_,
        inhPixelT_v<INH_WIDTH> data_,
        inhAlgoT algo_,
        inhTagT tag_) :
        mark(mark_),
        data(data_),
        algo(algo_),
        tag(tag_)
    {}
    explicit inhSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using inhSt = inhSt_v<Config::INH_WIDTH>;
} // namespace xpInhVar_xpInhCont_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpInhVar_xpInhCont_ns {
template<uint32_t INH_WIDTH> inline sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> testRefPack(const inhSt_v<INH_WIDTH> &x);
template<uint32_t INH_WIDTH> inline void testRefUnpack(inhSt_v<INH_WIDTH> &x, const sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> &packed_data);
template<uint32_t INH_WIDTH> inline sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> testRefPack(const inhSt_v<INH_WIDTH> &x)
{
    sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+8-1, _pos) = x.mark;
    _pos += 8;
    packed_data.range(_pos+INH_WIDTH-1, _pos) = x.data;
    _pos += INH_WIDTH;
    packed_data.range(_pos+8-1, _pos) = x.algo;
    _pos += 8;
    packed_data.range(_pos+8-1, _pos) = x.tag;
    _pos += 8;
    return packed_data;
}
template<uint32_t INH_WIDTH> inline void testRefUnpack(inhSt_v<INH_WIDTH> &x, const sc_bv<inhSt_v<INH_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.mark = (inhMarkT) packed_data.range(_pos+8-1, _pos).to_uint64();
    _pos += 8;
    x.data = (inhPixelT_v<INH_WIDTH>) packed_data.range(_pos+INH_WIDTH-1, _pos).to_uint64();
    _pos += INH_WIDTH;
    x.algo = (inhAlgoT) packed_data.range(_pos+8-1, _pos).to_uint64();
    _pos += 8;
    x.tag = (inhTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
    _pos += 8;
}
} // namespace xpInhVar_xpInhCont_ns
export namespace xpInhVar_xpInhCont_test_ns {
class test_xpInhCont_structs {
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
} // namespace xpInhVar_xpInhCont_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpInhVar_xpInhCont_test_ns {
using namespace xpInhVar_xpInhCont_ns;
struct xpInhContTestConfigDefault {
    static constexpr uint32_t INH_ALGO = 1;
    static constexpr uint32_t INH_WIDTH = 8;
};
struct xpInhContTestConfigMid {
    static constexpr uint32_t INH_ALGO = 3;
    static constexpr uint32_t INH_WIDTH = 16;
};
struct xpInhContTestConfigMax {
    static constexpr uint32_t INH_ALGO = 7;
    static constexpr uint32_t INH_WIDTH = 32;
};
std::string test_xpInhCont_structs::name(void) { return "test_xpInhCont_structs"; }
void test_xpInhCont_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<inhSt<xpInhContTestConfigDefault>>("inhSt", patterns);
    roundTrip<inhSt<xpInhContTestConfigMid>>("inhSt", patterns);
    roundTrip<inhSt<xpInhContTestConfigMax>>("inhSt", patterns);
}
} // namespace xpInhVar_xpInhCont_test_ns

// GENERATED_CODE_END
