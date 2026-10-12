
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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "bndEqSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<bndEqSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit bndEqSt(const sc_bv<bndEqSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "bndOrderSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<bndOrderSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit bndOrderSt(const sc_bv<bndOrderSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (bndPixelT)((_src));
    }
    inline sc_bv<bndSignSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bndSignSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "bndSignSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<bndSignSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit bndSignSt(const sc_bv<bndSignSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "bndNestSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<bndNestSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit bndNestSt(const sc_bv<bndNestSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
export namespace xpCppAxis_xpCppAxisTop_ns {
inline sc_bv<bndEqSt::_bitWidth> testRefPack(const bndEqSt &x);
inline void testRefUnpack(bndEqSt &x, const sc_bv<bndEqSt::_bitWidth> &packed_data);
inline sc_bv<bndOrderSt::_bitWidth> testRefPack(const bndOrderSt &x);
inline void testRefUnpack(bndOrderSt &x, const sc_bv<bndOrderSt::_bitWidth> &packed_data);
inline sc_bv<bndSignSt::_bitWidth> testRefPack(const bndSignSt &x);
inline void testRefUnpack(bndSignSt &x, const sc_bv<bndSignSt::_bitWidth> &packed_data);
inline sc_bv<bndNestSt::_bitWidth> testRefPack(const bndNestSt &x);
inline void testRefUnpack(bndNestSt &x, const sc_bv<bndNestSt::_bitWidth> &packed_data);
inline sc_bv<bndEqSt::_bitWidth> testRefPack(const bndEqSt &x)
{
    sc_bv<bndEqSt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.data;
    packed_data.range(8+8-1, 8) = x.tag;
    return packed_data;
}
inline void testRefUnpack(bndEqSt &x, const sc_bv<bndEqSt::_bitWidth> &packed_data)
{
    x.data = (bndPixelT) packed_data.range(0+8-1, 0).to_uint64();
    x.tag = (bndTagT) packed_data.range(8+8-1, 8).to_uint64();
}
inline sc_bv<bndOrderSt::_bitWidth> testRefPack(const bndOrderSt &x)
{
    sc_bv<bndOrderSt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.second;
    packed_data.range(8+8-1, 8) = x.first;
    return packed_data;
}
inline void testRefUnpack(bndOrderSt &x, const sc_bv<bndOrderSt::_bitWidth> &packed_data)
{
    x.second = (bndFlagT) packed_data.range(0+8-1, 0).to_uint64();
    x.first = (bndPixelT) packed_data.range(8+8-1, 8).to_uint64();
}
inline sc_bv<bndSignSt::_bitWidth> testRefPack(const bndSignSt &x)
{
    sc_bv<bndSignSt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.data;
    return packed_data;
}
inline void testRefUnpack(bndSignSt &x, const sc_bv<bndSignSt::_bitWidth> &packed_data)
{
    x.data = (bndPixelT) packed_data.range(0+8-1, 0).to_uint64();
}
inline sc_bv<bndNestSt::_bitWidth> testRefPack(const bndNestSt &x)
{
    sc_bv<bndNestSt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.data;
    packed_data.range(8+8-1, 8) = x.tail;
    packed_data.range(16+8-1, 16) = x.flag;
    packed_data.range(24+32-1, 24) = x.word;
    return packed_data;
}
inline void testRefUnpack(bndNestSt &x, const sc_bv<bndNestSt::_bitWidth> &packed_data)
{
    x.data = (bndPixelT) packed_data.range(0+8-1, 0).to_uint64();
    x.tail = (bndFlagT) packed_data.range(8+8-1, 8).to_uint64();
    x.flag = (bndFlagT) packed_data.range(16+8-1, 16).to_uint64();
    x.word = (bndWordT) packed_data.range(24+32-1, 24).to_uint64();
}
} // namespace xpCppAxis_xpCppAxisTop_ns
export namespace xpCppAxis_xpCppAxisTop_test_ns {
class test_xpCppAxisTop_structs {
public:
    static std::string name(void);
    static void test(void);
private:
    template<typename T>
    static void roundTrip(const char* sName, const std::vector<uint8_t>& patterns) {
        for(auto pattern : patterns) {
            roundTripBytes<T>(sName, pattern, 0);
        }
        // Bytes that differ by position expose a field placed a whole number of bytes off.
        roundTripBytes<T>(sName, 0x5b, 0x35);
    }
    template<typename T>
    static void roundTripBytes(const char* sName, uint8_t first, uint8_t step) {
        using P = typename T::_packedSt;
        P words{};
        sc_bv<T::_bitWidth> aInit;
        for (int i = 0; i < T::_byteWidth; i++) {
            uint8_t byte = (uint8_t)(first + i * step);
            int end = std::min((i+1)*8-1, T::_bitWidth-1);
            aInit.range(end, i*8) = byte;
            if constexpr (std::is_array_v<P>) {
                words[i / 8] |= (uint64_t)byte << ((i % 8) * 8);
            } else {
                words |= (P)((uint64_t)byte << (i * 8));
            }
        }
        T ref;
        testRefUnpack(ref, aInit);
        Q_ASSERT(testRefPack(ref) == aInit, std::string(sName) + ": testRefPack(testRefUnpack(pattern)) is not the pattern");
        T b;
        b.unpack(words);
        if (!(b == ref)) {
            cout << ref.prt() << endl << b.prt() << endl;
            Q_ASSERT(false, std::string(sName) + ": unpack() differs from the reference layout");
        }
        T c;
        c.sc_unpack(aInit);
        if (!(c == ref)) {
            cout << ref.prt() << endl << c.prt() << endl;
            Q_ASSERT(false, std::string(sName) + ": sc_unpack() differs from the reference layout");
        }
        P out;
        ref.pack(out);
        sc_bv<T::_bitWidth> outBits;
        for (int i = 0; i < T::_bitWidth; i++) {
            uint64_t word;
            if constexpr (std::is_array_v<P>) {
                word = out[i / 64];
            } else {
                word = (uint64_t)out;
            }
            outBits[i] = (bool)((word >> (i % 64)) & 1);
        }
        if (!(outBits == aInit)) {
            cout << ref.prt() << endl << outBits << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": pack() differs from the reference layout");
        }
        sc_bv<T::_bitWidth> scPacked = ref.sc_pack();
        if (!(scPacked == aInit)) {
            cout << ref.prt() << endl << scPacked << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": sc_pack() differs from the reference layout");
        }
        b.pack(out);
        for (int i = 0; i < T::_bitWidth; i++) {
            uint64_t word;
            if constexpr (std::is_array_v<P>) {
                word = out[i / 64];
            } else {
                word = (uint64_t)out;
            }
            outBits[i] = (bool)((word >> (i % 64)) & 1);
        }
        if (!(outBits == aInit)) {
            cout << b.prt() << endl << outBits << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": pack(unpack(pattern)) is not the pattern");
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
