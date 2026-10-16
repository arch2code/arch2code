
// GENERATED_CODE_PARAM --project=xpRtInh --context=../../yaml/xpRtInh.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpRtInh;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import common_shared_types;
using namespace common_shared_types_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpRtInh_ns {
//constants

} // namespace xpRtInh_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpRtInh_ns {
// types
template<uint32_t RT_WIDTH> using cfgDataT_v = uint64_t; // [max:32] xpRtLeaf configuration payload
template<typename Config> using cfgDataT = cfgDataT_v<Config::RT_WIDTH>;

} // namespace xpRtInh_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpRtInh_ns {
// enums
enum  addr_id_xpRtInhTop {   //Generated type for addressing top instances
    ADDR_ID_XPRTINHTOP_UWRAP=0 }; // uWrap instance address
inline const char* addr_id_xpRtInhTop_prt( addr_id_xpRtInhTop val )
{
    switch( val )
    {
        case ADDR_ID_XPRTINHTOP_UWRAP: return( "ADDR_ID_XPRTINHTOP_UWRAP" );
    }
    return("!!!BADENUM!!!");
}
enum  addr_id_xpRtWrap {     //Generated type for addressing wrap instances
    ADDR_ID_XPRTWRAP_ULEAF=0 }; // uLeaf instance address
inline const char* addr_id_xpRtWrap_prt( addr_id_xpRtWrap val )
{
    switch( val )
    {
        case ADDR_ID_XPRTWRAP_ULEAF: return( "ADDR_ID_XPRTWRAP_ULEAF" );
    }
    return("!!!BADENUM!!!");
}

} // namespace xpRtInh_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpRtInh_ns {
// structures
template<uint32_t RT_WIDTH>
struct cfgSt_v {
    cfgDataT_v<RT_WIDTH> value; //xpRtLeaf configuration value

    cfgSt_v() {}

    static constexpr uint16_t _bitWidth = RT_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const cfgSt_v<RT_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (value == rhs.value);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cfgSt_v<RT_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.value, NAME + ".value");
    }
    inline friend ostream& operator << ( ostream& os,  cfgSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("value:0x{:02x}",
           (uint64_t) value
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, value, RT_WIDTH);
        _pos += RT_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (cfgDataT_v<RT_WIDTH>)((_src) & (~0ULL >> (64 - (RT_WIDTH))));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        (( value & (~0ULL >> (64 - (RT_WIDTH))) ) << 0);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        value = ( cfgDataT_v<RT_WIDTH> ) (( packedValue >> 0 ) & (~0ULL >> (64 - (RT_WIDTH)))) ;
        }
    inline sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "cfgSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit cfgSt_v(const sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit cfgSt_v(
        cfgDataT_v<RT_WIDTH> value_) :
        value(value_)
    {}
    explicit cfgSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using cfgSt = cfgSt_v<Config::RT_WIDTH>;
} // namespace xpRtInh_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpRtInh_ns {
template<uint32_t RT_WIDTH> inline sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> testRefPack(const cfgSt_v<RT_WIDTH> &x);
template<uint32_t RT_WIDTH> inline void testRefUnpack(cfgSt_v<RT_WIDTH> &x, const sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> &packed_data);
template<uint32_t RT_WIDTH> inline sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> testRefPack(const cfgSt_v<RT_WIDTH> &x)
{
    sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+RT_WIDTH-1, _pos) = x.value;
    _pos += RT_WIDTH;
    return packed_data;
}
template<uint32_t RT_WIDTH> inline void testRefUnpack(cfgSt_v<RT_WIDTH> &x, const sc_bv<cfgSt_v<RT_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.value = (cfgDataT_v<RT_WIDTH>) packed_data.range(_pos+RT_WIDTH-1, _pos).to_uint64();
    _pos += RT_WIDTH;
}
} // namespace xpRtInh_ns
export namespace xpRtInh_test_ns {
class test_xpRtInh_structs {
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
} // namespace xpRtInh_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpRtInh_test_ns {
using namespace xpRtInh_ns;
struct xpRtInhTestConfigDefault {
    static constexpr uint32_t RT_WIDTH = 8;
};
struct xpRtInhTestConfigMid {
    static constexpr uint32_t RT_WIDTH = 16;
};
struct xpRtInhTestConfigMax {
    static constexpr uint32_t RT_WIDTH = 32;
};
std::string test_xpRtInh_structs::name(void) { return "test_xpRtInh_structs"; }
void test_xpRtInh_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<cfgSt<xpRtInhTestConfigDefault>>("cfgSt", patterns);
    roundTrip<cfgSt<xpRtInhTestConfigMid>>("cfgSt", patterns);
    roundTrip<cfgSt<xpRtInhTestConfigMax>>("cfgSt", patterns);
}
} // namespace xpRtInh_test_ns

// GENERATED_CODE_END
