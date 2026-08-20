
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
template<typename Config> using inhPixelT = uint64_t; // [max:32] Parameterizable pixel word
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
template<typename Config>
struct inhSt {
    inhMarkT mark; //Trailing marker
    inhPixelT<Config> data; //Parameterizable pixel payload
    inhAlgoT algo; //INH_ALGO the leaf instance resolved
    inhTagT tag; //Sample sequence tag

    inhSt() {}

    static constexpr uint16_t _bitWidth = 8 + Config::INH_WIDTH + 8 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const inhSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (algo == rhs.algo);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const inhSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.algo, NAME + ".algo");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  inhSt const & v ) {
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
        memset(&_ret, 0, inhSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, mark, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, data, Config::INH_WIDTH);
        _pos += Config::INH_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, algo, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (inhMarkT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        data = (inhPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::INH_WIDTH)) - 1));
        _pos += Config::INH_WIDTH;
        algo = (inhAlgoT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        tag = (inhTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<inhSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<inhSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+8-1, _pos) = mark;
        _pos += 8;
        packed_data.range(_pos+Config::INH_WIDTH-1, _pos) = data;
        _pos += Config::INH_WIDTH;
        packed_data.range(_pos+8-1, _pos) = algo;
        _pos += 8;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<inhSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        mark = (inhMarkT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        data = (inhPixelT<Config>) packed_data.range(_pos+Config::INH_WIDTH-1, _pos).to_uint64();
        _pos += Config::INH_WIDTH;
        algo = (inhAlgoT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        tag = (inhTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit inhSt(sc_bv<inhSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit inhSt(
        inhMarkT mark_,
        inhPixelT<Config> data_,
        inhAlgoT algo_,
        inhTagT tag_) :
        mark(mark_),
        data(data_),
        algo(algo_),
        tag(tag_)
    {}
    explicit inhSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpInhVar_xpInhCont_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpInhVar_xpInhCont_test_ns {
class test_xpInhCont_structs {
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
