
// GENERATED_CODE_PARAM --project=helloWorld --context=helloWorld_tb.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module helloWorld_tb;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace helloWorld_tb_ns {
//constants
inline constexpr uint32_t BUFFER_SIZE = 64;  // Buffer size

} // namespace helloWorld_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace helloWorld_tb_ns {
// types
typedef uint8_t byteT; // [8] Byte
typedef uint64_t qwordT; // [64] 64 bits

} // namespace helloWorld_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace helloWorld_tb_ns {
// enums

} // namespace helloWorld_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace helloWorld_tb_ns {
// structures
struct test_st {
    byteT a; //

    test_st() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const test_st & rhs) const {
        bool ret = true;
        ret = ret && (a == rhs.a);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test_st & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  test_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("a:0x{:02x}",
           (uint64_t) a
        ));
    }
    static const char* getValueType(void) { return( "tracker:cmd" );}
    inline uint64_t getStructValue(void) const { return( a );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (byteT)((_src));
    }
    inline sc_bv<test_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<test_st::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "test_st", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<test_st::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit test_st(const sc_bv<test_st::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit test_st(
        byteT a_) :
        a(a_)
    {}
    explicit test_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test_no_tracker_st {
    byteT a; //

    test_no_tracker_st() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const test_no_tracker_st & rhs) const {
        bool ret = true;
        ret = ret && (a == rhs.a);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test_no_tracker_st & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  test_no_tracker_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("a:0x{:02x}",
           (uint64_t) a
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (byteT)((_src));
    }
    inline sc_bv<test_no_tracker_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<test_no_tracker_st::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "test_no_tracker_st", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<test_no_tracker_st::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit test_no_tracker_st(const sc_bv<test_no_tracker_st::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit test_no_tracker_st(
        byteT a_) :
        a(a_)
    {}
    explicit test_no_tracker_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct data_st {
    qwordT b; //

    data_st() {}

    static constexpr uint16_t _bitWidth = 64;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const data_st & rhs) const {
        bool ret = true;
        ret = ret && (b == rhs.b);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const data_st & v, const std::string & NAME ) {
        sc_trace(tf,v.b, NAME + ".b");
    }
    inline friend ostream& operator << ( ostream& os,  data_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("b:0x{:016x}",
           (uint64_t) b
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = b;
    }
    inline void unpack(const _packedSt &_src)
    {
        b = (qwordT)((_src));
    }
    inline sc_bv<data_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<data_st::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "data_st", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<data_st::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit data_st(const sc_bv<data_st::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit data_st(
        qwordT b_) :
        b(b_)
    {}
    explicit data_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace helloWorld_tb_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace helloWorld_tb_ns {
inline sc_bv<test_st::_bitWidth> testRefPack(const test_st &x);
inline void testRefUnpack(test_st &x, const sc_bv<test_st::_bitWidth> &packed_data);
inline sc_bv<test_no_tracker_st::_bitWidth> testRefPack(const test_no_tracker_st &x);
inline void testRefUnpack(test_no_tracker_st &x, const sc_bv<test_no_tracker_st::_bitWidth> &packed_data);
inline sc_bv<data_st::_bitWidth> testRefPack(const data_st &x);
inline void testRefUnpack(data_st &x, const sc_bv<data_st::_bitWidth> &packed_data);
inline sc_bv<test_st::_bitWidth> testRefPack(const test_st &x)
{
    sc_bv<test_st::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.a;
    return packed_data;
}
inline void testRefUnpack(test_st &x, const sc_bv<test_st::_bitWidth> &packed_data)
{
    x.a = (byteT) packed_data.range(0+8-1, 0).to_uint64();
}
inline sc_bv<test_no_tracker_st::_bitWidth> testRefPack(const test_no_tracker_st &x)
{
    sc_bv<test_no_tracker_st::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.a;
    return packed_data;
}
inline void testRefUnpack(test_no_tracker_st &x, const sc_bv<test_no_tracker_st::_bitWidth> &packed_data)
{
    x.a = (byteT) packed_data.range(0+8-1, 0).to_uint64();
}
inline sc_bv<data_st::_bitWidth> testRefPack(const data_st &x)
{
    sc_bv<data_st::_bitWidth> packed_data;
    packed_data.range(0+64-1, 0) = x.b;
    return packed_data;
}
inline void testRefUnpack(data_st &x, const sc_bv<data_st::_bitWidth> &packed_data)
{
    x.b = (qwordT) packed_data.range(0+64-1, 0).to_uint64();
}
} // namespace helloWorld_tb_ns
export namespace helloWorld_tb_test_ns {
class test_helloWorld_tb_structs {
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
} // namespace helloWorld_tb_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace helloWorld_tb_test_ns {
using namespace helloWorld_tb_ns;
std::string test_helloWorld_tb_structs::name(void) { return "test_helloWorld_tb_structs"; }
void test_helloWorld_tb_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<test_st>("test_st", patterns);
    roundTrip<test_no_tracker_st>("test_no_tracker_st", patterns);
    roundTrip<data_st>("data_st", patterns);
}
} // namespace helloWorld_tb_test_ns

// GENERATED_CODE_END
