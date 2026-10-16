
// GENERATED_CODE_PARAM --project=mixed --context=mixedBlockC.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module mixed_mixedBlockC;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace mixed_mixedBlockC_ns {
//constants
inline constexpr uint32_t CSIZE = 2;  // The size of C
inline constexpr uint32_t CSIZE_PLUS = 3;  // The size of C plus 1

} // namespace mixed_mixedBlockC_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace mixed_mixedBlockC_ns {
// types
typedef uint8_t cSizeT; // [2] size of c
typedef uint8_t cSizePlusT; // [3] size of c plus 1
typedef uint16_t cBiggerT; // [13] yet another type

} // namespace mixed_mixedBlockC_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace mixed_mixedBlockC_ns {
// enums

} // namespace mixed_mixedBlockC_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace mixed_mixedBlockC_ns {
// structures
struct seeSt {
    cSizePlusT variablec2; //Three bits of C
    cSizeT variablec; //Two bits of C

    seeSt() {}

    static constexpr uint16_t _bitWidth = CSIZE_PLUS + CSIZE;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const seeSt & rhs) const {
        bool ret = true;
        ret = ret && (variablec == rhs.variablec);
        ret = ret && (variablec2 == rhs.variablec2);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const seeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.variablec, NAME + ".variablec");
        sc_trace(tf,v.variablec2, NAME + ".variablec2");
    }
    inline friend ostream& operator << ( ostream& os,  seeSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("variablec:0x{:01x} variablec2:0x{:01x}",
           (uint64_t) variablec,
           (uint64_t) variablec2
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = variablec2;
        _ret |= (uint8_t)variablec << (3 & 7);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        variablec2 = (cSizePlusT)((_src >> (_pos & 7)) & ((1ULL << 3) - 1));
        _pos += 3;
        variablec = (cSizeT)((_src >> (_pos & 7)) & ((1ULL << 2) - 1));
    }
    inline sc_bv<seeSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<seeSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "seeSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<seeSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit seeSt(const sc_bv<seeSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit seeSt(
        cSizePlusT variablec2_,
        cSizeT variablec_) :
        variablec2(variablec2_),
        variablec(variablec_)
    {}
    explicit seeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cHeaderSt {
    cBiggerT hdr; //

    cHeaderSt() {}

    static constexpr uint16_t _bitWidth = 13;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const cHeaderSt & rhs) const {
        bool ret = true;
        ret = ret && (hdr == rhs.hdr);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cHeaderSt & v, const std::string & NAME ) {
        sc_trace(tf,v.hdr, NAME + ".hdr");
    }
    inline friend ostream& operator << ( ostream& os,  cHeaderSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("hdr:0x{:04x}",
           (uint64_t) hdr
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = hdr;
    }
    inline void unpack(const _packedSt &_src)
    {
        hdr = (cBiggerT)((_src) & ((1ULL << 13) - 1));
    }
    inline sc_bv<cHeaderSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<cHeaderSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "cHeaderSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<cHeaderSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit cHeaderSt(const sc_bv<cHeaderSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit cHeaderSt(
        cBiggerT hdr_) :
        hdr(hdr_)
    {}
    explicit cHeaderSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace mixed_mixedBlockC_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace mixed_mixedBlockC_ns {
inline sc_bv<seeSt::_bitWidth> testRefPack(const seeSt &x);
inline void testRefUnpack(seeSt &x, const sc_bv<seeSt::_bitWidth> &packed_data);
inline sc_bv<cHeaderSt::_bitWidth> testRefPack(const cHeaderSt &x);
inline void testRefUnpack(cHeaderSt &x, const sc_bv<cHeaderSt::_bitWidth> &packed_data);
inline sc_bv<seeSt::_bitWidth> testRefPack(const seeSt &x)
{
    sc_bv<seeSt::_bitWidth> packed_data;
    packed_data.range(0+CSIZE_PLUS-1, 0) = x.variablec2;
    packed_data.range(3+CSIZE-1, 3) = x.variablec;
    return packed_data;
}
inline void testRefUnpack(seeSt &x, const sc_bv<seeSt::_bitWidth> &packed_data)
{
    x.variablec2 = (cSizePlusT) packed_data.range(0+CSIZE_PLUS-1, 0).to_uint64();
    x.variablec = (cSizeT) packed_data.range(3+CSIZE-1, 3).to_uint64();
}
inline sc_bv<cHeaderSt::_bitWidth> testRefPack(const cHeaderSt &x)
{
    sc_bv<cHeaderSt::_bitWidth> packed_data;
    packed_data.range(0+13-1, 0) = x.hdr;
    return packed_data;
}
inline void testRefUnpack(cHeaderSt &x, const sc_bv<cHeaderSt::_bitWidth> &packed_data)
{
    x.hdr = (cBiggerT) packed_data.range(0+13-1, 0).to_uint64();
}
} // namespace mixed_mixedBlockC_ns
export namespace mixed_mixedBlockC_test_ns {
class test_mixedBlockC_structs {
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
} // namespace mixed_mixedBlockC_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace mixed_mixedBlockC_test_ns {
using namespace mixed_mixedBlockC_ns;
std::string test_mixedBlockC_structs::name(void) { return "test_mixedBlockC_structs"; }
void test_mixedBlockC_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<seeSt>("seeSt", patterns);
    roundTrip<cHeaderSt>("cHeaderSt", patterns);
}
} // namespace mixed_mixedBlockC_test_ns

// GENERATED_CODE_END
