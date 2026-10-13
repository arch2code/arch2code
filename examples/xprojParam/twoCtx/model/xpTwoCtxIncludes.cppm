
// GENERATED_CODE_PARAM --project=xpTwoCtx --context=../../yaml/xpTwoCtx.yaml --mode=module
//

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpTwoCtx;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import xpDpLeaf;
using namespace xpDpLeaf_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpTwoCtx_ns {
//constants

} // namespace xpTwoCtx_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpTwoCtx_ns {
// types
typedef uint16_t litT; // [16] Literal, non-parameterizable payload word
typedef uint8_t tcTagT; // [8] Sample tag
template<uint32_t TC_GAIN> using tcValT_v = uint64_t; // [max:15] Parameterizable value word sized by this file's knob
template<typename Config> using tcValT = tcValT_v<Config::TC_GAIN>;

} // namespace xpTwoCtx_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpTwoCtx_ns {
// enums

} // namespace xpTwoCtx_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpTwoCtx_ns {
// structures
struct litSt {
    litT v; //Literal payload

    litSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const litSt & rhs) const {
        bool ret = true;
        ret = ret && (v == rhs.v);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const litSt & v, const std::string & NAME ) {
        sc_trace(tf,v.v, NAME + ".v");
    }
    inline friend ostream& operator << ( ostream& os,  litSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("v:0x{:04x}",
           (uint64_t) v
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = v;
    }
    inline void unpack(const _packedSt &_src)
    {
        v = (litT)((_src));
    }
    inline sc_bv<litSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<litSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "litSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<litSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit litSt(const sc_bv<litSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit litSt(
        litT v_) :
        v(v_)
    {}
    explicit litSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<uint32_t TC_GAIN>
struct tcSt_v {
    tcValT_v<TC_GAIN> val; //Parameterizable payload sized by TC_GAIN
    tcTagT tag; //Sample tag

    tcSt_v() {}

    static constexpr uint16_t _bitWidth = TC_GAIN + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const tcSt_v<TC_GAIN> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (val == rhs.val);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tcSt_v<TC_GAIN> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.val, NAME + ".val");
    }
    inline friend ostream& operator << ( ostream& os,  tcSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:02x} val:0x{:01x}",
           (uint64_t) tag,
           (uint64_t) val
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, val, TC_GAIN);
        _pos += TC_GAIN;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        val = (tcValT_v<TC_GAIN>)((_src >> (_pos & 63)) & (~0ULL >> (64 - (TC_GAIN))));
        _pos += TC_GAIN;
        tag = (tcTagT)((_src >> (_pos & 63)) & (~0ULL >> (64 - (8))));
    }
    inline sc_bv<tcSt_v<TC_GAIN>::_bitWidth> sc_pack(void) const
    {
        sc_bv<tcSt_v<TC_GAIN>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "tcSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<tcSt_v<TC_GAIN>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit tcSt_v(const sc_bv<tcSt_v<TC_GAIN>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit tcSt_v(
        tcValT_v<TC_GAIN> val_,
        tcTagT tag_) :
        val(val_),
        tag(tag_)
    {}
    explicit tcSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using tcSt = tcSt_v<Config::TC_GAIN>;
} // namespace xpTwoCtx_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpTwoCtx_ns {
inline sc_bv<litSt::_bitWidth> testRefPack(const litSt &x);
inline void testRefUnpack(litSt &x, const sc_bv<litSt::_bitWidth> &packed_data);
template<uint32_t TC_GAIN> inline sc_bv<tcSt_v<TC_GAIN>::_bitWidth> testRefPack(const tcSt_v<TC_GAIN> &x);
template<uint32_t TC_GAIN> inline void testRefUnpack(tcSt_v<TC_GAIN> &x, const sc_bv<tcSt_v<TC_GAIN>::_bitWidth> &packed_data);
inline sc_bv<litSt::_bitWidth> testRefPack(const litSt &x)
{
    sc_bv<litSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.v;
    return packed_data;
}
inline void testRefUnpack(litSt &x, const sc_bv<litSt::_bitWidth> &packed_data)
{
    x.v = (litT) packed_data.range(0+16-1, 0).to_uint64();
}
template<uint32_t TC_GAIN> inline sc_bv<tcSt_v<TC_GAIN>::_bitWidth> testRefPack(const tcSt_v<TC_GAIN> &x)
{
    sc_bv<tcSt_v<TC_GAIN>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+TC_GAIN-1, _pos) = x.val;
    _pos += TC_GAIN;
    packed_data.range(_pos+8-1, _pos) = x.tag;
    _pos += 8;
    return packed_data;
}
template<uint32_t TC_GAIN> inline void testRefUnpack(tcSt_v<TC_GAIN> &x, const sc_bv<tcSt_v<TC_GAIN>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.val = (tcValT_v<TC_GAIN>) packed_data.range(_pos+TC_GAIN-1, _pos).to_uint64();
    _pos += TC_GAIN;
    x.tag = (tcTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
    _pos += 8;
}
} // namespace xpTwoCtx_ns
export namespace xpTwoCtx_test_ns {
class test_xpTwoCtx_structs {
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
} // namespace xpTwoCtx_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpTwoCtx_test_ns {
using namespace xpTwoCtx_ns;
struct xpTwoCtxTestConfigDefault {
    static constexpr uint32_t TC_GAIN = 2;
};
struct xpTwoCtxTestConfigMid {
    static constexpr uint32_t TC_GAIN = 7;
};
struct xpTwoCtxTestConfigMax {
    static constexpr uint32_t TC_GAIN = 15;
};
std::string test_xpTwoCtx_structs::name(void) { return "test_xpTwoCtx_structs"; }
void test_xpTwoCtx_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<litSt>("litSt", patterns);
    roundTrip<tcSt<xpTwoCtxTestConfigDefault>>("tcSt", patterns);
    roundTrip<tcSt<xpTwoCtxTestConfigMid>>("tcSt", patterns);
    roundTrip<tcSt<xpTwoCtxTestConfigMax>>("tcSt", patterns);
}
} // namespace xpTwoCtx_test_ns

// GENERATED_CODE_END
