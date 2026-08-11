
// GENERATED_CODE_PARAM --project=xpFilter --context=../../yaml/xpFilter.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpFilter;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpFilter_ns {
//constants

} // namespace xpFilter_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpFilter_ns {
// types
template<typename Config> using pixel_t = uint64_t; // [max:32] Parameterizable pixel word
typedef uint8_t tag_t; // [4] Sample sequence tag

} // namespace xpFilter_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpFilter_ns {
// enums

} // namespace xpFilter_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpFilter_ns {
// structures
template<typename Config>
struct videoSt {
    pixel_t<Config> data; //Pixel payload
    tag_t tag; //Sample sequence tag

    videoSt() {}

    static constexpr uint16_t _bitWidth = Config::PIXEL_WIDTH + 4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const videoSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const videoSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  videoSt const & v ) {
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
        memset(&_ret, 0, videoSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::PIXEL_WIDTH);
        _pos += Config::PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 4);
        _pos += 4;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (pixel_t<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::PIXEL_WIDTH)) - 1));
        _pos += Config::PIXEL_WIDTH;
        tag = (tag_t)((_src >> (_pos & 63)) & ((1ULL << (4)) - 1));
    }
    inline sc_bv<videoSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<videoSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::PIXEL_WIDTH-1, _pos) = data;
        _pos += Config::PIXEL_WIDTH;
        packed_data.range(_pos+4-1, _pos) = tag;
        _pos += 4;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<videoSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (pixel_t<Config>) packed_data.range(_pos+Config::PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::PIXEL_WIDTH;
        tag = (tag_t) packed_data.range(_pos+4-1, _pos).to_uint64();
        _pos += 4;
    }
    explicit videoSt(sc_bv<videoSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit videoSt(
        pixel_t<Config> data_,
        tag_t tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit videoSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpFilter_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpFilter_test_ns {
class test_xpFilter_structs {
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
} // namespace xpFilter_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpFilter_test_ns {
using namespace xpFilter_ns;
struct xpFilterTestConfigDefault {
    static constexpr uint32_t PIXEL_WIDTH = 8;
};
struct xpFilterTestConfigMid {
    static constexpr uint32_t PIXEL_WIDTH = 16;
};
struct xpFilterTestConfigMax {
    static constexpr uint32_t PIXEL_WIDTH = 32;
};
std::string test_xpFilter_structs::name(void) { return "test_xpFilter_structs"; }
void test_xpFilter_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<videoSt<xpFilterTestConfigDefault>>("videoSt", patterns);
    roundTrip<videoSt<xpFilterTestConfigMid>>("videoSt", patterns);
    roundTrip<videoSt<xpFilterTestConfigMax>>("videoSt", patterns);
}
} // namespace xpFilter_test_ns

// GENERATED_CODE_END
