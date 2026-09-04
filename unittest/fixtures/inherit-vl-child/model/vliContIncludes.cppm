
// GENERATED_CODE_PARAM --project=vlInh --context=../../yaml/vliCont.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module vlInh_vliCont;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace vlInh_vliCont_ns {
//constants

} // namespace vlInh_vliCont_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace vlInh_vliCont_ns {
// types
template<typename Config> using vliPixelT = uint64_t; // [max:32] Parameterizable pixel word
typedef uint8_t vliTagT; // [8] Sample sequence tag; lowest packed position
typedef uint8_t vliAlgoT; // [8] Algorithm the leaf instance resolved, stamped into the payload
typedef uint8_t vliWidT; // [8] VLI_WIDTH the leaf instance elaborated at, stamped into the payload
typedef uint8_t vliMarkT; // [8] Trailing marker

} // namespace vlInh_vliCont_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace vlInh_vliCont_ns {
// enums

} // namespace vlInh_vliCont_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace vlInh_vliCont_ns {
// structures
template<typename Config>
struct vliSt {
    vliMarkT mark; //Trailing marker
    vliPixelT<Config> data; //Parameterizable pixel payload
    vliWidT wid; //VLI_WIDTH the leaf instance resolved
    vliAlgoT algo; //VLI_ALGO the leaf instance resolved
    vliTagT tag; //Sample sequence tag

    vliSt() {}

    static constexpr uint16_t _bitWidth = 8 + Config::VLI_WIDTH + 8 + 8 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const vliSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (algo == rhs.algo);
        ret = ret && (wid == rhs.wid);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const vliSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.algo, NAME + ".algo");
        sc_trace(tf,v.wid, NAME + ".wid");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  vliSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:02x} algo:0x{:02x} wid:0x{:02x} data:0x{:02x} mark:0x{:02x}",
           (uint64_t) tag,
           (uint64_t) algo,
           (uint64_t) wid,
           (uint64_t) data,
           (uint64_t) mark
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, vliSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, mark, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, data, Config::VLI_WIDTH);
        _pos += Config::VLI_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, wid, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, algo, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (vliMarkT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        data = (vliPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::VLI_WIDTH)) - 1));
        _pos += Config::VLI_WIDTH;
        wid = (vliWidT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        algo = (vliAlgoT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        tag = (vliTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<vliSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<vliSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+8-1, _pos) = mark;
        _pos += 8;
        packed_data.range(_pos+Config::VLI_WIDTH-1, _pos) = data;
        _pos += Config::VLI_WIDTH;
        packed_data.range(_pos+8-1, _pos) = wid;
        _pos += 8;
        packed_data.range(_pos+8-1, _pos) = algo;
        _pos += 8;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<vliSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        mark = (vliMarkT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        data = (vliPixelT<Config>) packed_data.range(_pos+Config::VLI_WIDTH-1, _pos).to_uint64();
        _pos += Config::VLI_WIDTH;
        wid = (vliWidT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        algo = (vliAlgoT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        tag = (vliTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit vliSt(sc_bv<vliSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit vliSt(
        vliMarkT mark_,
        vliPixelT<Config> data_,
        vliWidT wid_,
        vliAlgoT algo_,
        vliTagT tag_) :
        mark(mark_),
        data(data_),
        wid(wid_),
        algo(algo_),
        tag(tag_)
    {}
    explicit vliSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace vlInh_vliCont_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace vlInh_vliCont_test_ns {
class test_vliCont_structs {
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
} // namespace vlInh_vliCont_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace vlInh_vliCont_test_ns {
using namespace vlInh_vliCont_ns;
struct vliContTestConfigDefault {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 8;
};
struct vliContTestConfigMid {
    static constexpr uint32_t VLI_ALGO = 3;
    static constexpr uint32_t VLI_WIDTH = 16;
};
struct vliContTestConfigMax {
    static constexpr uint32_t VLI_ALGO = 7;
    static constexpr uint32_t VLI_WIDTH = 32;
};
std::string test_vliCont_structs::name(void) { return "test_vliCont_structs"; }
void test_vliCont_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<vliSt<vliContTestConfigDefault>>("vliSt", patterns);
    roundTrip<vliSt<vliContTestConfigMid>>("vliSt", patterns);
    roundTrip<vliSt<vliContTestConfigMax>>("vliSt", patterns);
}
} // namespace vlInh_vliCont_test_ns

// GENERATED_CODE_END
