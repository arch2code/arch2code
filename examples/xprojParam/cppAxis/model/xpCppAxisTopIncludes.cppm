
// GENERATED_CODE_PARAM --project=xpCppAxis --context=../../yaml/xpCppAxisTop.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpCppAxis_xpCppAxisTop;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import xpCppAxis_xpCppWrap;
import xpCppLeaf;
using namespace xpCppAxis_xpCppWrap_ns;
using namespace xpCppLeaf_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpCppAxis_xpCppAxisTop_ns {
//constants

} // namespace xpCppAxis_xpCppAxisTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpCppAxis_xpCppAxisTop_ns {
// types
typedef uint8_t bndTagT; // [8] Literal boundary tag
typedef uint8_t bndPixelT; // [8] Literal boundary pixel; matches the bound wrapper width
typedef uint32_t bndWordT; // [32] Literal boundary header word
typedef uint8_t bndFlagT; // [8] Literal boundary header flag

} // namespace xpCppAxis_xpCppAxisTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpCppAxis_xpCppAxisTop_ns {
// enums

} // namespace xpCppAxis_xpCppAxisTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpCppAxis_xpCppAxisTop_ns {
// structures
struct bndEqSt {
    bndPixelT data; //Pixel payload
    bndTagT tag; //Sample sequence tag

    bndEqSt() {}

    static constexpr uint16_t _bitWidth = 8 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const bndEqSt & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bndEqSt & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  bndEqSt const & v ) {
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
        memset(&_ret, 0, bndEqSt::_byteWidth);
        _ret = data;
        _ret |= (uint16_t)tag << (8 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (bndPixelT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
        _pos += 8;
        tag = (bndTagT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
    }
    inline sc_bv<bndEqSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bndEqSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = data;
        packed_data.range(15, 8) = tag;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bndEqSt::_bitWidth> packed_data)
    {
        data = (bndPixelT) packed_data.range(7, 0).to_uint64();
        tag = (bndTagT) packed_data.range(15, 8).to_uint64();
    }
    explicit bndEqSt(sc_bv<bndEqSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bndEqSt(
        bndPixelT data_,
        bndTagT tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit bndEqSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bndOrderSt {
    bndFlagT second; //High packed position
    bndPixelT first; //Low packed position

    bndOrderSt() {}

    static constexpr uint16_t _bitWidth = 8 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const bndOrderSt & rhs) const {
        bool ret = true;
        ret = ret && (first == rhs.first);
        ret = ret && (second == rhs.second);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bndOrderSt & v, const std::string & NAME ) {
        sc_trace(tf,v.first, NAME + ".first");
        sc_trace(tf,v.second, NAME + ".second");
    }
    inline friend ostream& operator << ( ostream& os,  bndOrderSt const & v ) {
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
        memset(&_ret, 0, bndOrderSt::_byteWidth);
        _ret = second;
        _ret |= (uint16_t)first << (8 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        second = (bndFlagT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
        _pos += 8;
        first = (bndPixelT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
    }
    inline sc_bv<bndOrderSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bndOrderSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = second;
        packed_data.range(15, 8) = first;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bndOrderSt::_bitWidth> packed_data)
    {
        second = (bndFlagT) packed_data.range(7, 0).to_uint64();
        first = (bndPixelT) packed_data.range(15, 8).to_uint64();
    }
    explicit bndOrderSt(sc_bv<bndOrderSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bndOrderSt(
        bndFlagT second_,
        bndPixelT first_) :
        second(second_),
        first(first_)
    {}
    explicit bndOrderSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bndSignSt {
    bndPixelT data; //Pixel payload

    bndSignSt() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const bndSignSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bndSignSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  bndSignSt const & v ) {
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
        memset(&_ret, 0, bndSignSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (bndPixelT)((_src));
    }
    inline sc_bv<bndSignSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bndSignSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = data;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bndSignSt::_bitWidth> packed_data)
    {
        data = (bndPixelT) packed_data.range(7, 0).to_uint64();
    }
    explicit bndSignSt(sc_bv<bndSignSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bndSignSt(
        bndPixelT data_) :
        data(data_)
    {}
    explicit bndSignSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bndNestSt {
    bndPixelT data; //Pixel payload
    bndFlagT tail; //Trailing flag
    bndFlagT flag; //Header flag
    bndWordT word; //Header word

    bndNestSt() {}

    static constexpr uint16_t _bitWidth = 8 + 8 + 8 + 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const bndNestSt & rhs) const {
        bool ret = true;
        ret = ret && (word == rhs.word);
        ret = ret && (flag == rhs.flag);
        ret = ret && (tail == rhs.tail);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bndNestSt & v, const std::string & NAME ) {
        sc_trace(tf,v.word, NAME + ".word");
        sc_trace(tf,v.flag, NAME + ".flag");
        sc_trace(tf,v.tail, NAME + ".tail");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  bndNestSt const & v ) {
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
        memset(&_ret, 0, bndNestSt::_byteWidth);
        _ret = data;
        _ret |= (uint64_t)tail << (8 & 63);
        _ret |= (uint64_t)flag << (16 & 63);
        _ret |= (uint64_t)word << (24 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (bndPixelT)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
        _pos += 8;
        tail = (bndFlagT)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
        _pos += 8;
        flag = (bndFlagT)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
        _pos += 8;
        word = (bndWordT)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
    }
    inline sc_bv<bndNestSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bndNestSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = data;
        packed_data.range(15, 8) = tail;
        packed_data.range(23, 16) = flag;
        packed_data.range(55, 24) = word;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bndNestSt::_bitWidth> packed_data)
    {
        data = (bndPixelT) packed_data.range(7, 0).to_uint64();
        tail = (bndFlagT) packed_data.range(15, 8).to_uint64();
        flag = (bndFlagT) packed_data.range(23, 16).to_uint64();
        word = (bndWordT) packed_data.range(55, 24).to_uint64();
    }
    explicit bndNestSt(sc_bv<bndNestSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bndNestSt(
        bndPixelT data_,
        bndFlagT tail_,
        bndFlagT flag_,
        bndWordT word_) :
        data(data_),
        tail(tail_),
        flag(flag_),
        word(word_)
    {}
    explicit bndNestSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpCppAxis_xpCppAxisTop_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpCppAxis_xpCppAxisTop_test_ns {
class test_xpCppAxisTop_structs {
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
} // namespace xpCppAxis_xpCppAxisTop_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpCppAxis_xpCppAxisTop_test_ns {
using namespace xpCppAxis_xpCppAxisTop_ns;
std::string test_xpCppAxisTop_structs::name(void) { return "test_xpCppAxisTop_structs"; }
void test_xpCppAxisTop_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<bndEqSt>("bndEqSt", patterns);
    roundTrip<bndOrderSt>("bndOrderSt", patterns);
    roundTrip<bndSignSt>("bndSignSt", patterns);
    roundTrip<bndNestSt>("bndNestSt", patterns);
}
} // namespace xpCppAxis_xpCppAxisTop_test_ns

// GENERATED_CODE_END
