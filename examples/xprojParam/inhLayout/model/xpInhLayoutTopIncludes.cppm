
// GENERATED_CODE_PARAM --project=xpInhLayout --context=../../yaml/xpInhLayoutTop.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpInhLayout_xpInhLayoutTop;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpInhLayout_xpInhLayoutTop_ns {
//constants

} // namespace xpInhLayout_xpInhLayoutTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpInhLayout_xpInhLayoutTop_ns {
// types
template<uint32_t IL_WIDTH> using ilPixelT_v = uint64_t; // [max:32] Parameterizable pixel word
template<typename Config> using ilPixelT = ilPixelT_v<Config::IL_WIDTH>;
typedef uint8_t ilTagT; // [8] Sample tag; lowest packed position
typedef uint8_t ilMarkT; // [8] Trailing marker, so a width change also moves an offset

} // namespace xpInhLayout_xpInhLayoutTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpInhLayout_xpInhLayoutTop_ns {
// enums

} // namespace xpInhLayout_xpInhLayoutTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpInhLayout_xpInhLayoutTop_ns {
// structures
template<uint32_t IL_WIDTH>
struct ilSt_v {
    ilMarkT mark; //Trailing marker
    ilPixelT_v<IL_WIDTH> data; //Parameterizable pixel payload
    ilTagT tag; //Sample tag

    ilSt_v() {}

    static constexpr uint16_t _bitWidth = 8 + IL_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const ilSt_v<IL_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ilSt_v<IL_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  ilSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:02x} data:0x{:02x} mark:0x{:02x}",
           (uint64_t) tag,
           (uint64_t) data,
           (uint64_t) mark
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ilSt_v<IL_WIDTH>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, mark, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, data, IL_WIDTH);
        _pos += IL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (ilMarkT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        data = (ilPixelT_v<IL_WIDTH>)((_src >> (_pos & 63)) & ((1ULL << (IL_WIDTH)) - 1));
        _pos += IL_WIDTH;
        tag = (ilTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<ilSt_v<IL_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ilSt_v<IL_WIDTH>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+8-1, _pos) = mark;
        _pos += 8;
        packed_data.range(_pos+IL_WIDTH-1, _pos) = data;
        _pos += IL_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ilSt_v<IL_WIDTH>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        mark = (ilMarkT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        data = (ilPixelT_v<IL_WIDTH>) packed_data.range(_pos+IL_WIDTH-1, _pos).to_uint64();
        _pos += IL_WIDTH;
        tag = (ilTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit ilSt_v(sc_bv<ilSt_v<IL_WIDTH>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ilSt_v(
        ilMarkT mark_,
        ilPixelT_v<IL_WIDTH> data_,
        ilTagT tag_) :
        mark(mark_),
        data(data_),
        tag(tag_)
    {}
    explicit ilSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using ilSt = ilSt_v<Config::IL_WIDTH>;
} // namespace xpInhLayout_xpInhLayoutTop_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpInhLayout_xpInhLayoutTop_test_ns {
class test_xpInhLayoutTop_structs {
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
} // namespace xpInhLayout_xpInhLayoutTop_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpInhLayout_xpInhLayoutTop_test_ns {
using namespace xpInhLayout_xpInhLayoutTop_ns;
struct xpInhLayoutTopTestConfigDefault {
    static constexpr uint32_t IL_WIDTH = 8;
};
struct xpInhLayoutTopTestConfigMid {
    static constexpr uint32_t IL_WIDTH = 16;
};
struct xpInhLayoutTopTestConfigMax {
    static constexpr uint32_t IL_WIDTH = 32;
};
std::string test_xpInhLayoutTop_structs::name(void) { return "test_xpInhLayoutTop_structs"; }
void test_xpInhLayoutTop_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<ilSt<xpInhLayoutTopTestConfigDefault>>("ilSt", patterns);
    roundTrip<ilSt<xpInhLayoutTopTestConfigMid>>("ilSt", patterns);
    roundTrip<ilSt<xpInhLayoutTopTestConfigMax>>("ilSt", patterns);
}
} // namespace xpInhLayout_xpInhLayoutTop_test_ns

// GENERATED_CODE_END
