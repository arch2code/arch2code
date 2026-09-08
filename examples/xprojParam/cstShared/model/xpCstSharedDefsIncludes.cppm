
// GENERATED_CODE_PARAM --project=xpCstShared --context=../../yaml/xpCstSharedDefs.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpCstShared_xpCstSharedDefs;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpCstShared_xpCstSharedDefs_ns {
//constants

} // namespace xpCstShared_xpCstSharedDefs_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpCstShared_xpCstSharedDefs_ns {
// types
template<typename Config> using cshPixelT = uint64_t; // [max:32] Parameterizable pixel word
typedef uint8_t cshTagT; // [8] Sample sequence tag
typedef uint8_t cshMarkT; // [8] Trailing marker

} // namespace xpCstShared_xpCstSharedDefs_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpCstShared_xpCstSharedDefs_ns {
// enums

} // namespace xpCstShared_xpCstSharedDefs_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpCstShared_xpCstSharedDefs_ns {
// structures
template<typename Config>
struct cshSt {
    cshMarkT mark; //Trailing marker
    cshPixelT<Config> data; //Parameterizable pixel payload
    cshTagT tag; //Sample sequence tag

    cshSt() {}

    static constexpr uint16_t _bitWidth = 8 + Config::CSH_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const cshSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cshSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  cshSt const & v ) {
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
        memset(&_ret, 0, cshSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, mark, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, data, Config::CSH_WIDTH);
        _pos += Config::CSH_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (cshMarkT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        data = (cshPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::CSH_WIDTH)) - 1));
        _pos += Config::CSH_WIDTH;
        tag = (cshTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<cshSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<cshSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+8-1, _pos) = mark;
        _pos += 8;
        packed_data.range(_pos+Config::CSH_WIDTH-1, _pos) = data;
        _pos += Config::CSH_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<cshSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        mark = (cshMarkT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        data = (cshPixelT<Config>) packed_data.range(_pos+Config::CSH_WIDTH-1, _pos).to_uint64();
        _pos += Config::CSH_WIDTH;
        tag = (cshTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit cshSt(sc_bv<cshSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit cshSt(
        cshMarkT mark_,
        cshPixelT<Config> data_,
        cshTagT tag_) :
        mark(mark_),
        data(data_),
        tag(tag_)
    {}
    explicit cshSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpCstShared_xpCstSharedDefs_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpCstShared_xpCstSharedDefs_test_ns {
class test_xpCstSharedDefs_structs {
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
} // namespace xpCstShared_xpCstSharedDefs_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpCstShared_xpCstSharedDefs_test_ns {
using namespace xpCstShared_xpCstSharedDefs_ns;
struct xpCstSharedDefsTestConfigDefault {
    static constexpr uint32_t CSH_WIDTH = 8;
};
struct xpCstSharedDefsTestConfigMid {
    static constexpr uint32_t CSH_WIDTH = 16;
};
struct xpCstSharedDefsTestConfigMax {
    static constexpr uint32_t CSH_WIDTH = 32;
};
std::string test_xpCstSharedDefs_structs::name(void) { return "test_xpCstSharedDefs_structs"; }
void test_xpCstSharedDefs_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<cshSt<xpCstSharedDefsTestConfigDefault>>("cshSt", patterns);
    roundTrip<cshSt<xpCstSharedDefsTestConfigMid>>("cshSt", patterns);
    roundTrip<cshSt<xpCstSharedDefsTestConfigMax>>("cshSt", patterns);
}
} // namespace xpCstShared_xpCstSharedDefs_test_ns

// GENERATED_CODE_END
