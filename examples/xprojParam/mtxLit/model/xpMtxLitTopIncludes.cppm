
// GENERATED_CODE_PARAM --project=xpMtxLit --context=../../yaml/xpMtxLitTop.yaml --mode=module
//

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpMtxLit_xpMtxLitTop;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import xpMtxIp;
using namespace xpMtxIp_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpMtxLit_xpMtxLitTop_ns {
//constants

} // namespace xpMtxLit_xpMtxLitTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpMtxLit_xpMtxLitTop_ns {
// types
typedef uint8_t mlChTagT; // [8] Channel tag; low packed position
typedef uint16_t mlChPixelT; // [12] Channel pixel at the resolved endpoint width
typedef uint8_t mlChMarkT; // [8] Channel trailing marker

} // namespace xpMtxLit_xpMtxLitTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpMtxLit_xpMtxLitTop_ns {
// enums

} // namespace xpMtxLit_xpMtxLitTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpMtxLit_xpMtxLitTop_ns {
// structures
struct mlChSt {
    mlChMarkT mark; //Trailing marker
    mlChPixelT data; //Pixel payload
    mlChTagT tag; //Sample sequence tag

    mlChSt() {}

    static constexpr uint16_t _bitWidth = 8 + 12 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const mlChSt & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const mlChSt & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  mlChSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:02x} data:0x{:03x} mark:0x{:02x}",
           (uint64_t) tag,
           (uint64_t) data,
           (uint64_t) mark
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = mark;
        _ret |= (uint32_t)data << (8 & 31);
        _ret |= (uint32_t)tag << (20 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (mlChMarkT)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
        _pos += 8;
        data = (mlChPixelT)((_src >> (_pos & 31)) & ((1ULL << 12) - 1));
        _pos += 12;
        tag = (mlChTagT)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
    }
    inline sc_bv<mlChSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<mlChSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "mlChSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<mlChSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit mlChSt(const sc_bv<mlChSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit mlChSt(
        mlChMarkT mark_,
        mlChPixelT data_,
        mlChTagT tag_) :
        mark(mark_),
        data(data_),
        tag(tag_)
    {}
    explicit mlChSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpMtxLit_xpMtxLitTop_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpMtxLit_xpMtxLitTop_ns {
inline sc_bv<mlChSt::_bitWidth> testRefPack(const mlChSt &x);
inline void testRefUnpack(mlChSt &x, const sc_bv<mlChSt::_bitWidth> &packed_data);
inline sc_bv<mlChSt::_bitWidth> testRefPack(const mlChSt &x)
{
    sc_bv<mlChSt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.mark;
    packed_data.range(8+12-1, 8) = x.data;
    packed_data.range(20+8-1, 20) = x.tag;
    return packed_data;
}
inline void testRefUnpack(mlChSt &x, const sc_bv<mlChSt::_bitWidth> &packed_data)
{
    x.mark = (mlChMarkT) packed_data.range(0+8-1, 0).to_uint64();
    x.data = (mlChPixelT) packed_data.range(8+12-1, 8).to_uint64();
    x.tag = (mlChTagT) packed_data.range(20+8-1, 20).to_uint64();
}
} // namespace xpMtxLit_xpMtxLitTop_ns
export namespace xpMtxLit_xpMtxLitTop_test_ns {
class test_xpMtxLitTop_structs {
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
} // namespace xpMtxLit_xpMtxLitTop_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpMtxLit_xpMtxLitTop_test_ns {
using namespace xpMtxLit_xpMtxLitTop_ns;
std::string test_xpMtxLitTop_structs::name(void) { return "test_xpMtxLitTop_structs"; }
void test_xpMtxLitTop_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<mlChSt>("mlChSt", patterns);
}
} // namespace xpMtxLit_xpMtxLitTop_test_ns

// GENERATED_CODE_END
