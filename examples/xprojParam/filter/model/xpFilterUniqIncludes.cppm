
// GENERATED_CODE_PARAM --project=xpFilter --context=../../yaml/xpFilterUniq.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpFilter_xpFilterUniq;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpFilter_xpFilterUniq_ns {
//constants

} // namespace xpFilter_xpFilterUniq_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpFilter_xpFilterUniq_ns {
// types
template<typename Config> using flPixelT = uint64_t; // [max:32] Parameterizable pixel word
typedef uint8_t flTagT; // [4] Sample sequence tag

} // namespace xpFilter_xpFilterUniq_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpFilter_xpFilterUniq_ns {
// enums

} // namespace xpFilter_xpFilterUniq_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpFilter_xpFilterUniq_ns {
// structures
template<typename Config>
struct flVideoSt {
    flPixelT<Config> data; //Pixel payload
    flTagT tag; //Sample sequence tag

    flVideoSt() {}

    static constexpr uint16_t _bitWidth = Config::FL_PIXEL_WIDTH + 4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const flVideoSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const flVideoSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  flVideoSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:01x} data:0x{:02x}",
           (uint64_t) tag,
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, flVideoSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::FL_PIXEL_WIDTH);
        _pos += Config::FL_PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 4);
        _pos += 4;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (flPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::FL_PIXEL_WIDTH)) - 1));
        _pos += Config::FL_PIXEL_WIDTH;
        tag = (flTagT)((_src >> (_pos & 63)) & ((1ULL << (4)) - 1));
    }
    inline sc_bv<flVideoSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<flVideoSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::FL_PIXEL_WIDTH-1, _pos) = data;
        _pos += Config::FL_PIXEL_WIDTH;
        packed_data.range(_pos+4-1, _pos) = tag;
        _pos += 4;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<flVideoSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (flPixelT<Config>) packed_data.range(_pos+Config::FL_PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::FL_PIXEL_WIDTH;
        tag = (flTagT) packed_data.range(_pos+4-1, _pos).to_uint64();
        _pos += 4;
    }
    explicit flVideoSt(sc_bv<flVideoSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit flVideoSt(
        flPixelT<Config> data_,
        flTagT tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit flVideoSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpFilter_xpFilterUniq_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpFilter_xpFilterUniq_test_ns {
class test_xpFilterUniq_structs {
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
} // namespace xpFilter_xpFilterUniq_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpFilter_xpFilterUniq_test_ns {
using namespace xpFilter_xpFilterUniq_ns;
struct xpFilterUniqTestConfigDefault {
    static constexpr uint32_t FL_PIXEL_WIDTH = 8;
};
struct xpFilterUniqTestConfigMid {
    static constexpr uint32_t FL_PIXEL_WIDTH = 16;
};
struct xpFilterUniqTestConfigMax {
    static constexpr uint32_t FL_PIXEL_WIDTH = 32;
};
std::string test_xpFilterUniq_structs::name(void) { return "test_xpFilterUniq_structs"; }
void test_xpFilterUniq_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<flVideoSt<xpFilterUniqTestConfigDefault>>("flVideoSt", patterns);
    roundTrip<flVideoSt<xpFilterUniqTestConfigMid>>("flVideoSt", patterns);
    roundTrip<flVideoSt<xpFilterUniqTestConfigMax>>("flVideoSt", patterns);
}
} // namespace xpFilter_xpFilterUniq_test_ns

// GENERATED_CODE_END
