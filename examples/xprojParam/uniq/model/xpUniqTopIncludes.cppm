
// GENERATED_CODE_PARAM --project=xpUniq --context=../../yaml/xpUniqTop.yaml --mode=module
//

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpUniq_xpUniqTop;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import xpGain_xpGainUniq;
import xpFilter_xpFilterUniq;
import xpSink_xpSinkUniq;
using namespace xpGain_xpGainUniq_ns;
using namespace xpFilter_xpFilterUniq_ns;
using namespace xpSink_xpSinkUniq_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpUniq_xpUniqTop_ns {
//constants

} // namespace xpUniq_xpUniqTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpUniq_xpUniqTop_ns {
// types
typedef uint8_t boundaryTagT; // [4] Literal boundary tag; matches each stage's tag field
typedef uint8_t boundaryPixelT; // [8] Literal boundary pixel; matches each stage's data field at width 8

} // namespace xpUniq_xpUniqTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpUniq_xpUniqTop_ns {
// enums

} // namespace xpUniq_xpUniqTop_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpUniq_xpUniqTop_ns {
// structures
struct boundarySt {
    boundaryPixelT data; //Pixel payload
    boundaryTagT tag; //Sample sequence tag

    boundarySt() {}

    static constexpr uint16_t _bitWidth = 8 + 4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const boundarySt & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const boundarySt & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  boundarySt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:01x} data:0x{:02x}",
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
        data = (boundaryPixelT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
        _pos += 8;
        tag = (boundaryTagT)((_src >> (_pos & 15)) & ((1ULL << 4) - 1));
    }
    inline sc_bv<boundarySt::_bitWidth> sc_pack(void) const
    {
        sc_bv<boundarySt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "boundarySt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<boundarySt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit boundarySt(const sc_bv<boundarySt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit boundarySt(
        boundaryPixelT data_,
        boundaryTagT tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit boundarySt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpUniq_xpUniqTop_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpUniq_xpUniqTop_ns {
inline sc_bv<boundarySt::_bitWidth> testRefPack(const boundarySt &x);
inline void testRefUnpack(boundarySt &x, const sc_bv<boundarySt::_bitWidth> &packed_data);
inline sc_bv<boundarySt::_bitWidth> testRefPack(const boundarySt &x)
{
    sc_bv<boundarySt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.data;
    packed_data.range(8+4-1, 8) = x.tag;
    return packed_data;
}
inline void testRefUnpack(boundarySt &x, const sc_bv<boundarySt::_bitWidth> &packed_data)
{
    x.data = (boundaryPixelT) packed_data.range(0+8-1, 0).to_uint64();
    x.tag = (boundaryTagT) packed_data.range(8+4-1, 8).to_uint64();
}
} // namespace xpUniq_xpUniqTop_ns
export namespace xpUniq_xpUniqTop_test_ns {
class test_xpUniqTop_structs {
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
} // namespace xpUniq_xpUniqTop_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpUniq_xpUniqTop_test_ns {
using namespace xpUniq_xpUniqTop_ns;
std::string test_xpUniqTop_structs::name(void) { return "test_xpUniqTop_structs"; }
void test_xpUniqTop_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<boundarySt>("boundarySt", patterns);
}
} // namespace xpUniq_xpUniqTop_test_ns

// GENERATED_CODE_END
