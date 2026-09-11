
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
template<typename Config> using cfgDataT = uint64_t; // [max:32] xpRtLeaf configuration payload

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
template<typename Config>
struct cfgSt {
    cfgDataT<Config> value; //xpRtLeaf configuration value

    cfgSt() {}

    static constexpr uint16_t _bitWidth = Config::RT_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const cfgSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (value == rhs.value);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cfgSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.value, NAME + ".value");
    }
    inline friend ostream& operator << ( ostream& os,  cfgSt const & v ) {
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
        memset(&_ret, 0, cfgSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, value, Config::RT_WIDTH);
        _pos += Config::RT_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (cfgDataT<Config>)((_src) & ((1ULL << (Config::RT_WIDTH)) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( value & ((1ULL<<Config::RT_WIDTH )-1) << 0);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        value = ( cfgDataT<Config> ) (( packedValue >> 0 ) & (( (uint64_t)1 << Config::RT_WIDTH ) - 1)) ;
        }
    inline sc_bv<cfgSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<cfgSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::RT_WIDTH-1, _pos) = value;
        _pos += Config::RT_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<cfgSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        value = (cfgDataT<Config>) packed_data.range(_pos+Config::RT_WIDTH-1, _pos).to_uint64();
        _pos += Config::RT_WIDTH;
    }
    explicit cfgSt(sc_bv<cfgSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit cfgSt(
        cfgDataT<Config> value_) :
        value(value_)
    {}
    explicit cfgSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpRtInh_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpRtInh_test_ns {
class test_xpRtInh_structs {
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
