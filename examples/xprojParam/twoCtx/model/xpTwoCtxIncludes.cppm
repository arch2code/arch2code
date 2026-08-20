
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
template<typename Config> using tcValT = uint64_t; // [max:15] Parameterizable value word sized by this file's knob

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
        memset(&_ret, 0, litSt::_byteWidth);
        _ret = v;
    }
    inline void unpack(const _packedSt &_src)
    {
        v = (litT)((_src));
    }
    inline sc_bv<litSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<litSt::_bitWidth> packed_data;
        packed_data.range(15, 0) = v;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<litSt::_bitWidth> packed_data)
    {
        v = (litT) packed_data.range(15, 0).to_uint64();
    }
    explicit litSt(sc_bv<litSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit litSt(
        litT v_) :
        v(v_)
    {}
    explicit litSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct tcSt {
    tcValT<Config> val; //Parameterizable payload sized by TC_GAIN
    tcTagT tag; //Sample tag

    tcSt() {}

    static constexpr uint16_t _bitWidth = Config::TC_GAIN + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const tcSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (val == rhs.val);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tcSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.val, NAME + ".val");
    }
    inline friend ostream& operator << ( ostream& os,  tcSt const & v ) {
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
        memset(&_ret, 0, tcSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, val, Config::TC_GAIN);
        _pos += Config::TC_GAIN;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        val = (tcValT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::TC_GAIN)) - 1));
        _pos += Config::TC_GAIN;
        tag = (tcTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<tcSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<tcSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::TC_GAIN-1, _pos) = val;
        _pos += Config::TC_GAIN;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<tcSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        val = (tcValT<Config>) packed_data.range(_pos+Config::TC_GAIN-1, _pos).to_uint64();
        _pos += Config::TC_GAIN;
        tag = (tcTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit tcSt(sc_bv<tcSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit tcSt(
        tcValT<Config> val_,
        tcTagT tag_) :
        val(val_),
        tag(tag_)
    {}
    explicit tcSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpTwoCtx_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpTwoCtx_test_ns {
class test_xpTwoCtx_structs {
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
} // namespace xpTwoCtx_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpTwoCtx_test_ns {
using namespace xpTwoCtx_ns;
struct xpTwoCtxTestConfigDefault {
    static constexpr uint32_t TC_GAIN = 2;
    static constexpr uint32_t TC_GAIN_X2 = TC_GAIN * 2;
};
struct xpTwoCtxTestConfigMid {
    static constexpr uint32_t TC_GAIN = 7;
    static constexpr uint32_t TC_GAIN_X2 = TC_GAIN * 2;
};
struct xpTwoCtxTestConfigMax {
    static constexpr uint32_t TC_GAIN = 15;
    static constexpr uint32_t TC_GAIN_X2 = TC_GAIN * 2;
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
