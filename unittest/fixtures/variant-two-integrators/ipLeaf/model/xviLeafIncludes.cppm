
// GENERATED_CODE_PARAM --project=xviLeaf --context=../../yaml/xviLeaf.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xviLeaf;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xviLeaf_ns {
//constants

} // namespace xviLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xviLeaf_ns {
// types
template<typename Config> using xviPixelT = uint64_t; // [max:32] Parameterizable pixel word
typedef uint8_t xviTagT; // [8] Sample sequence tag

} // namespace xviLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xviLeaf_ns {
// enums

} // namespace xviLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xviLeaf_ns {
// structures
template<typename Config>
struct xviSt {
    xviPixelT<Config> data; //Parameterizable pixel payload
    xviTagT tag; //Sample sequence tag

    xviSt() {}

    static constexpr uint16_t _bitWidth = Config::XVI_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const xviSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const xviSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  xviSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:02x} data:0x{:02x}",
           (uint64_t) tag,
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, xviSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::XVI_WIDTH);
        _pos += Config::XVI_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (xviPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::XVI_WIDTH)) - 1));
        _pos += Config::XVI_WIDTH;
        tag = (xviTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<xviSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<xviSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::XVI_WIDTH-1, _pos) = data;
        _pos += Config::XVI_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<xviSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (xviPixelT<Config>) packed_data.range(_pos+Config::XVI_WIDTH-1, _pos).to_uint64();
        _pos += Config::XVI_WIDTH;
        tag = (xviTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit xviSt(sc_bv<xviSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit xviSt(
        xviPixelT<Config> data_,
        xviTagT tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit xviSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xviLeaf_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xviLeaf_test_ns {
class test_xviLeaf_structs {
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
} // namespace xviLeaf_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xviLeaf_test_ns {
using namespace xviLeaf_ns;
struct xviLeafTestConfigDefault {
    static constexpr uint32_t XVI_WIDTH = 8;
    static constexpr uint32_t XVI_GAIN = 1;
};
struct xviLeafTestConfigMid {
    static constexpr uint32_t XVI_WIDTH = 16;
    static constexpr uint32_t XVI_GAIN = 7;
};
struct xviLeafTestConfigMax {
    static constexpr uint32_t XVI_WIDTH = 32;
    static constexpr uint32_t XVI_GAIN = 15;
};
std::string test_xviLeaf_structs::name(void) { return "test_xviLeaf_structs"; }
void test_xviLeaf_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<xviSt<xviLeafTestConfigDefault>>("xviSt", patterns);
    roundTrip<xviSt<xviLeafTestConfigMid>>("xviSt", patterns);
    roundTrip<xviSt<xviLeafTestConfigMax>>("xviSt", patterns);
}
} // namespace xviLeaf_test_ns

// GENERATED_CODE_END
