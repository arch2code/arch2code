
// GENERATED_CODE_PARAM --project=axiDemo --context=axiDemo.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module axiDemo;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import axiDemo_axiStd;
using namespace axiDemo_axiStd_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace axiDemo_ns {
//constants
inline constexpr uint32_t AXI_ADDRESS_WIDTH = 32;  // The width of the AXI address busses
inline constexpr uint32_t AXI_DATA_WIDTH = 32;  // The width of the AXI data busses
inline constexpr uint32_t AXI_STROBE_WIDTH = 4;  // The width of the AXI strobe signals

} // namespace axiDemo_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace axiDemo_ns {
// types
typedef uint32_t axiAddrT; // [32] Address Width
typedef uint32_t axiDataT; // [32] Width of the data bus.
typedef uint8_t axiStrobeT; // [4] Width of the strobe bus.

} // namespace axiDemo_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace axiDemo_ns {
// enums

} // namespace axiDemo_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace axiDemo_ns {
// structures
struct axiAddrSt {
    axiAddrT addr; //

    axiAddrSt() {}

    static constexpr uint16_t _bitWidth = AXI_ADDRESS_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const axiAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (addr == rhs.addr);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const axiAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.addr, NAME + ".addr");
    }
    inline friend ostream& operator << ( ostream& os,  axiAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("addr:0x{:08x}",
           (uint64_t) addr
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = addr;
    }
    inline void unpack(const _packedSt &_src)
    {
        addr = (axiAddrT)((_src));
    }
    inline sc_bv<axiAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<axiAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "axiAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<axiAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit axiAddrSt(const sc_bv<axiAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit axiAddrSt(
        axiAddrT addr_) :
        addr(addr_)
    {}
    explicit axiAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct axiDataSt {
    axiDataT data; //

    axiDataSt() {}

    static constexpr uint16_t _bitWidth = AXI_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const axiDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const axiDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  axiDataSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:08x}",
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
        data = (axiDataT)((_src));
    }
    inline sc_bv<axiDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<axiDataSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "axiDataSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<axiDataSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit axiDataSt(const sc_bv<axiDataSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit axiDataSt(
        axiDataT data_) :
        data(data_)
    {}
    explicit axiDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct axiStrobeSt {
    axiStrobeT strobe; //

    axiStrobeSt() {}

    static constexpr uint16_t _bitWidth = AXI_STROBE_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const axiStrobeSt & rhs) const {
        bool ret = true;
        ret = ret && (strobe == rhs.strobe);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const axiStrobeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.strobe, NAME + ".strobe");
    }
    inline friend ostream& operator << ( ostream& os,  axiStrobeSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("strobe:0x{:01x}",
           (uint64_t) strobe
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = strobe;
    }
    inline void unpack(const _packedSt &_src)
    {
        strobe = (axiStrobeT)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<axiStrobeSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<axiStrobeSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "axiStrobeSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<axiStrobeSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit axiStrobeSt(const sc_bv<axiStrobeSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit axiStrobeSt(
        axiStrobeT strobe_) :
        strobe(strobe_)
    {}
    explicit axiStrobeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace axiDemo_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace axiDemo_ns {
inline sc_bv<axiAddrSt::_bitWidth> testRefPack(const axiAddrSt &x);
inline void testRefUnpack(axiAddrSt &x, const sc_bv<axiAddrSt::_bitWidth> &packed_data);
inline sc_bv<axiDataSt::_bitWidth> testRefPack(const axiDataSt &x);
inline void testRefUnpack(axiDataSt &x, const sc_bv<axiDataSt::_bitWidth> &packed_data);
inline sc_bv<axiStrobeSt::_bitWidth> testRefPack(const axiStrobeSt &x);
inline void testRefUnpack(axiStrobeSt &x, const sc_bv<axiStrobeSt::_bitWidth> &packed_data);
inline sc_bv<axiAddrSt::_bitWidth> testRefPack(const axiAddrSt &x)
{
    sc_bv<axiAddrSt::_bitWidth> packed_data;
    packed_data.range(0+AXI_ADDRESS_WIDTH-1, 0) = x.addr;
    return packed_data;
}
inline void testRefUnpack(axiAddrSt &x, const sc_bv<axiAddrSt::_bitWidth> &packed_data)
{
    x.addr = (axiAddrT) packed_data.range(0+AXI_ADDRESS_WIDTH-1, 0).to_uint64();
}
inline sc_bv<axiDataSt::_bitWidth> testRefPack(const axiDataSt &x)
{
    sc_bv<axiDataSt::_bitWidth> packed_data;
    packed_data.range(0+AXI_DATA_WIDTH-1, 0) = x.data;
    return packed_data;
}
inline void testRefUnpack(axiDataSt &x, const sc_bv<axiDataSt::_bitWidth> &packed_data)
{
    x.data = (axiDataT) packed_data.range(0+AXI_DATA_WIDTH-1, 0).to_uint64();
}
inline sc_bv<axiStrobeSt::_bitWidth> testRefPack(const axiStrobeSt &x)
{
    sc_bv<axiStrobeSt::_bitWidth> packed_data;
    packed_data.range(0+AXI_STROBE_WIDTH-1, 0) = x.strobe;
    return packed_data;
}
inline void testRefUnpack(axiStrobeSt &x, const sc_bv<axiStrobeSt::_bitWidth> &packed_data)
{
    x.strobe = (axiStrobeT) packed_data.range(0+AXI_STROBE_WIDTH-1, 0).to_uint64();
}
} // namespace axiDemo_ns
export namespace axiDemo_test_ns {
class test_axiDemo_structs {
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
} // namespace axiDemo_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace axiDemo_test_ns {
using namespace axiDemo_ns;
std::string test_axiDemo_structs::name(void) { return "test_axiDemo_structs"; }
void test_axiDemo_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<axiAddrSt>("axiAddrSt", patterns);
    roundTrip<axiDataSt>("axiDataSt", patterns);
    roundTrip<axiStrobeSt>("axiStrobeSt", patterns);
}
} // namespace axiDemo_test_ns

// GENERATED_CODE_END
