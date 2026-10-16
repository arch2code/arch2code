
// GENERATED_CODE_PARAM --project=ip_test --context=../../leaf/yaml/ipLeaf.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module ip_test_ipLeaf;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_test_ipLeaf_ns {
//constants

} // namespace ip_test_ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_test_ipLeaf_ns {
// types
template<uint32_t LEAF_MEM_DEPTH> using ipLeafMemAddrT_v = uint64_t; // [max:3] Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)
template<typename Config> using ipLeafMemAddrT = ipLeafMemAddrT_v<Config::LEAF_MEM_DEPTH>;
template<uint32_t LEAF_DATA_WIDTH> using ipLeafDataT_v = uint64_t; // [max:16] ipLeaf data word, parameterizable
template<typename Config> using ipLeafDataT = ipLeafDataT_v<Config::LEAF_DATA_WIDTH>;

} // namespace ip_test_ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_test_ipLeaf_ns {
// enums

} // namespace ip_test_ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ip_test_ipLeaf_ns {
// structures
template<uint32_t LEAF_DATA_WIDTH>
struct ipLeafMemSt_v {
    ipLeafDataT_v<LEAF_DATA_WIDTH> data; //Leaf memory word

    ipLeafMemSt_v() {}

    static constexpr uint16_t _bitWidth = LEAF_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const ipLeafMemSt_v<LEAF_DATA_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipLeafMemSt_v<LEAF_DATA_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  ipLeafMemSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:01x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, LEAF_DATA_WIDTH);
        _pos += LEAF_DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (ipLeafDataT_v<LEAF_DATA_WIDTH>)((_src) & (~0ULL >> (64 - (LEAF_DATA_WIDTH))));
    }
    inline sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "ipLeafMemSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit ipLeafMemSt_v(const sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit ipLeafMemSt_v(
        ipLeafDataT_v<LEAF_DATA_WIDTH> data_) :
        data(data_)
    {}
    explicit ipLeafMemSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using ipLeafMemSt = ipLeafMemSt_v<Config::LEAF_DATA_WIDTH>;
template<uint32_t LEAF_MEM_DEPTH>
struct ipLeafMemAddrSt_v {
    ipLeafMemAddrT_v<LEAF_MEM_DEPTH> address; //Leaf memory address

    ipLeafMemAddrSt_v() {}

    static constexpr uint16_t _bitWidth = clog2(LEAF_MEM_DEPTH);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const ipLeafMemAddrSt_v<LEAF_MEM_DEPTH> & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipLeafMemAddrSt_v<LEAF_MEM_DEPTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  ipLeafMemAddrSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("address:0x{:01x}",
           (uint64_t) address
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, address, clog2(LEAF_MEM_DEPTH));
        _pos += clog2(LEAF_MEM_DEPTH);
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ipLeafMemAddrT_v<LEAF_MEM_DEPTH>)((_src) & (~0ULL >> (64 - (clog2(LEAF_MEM_DEPTH)))));
    }
    inline sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "ipLeafMemAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit ipLeafMemAddrSt_v(const sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit ipLeafMemAddrSt_v(
        ipLeafMemAddrT_v<LEAF_MEM_DEPTH> address_) :
        address(address_)
    {}
    explicit ipLeafMemAddrSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using ipLeafMemAddrSt = ipLeafMemAddrSt_v<Config::LEAF_MEM_DEPTH>;
} // namespace ip_test_ipLeaf_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ip_test_ipLeaf_ns {
template<uint32_t LEAF_DATA_WIDTH> inline sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> testRefPack(const ipLeafMemSt_v<LEAF_DATA_WIDTH> &x);
template<uint32_t LEAF_DATA_WIDTH> inline void testRefUnpack(ipLeafMemSt_v<LEAF_DATA_WIDTH> &x, const sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> &packed_data);
template<uint32_t LEAF_MEM_DEPTH> inline sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> testRefPack(const ipLeafMemAddrSt_v<LEAF_MEM_DEPTH> &x);
template<uint32_t LEAF_MEM_DEPTH> inline void testRefUnpack(ipLeafMemAddrSt_v<LEAF_MEM_DEPTH> &x, const sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> &packed_data);
template<uint32_t LEAF_DATA_WIDTH> inline sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> testRefPack(const ipLeafMemSt_v<LEAF_DATA_WIDTH> &x)
{
    sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+LEAF_DATA_WIDTH-1, _pos) = x.data;
    _pos += LEAF_DATA_WIDTH;
    return packed_data;
}
template<uint32_t LEAF_DATA_WIDTH> inline void testRefUnpack(ipLeafMemSt_v<LEAF_DATA_WIDTH> &x, const sc_bv<ipLeafMemSt_v<LEAF_DATA_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.data = (ipLeafDataT_v<LEAF_DATA_WIDTH>) packed_data.range(_pos+LEAF_DATA_WIDTH-1, _pos).to_uint64();
    _pos += LEAF_DATA_WIDTH;
}
template<uint32_t LEAF_MEM_DEPTH> inline sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> testRefPack(const ipLeafMemAddrSt_v<LEAF_MEM_DEPTH> &x)
{
    sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+clog2(LEAF_MEM_DEPTH)-1, _pos) = x.address;
    _pos += clog2(LEAF_MEM_DEPTH);
    return packed_data;
}
template<uint32_t LEAF_MEM_DEPTH> inline void testRefUnpack(ipLeafMemAddrSt_v<LEAF_MEM_DEPTH> &x, const sc_bv<ipLeafMemAddrSt_v<LEAF_MEM_DEPTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.address = (ipLeafMemAddrT_v<LEAF_MEM_DEPTH>) packed_data.range(_pos+clog2(LEAF_MEM_DEPTH)-1, _pos).to_uint64();
    _pos += clog2(LEAF_MEM_DEPTH);
}
} // namespace ip_test_ipLeaf_ns
export namespace ip_test_ipLeaf_test_ns {
class test_ipLeaf_structs {
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
} // namespace ip_test_ipLeaf_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ip_test_ipLeaf_test_ns {
using namespace ip_test_ipLeaf_ns;
struct ipLeafTestConfigDefault {
    static constexpr uint32_t LEAF_DATA_WIDTH = 4;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};
struct ipLeafTestConfigMid {
    static constexpr uint32_t LEAF_DATA_WIDTH = 8;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};
struct ipLeafTestConfigMax {
    static constexpr uint32_t LEAF_DATA_WIDTH = 16;
    static constexpr uint32_t LEAF_MEM_DEPTH = 8;
};
std::string test_ipLeaf_structs::name(void) { return "test_ipLeaf_structs"; }
void test_ipLeaf_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<ipLeafMemSt<ipLeafTestConfigDefault>>("ipLeafMemSt", patterns);
    roundTrip<ipLeafMemSt<ipLeafTestConfigMid>>("ipLeafMemSt", patterns);
    roundTrip<ipLeafMemSt<ipLeafTestConfigMax>>("ipLeafMemSt", patterns);
    roundTrip<ipLeafMemAddrSt<ipLeafTestConfigDefault>>("ipLeafMemAddrSt", patterns);
    roundTrip<ipLeafMemAddrSt<ipLeafTestConfigMid>>("ipLeafMemAddrSt", patterns);
    roundTrip<ipLeafMemAddrSt<ipLeafTestConfigMax>>("ipLeafMemAddrSt", patterns);
}
} // namespace ip_test_ipLeaf_test_ns

// GENERATED_CODE_END
