
// GENERATED_CODE_PARAM --project=xpCppLeaf --context=../../yaml/xpCppLeaf.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpCppLeaf;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpCppLeaf_ns {
//constants

} // namespace xpCppLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpCppLeaf_ns {
// types
template<typename Config> using leafPixelT = uint64_t; // [max:32] Parameterizable pixel word
template<typename Config> using leafSignedPixelT = int64_t; // [max:32] Signed parameterizable pixel word
typedef uint8_t leafTagT; // [8] Sample sequence tag
typedef uint32_t leafWordT; // [32] 32-bit header word
typedef uint8_t leafFlagT; // [8] 8-bit header flag

} // namespace xpCppLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpCppLeaf_ns {
// enums

} // namespace xpCppLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpCppLeaf_ns {
// structures
template<typename Config>
struct leafEqSt {
    leafPixelT<Config> data; //Pixel payload
    leafTagT tag; //Sample sequence tag

    leafEqSt() {}

    static constexpr uint16_t _bitWidth = Config::LEAF_PIXEL_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const leafEqSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const leafEqSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  leafEqSt const & v ) {
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
        memset(&_ret, 0, leafEqSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::LEAF_PIXEL_WIDTH);
        _pos += Config::LEAF_PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (leafPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::LEAF_PIXEL_WIDTH)) - 1));
        _pos += Config::LEAF_PIXEL_WIDTH;
        tag = (leafTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<leafEqSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<leafEqSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::LEAF_PIXEL_WIDTH-1, _pos) = data;
        _pos += Config::LEAF_PIXEL_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<leafEqSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (leafPixelT<Config>) packed_data.range(_pos+Config::LEAF_PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::LEAF_PIXEL_WIDTH;
        tag = (leafTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit leafEqSt(sc_bv<leafEqSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit leafEqSt(
        leafPixelT<Config> data_,
        leafTagT tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit leafEqSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct leafOrderSt {
    leafPixelT<Config> second; //Parameterizable member at the high packed position
    leafFlagT first; //Literal member at the low packed position

    leafOrderSt() {}

    static constexpr uint16_t _bitWidth = Config::LEAF_PIXEL_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const leafOrderSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (first == rhs.first);
        ret = ret && (second == rhs.second);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const leafOrderSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.first, NAME + ".first");
        sc_trace(tf,v.second, NAME + ".second");
    }
    inline friend ostream& operator << ( ostream& os,  leafOrderSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("first:0x{:02x} second:0x{:02x}",
           (uint64_t) first,
           (uint64_t) second
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, leafOrderSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, second, Config::LEAF_PIXEL_WIDTH);
        _pos += Config::LEAF_PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, first, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        second = (leafPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::LEAF_PIXEL_WIDTH)) - 1));
        _pos += Config::LEAF_PIXEL_WIDTH;
        first = (leafFlagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<leafOrderSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<leafOrderSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::LEAF_PIXEL_WIDTH-1, _pos) = second;
        _pos += Config::LEAF_PIXEL_WIDTH;
        packed_data.range(_pos+8-1, _pos) = first;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<leafOrderSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        second = (leafPixelT<Config>) packed_data.range(_pos+Config::LEAF_PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::LEAF_PIXEL_WIDTH;
        first = (leafFlagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit leafOrderSt(sc_bv<leafOrderSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit leafOrderSt(
        leafPixelT<Config> second_,
        leafFlagT first_) :
        second(second_),
        first(first_)
    {}
    explicit leafOrderSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct leafSignSt {
    leafSignedPixelT<Config> data; //Signed pixel payload

    leafSignSt() {}

    static constexpr uint16_t _bitWidth = Config::LEAF_PIXEL_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const leafSignSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const leafSignSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  leafSignSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:02x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, leafSignSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data & ((1ULL << (Config::LEAF_PIXEL_WIDTH)) - 1), Config::LEAF_PIXEL_WIDTH);
        _pos += Config::LEAF_PIXEL_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (leafSignedPixelT<Config>)((_src) & ((1ULL << (Config::LEAF_PIXEL_WIDTH)) - 1));
        // Sign extension for signed type
        if (data & (1ULL << (Config::LEAF_PIXEL_WIDTH - 1))) {
            data = (leafSignedPixelT<Config>)(data | ~((1ULL << (Config::LEAF_PIXEL_WIDTH)) - 1));
        }
    }
    inline sc_bv<leafSignSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<leafSignSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::LEAF_PIXEL_WIDTH-1, _pos) = data;
        _pos += Config::LEAF_PIXEL_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<leafSignSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (leafSignedPixelT<Config>) packed_data.range(_pos+Config::LEAF_PIXEL_WIDTH-1, _pos).to_uint64();
        // Sign extension for signed type
        if (data & (1ULL << (Config::LEAF_PIXEL_WIDTH - 1))) {
            data = (leafSignedPixelT<Config>)(data | ~((1ULL << (Config::LEAF_PIXEL_WIDTH)) - 1));
        }
        _pos += Config::LEAF_PIXEL_WIDTH;
    }
    explicit leafSignSt(sc_bv<leafSignSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit leafSignSt(
        leafSignedPixelT<Config> data_) :
        data(data_)
    {}
    explicit leafSignSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct leafNestSt {
    leafPixelT<Config> data; //Pixel payload
    leafFlagT tail; //Trailing flag
    leafFlagT flag; //Header flag
    leafWordT word; //Header word

    leafNestSt() {}

    static constexpr uint16_t _bitWidth = Config::LEAF_PIXEL_WIDTH + 8 + 8 + 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const leafNestSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (word == rhs.word);
        ret = ret && (flag == rhs.flag);
        ret = ret && (tail == rhs.tail);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const leafNestSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.word, NAME + ".word");
        sc_trace(tf,v.flag, NAME + ".flag");
        sc_trace(tf,v.tail, NAME + ".tail");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  leafNestSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("word:0x{:08x} flag:0x{:02x} tail:0x{:02x} data:0x{:02x}",
           (uint64_t) word,
           (uint64_t) flag,
           (uint64_t) tail,
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, leafNestSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::LEAF_PIXEL_WIDTH);
        _pos += Config::LEAF_PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tail, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, flag, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, word, 32);
        _pos += 32;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (leafPixelT<Config>)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (Config::LEAF_PIXEL_WIDTH)) - 1));
        _pos += Config::LEAF_PIXEL_WIDTH;
        tail = (leafFlagT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        flag = (leafFlagT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        word = (leafWordT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (32)) - 1));
    }
    inline sc_bv<leafNestSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<leafNestSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::LEAF_PIXEL_WIDTH-1, _pos) = data;
        _pos += Config::LEAF_PIXEL_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tail;
        _pos += 8;
        packed_data.range(_pos+8-1, _pos) = flag;
        _pos += 8;
        packed_data.range(_pos+32-1, _pos) = word;
        _pos += 32;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<leafNestSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (leafPixelT<Config>) packed_data.range(_pos+Config::LEAF_PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::LEAF_PIXEL_WIDTH;
        tail = (leafFlagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        flag = (leafFlagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        word = (leafWordT) packed_data.range(_pos+32-1, _pos).to_uint64();
        _pos += 32;
    }
    explicit leafNestSt(sc_bv<leafNestSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit leafNestSt(
        leafPixelT<Config> data_,
        leafFlagT tail_,
        leafFlagT flag_,
        leafWordT word_) :
        data(data_),
        tail(tail_),
        flag(flag_),
        word(word_)
    {}
    explicit leafNestSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpCppLeaf_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpCppLeaf_test_ns {
class test_xpCppLeaf_structs {
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
} // namespace xpCppLeaf_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpCppLeaf_test_ns {
using namespace xpCppLeaf_ns;
struct xpCppLeafTestConfigDefault {
    static constexpr uint32_t LEAF_PIXEL_WIDTH = 8;
};
struct xpCppLeafTestConfigMid {
    static constexpr uint32_t LEAF_PIXEL_WIDTH = 16;
};
struct xpCppLeafTestConfigMax {
    static constexpr uint32_t LEAF_PIXEL_WIDTH = 32;
};
std::string test_xpCppLeaf_structs::name(void) { return "test_xpCppLeaf_structs"; }
void test_xpCppLeaf_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<leafEqSt<xpCppLeafTestConfigDefault>>("leafEqSt", patterns);
    roundTrip<leafEqSt<xpCppLeafTestConfigMid>>("leafEqSt", patterns);
    roundTrip<leafEqSt<xpCppLeafTestConfigMax>>("leafEqSt", patterns);
    roundTrip<leafOrderSt<xpCppLeafTestConfigDefault>>("leafOrderSt", patterns);
    roundTrip<leafOrderSt<xpCppLeafTestConfigMid>>("leafOrderSt", patterns);
    roundTrip<leafOrderSt<xpCppLeafTestConfigMax>>("leafOrderSt", patterns);
    roundTrip<leafSignSt<xpCppLeafTestConfigDefault>>("leafSignSt", signedPatterns);
    roundTrip<leafSignSt<xpCppLeafTestConfigMid>>("leafSignSt", signedPatterns);
    roundTrip<leafSignSt<xpCppLeafTestConfigMax>>("leafSignSt", signedPatterns);
    roundTrip<leafNestSt<xpCppLeafTestConfigDefault>>("leafNestSt", patterns);
    roundTrip<leafNestSt<xpCppLeafTestConfigMid>>("leafNestSt", patterns);
    roundTrip<leafNestSt<xpCppLeafTestConfigMax>>("leafNestSt", patterns);
}
} // namespace xpCppLeaf_test_ns

// GENERATED_CODE_END
