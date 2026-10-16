
// GENERATED_CODE_PARAM --project=xif --context=xif.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xif;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xif_ns {
//constants

} // namespace xif_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xif_ns {
// types
template<uint32_t DATA_WIDTH> using streamDataT_v = uint64_t; // [max:32] Parameterized stream payload word
template<typename Config> using streamDataT = streamDataT_v<Config::DATA_WIDTH>;
typedef uint16_t streamBndryDataT; // [16] Non-parameterized boundary payload word (matches DATA_WIDTH=16)

} // namespace xif_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xif_ns {
// enums

} // namespace xif_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xif_ns {
// structures
template<uint32_t DATA_WIDTH>
struct streamSt_v {
    streamDataT_v<DATA_WIDTH> data; //Parameterized stream payload

    streamSt_v() {}

    static constexpr uint16_t _bitWidth = DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const streamSt_v<DATA_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const streamSt_v<DATA_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  streamSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:04x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, DATA_WIDTH);
        _pos += DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (streamDataT_v<DATA_WIDTH>)((_src) & (~0ULL >> (64 - (DATA_WIDTH))));
    }
    inline sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "streamSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit streamSt_v(const sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit streamSt_v(
        streamDataT_v<DATA_WIDTH> data_) :
        data(data_)
    {}
    explicit streamSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using streamSt = streamSt_v<Config::DATA_WIDTH>;
struct streamBndrySt {
    streamBndryDataT data; //Boundary payload; packed layout matches streamSt<dutV0>

    streamBndrySt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const streamBndrySt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const streamBndrySt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  streamBndrySt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:04x}",
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
        data = (streamBndryDataT)((_src));
    }
    inline sc_bv<streamBndrySt::_bitWidth> sc_pack(void) const
    {
        sc_bv<streamBndrySt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "streamBndrySt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<streamBndrySt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit streamBndrySt(const sc_bv<streamBndrySt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit streamBndrySt(
        streamBndryDataT data_) :
        data(data_)
    {}
    explicit streamBndrySt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xif_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xif_ns {
template<uint32_t DATA_WIDTH> inline sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> testRefPack(const streamSt_v<DATA_WIDTH> &x);
template<uint32_t DATA_WIDTH> inline void testRefUnpack(streamSt_v<DATA_WIDTH> &x, const sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> &packed_data);
inline sc_bv<streamBndrySt::_bitWidth> testRefPack(const streamBndrySt &x);
inline void testRefUnpack(streamBndrySt &x, const sc_bv<streamBndrySt::_bitWidth> &packed_data);
template<uint32_t DATA_WIDTH> inline sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> testRefPack(const streamSt_v<DATA_WIDTH> &x)
{
    sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+DATA_WIDTH-1, _pos) = x.data;
    _pos += DATA_WIDTH;
    return packed_data;
}
template<uint32_t DATA_WIDTH> inline void testRefUnpack(streamSt_v<DATA_WIDTH> &x, const sc_bv<streamSt_v<DATA_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.data = (streamDataT_v<DATA_WIDTH>) packed_data.range(_pos+DATA_WIDTH-1, _pos).to_uint64();
    _pos += DATA_WIDTH;
}
inline sc_bv<streamBndrySt::_bitWidth> testRefPack(const streamBndrySt &x)
{
    sc_bv<streamBndrySt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.data;
    return packed_data;
}
inline void testRefUnpack(streamBndrySt &x, const sc_bv<streamBndrySt::_bitWidth> &packed_data)
{
    x.data = (streamBndryDataT) packed_data.range(0+16-1, 0).to_uint64();
}
} // namespace xif_ns
export namespace xif_test_ns {
class test_xif_structs {
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
} // namespace xif_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xif_test_ns {
using namespace xif_ns;
struct xifTestConfigDefault {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};
struct xifTestConfigMax {
    static constexpr uint32_t DATA_WIDTH = 32;
    static constexpr uint32_t FRAME_HEIGHT = 16;
    static constexpr uint32_t FRAME_WIDTH = 16;
};
std::string test_xif_structs::name(void) { return "test_xif_structs"; }
void test_xif_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<streamSt<xifTestConfigDefault>>("streamSt", patterns);
    roundTrip<streamSt<xifTestConfigMax>>("streamSt", patterns);
    roundTrip<streamBndrySt>("streamBndrySt", patterns);
}
} // namespace xif_test_ns

// GENERATED_CODE_END
