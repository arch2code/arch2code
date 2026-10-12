
// GENERATED_CODE_PARAM --project=simple --context=simple.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module simple;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace simple_ns {
//constants
inline constexpr uint32_t NUM_TAGS = 32;  // number of tags
inline constexpr uint32_t NUM_TAGS_LOG2 = 5;  // log2 of number of tags

} // namespace simple_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace simple_ns {
// types
typedef uint8_t tag; // [5] tag

} // namespace simple_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace simple_ns {
// enums

} // namespace simple_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace simple_ns {
// structures
struct tag_st {
    tag tagId; //tag id

    tag_st() {}

    static constexpr uint16_t _bitWidth = NUM_TAGS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const tag_st & rhs) const {
        bool ret = true;
        ret = ret && (tagId == rhs.tagId);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tag_st & v, const std::string & NAME ) {
        sc_trace(tf,v.tagId, NAME + ".tagId");
    }
    inline friend ostream& operator << ( ostream& os,  tag_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tagId:0x{:02x}",
           (uint64_t) tagId
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = tagId;
    }
    inline void unpack(const _packedSt &_src)
    {
        tagId = (tag)((_src) & ((1ULL << 5) - 1));
    }
    inline sc_bv<tag_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<tag_st::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "tag_st", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<tag_st::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit tag_st(const sc_bv<tag_st::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit tag_st(
        tag tagId_) :
        tagId(tagId_)
    {}
    explicit tag_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace simple_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace simple_ns {
inline sc_bv<tag_st::_bitWidth> testRefPack(const tag_st &x);
inline void testRefUnpack(tag_st &x, const sc_bv<tag_st::_bitWidth> &packed_data);
inline sc_bv<tag_st::_bitWidth> testRefPack(const tag_st &x)
{
    sc_bv<tag_st::_bitWidth> packed_data;
    packed_data.range(0+NUM_TAGS_LOG2-1, 0) = x.tagId;
    return packed_data;
}
inline void testRefUnpack(tag_st &x, const sc_bv<tag_st::_bitWidth> &packed_data)
{
    x.tagId = (tag) packed_data.range(0+NUM_TAGS_LOG2-1, 0).to_uint64();
}
} // namespace simple_ns
export namespace simple_test_ns {
class test_simple_structs {
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
} // namespace simple_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace simple_test_ns {
using namespace simple_ns;
std::string test_simple_structs::name(void) { return "test_simple_structs"; }
void test_simple_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<tag_st>("tag_st", patterns);
}
} // namespace simple_test_ns

// GENERATED_CODE_END
