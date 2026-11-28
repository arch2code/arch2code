
// GENERATED_CODE_PARAM --project=uvmReuseLeaf --context=../../yaml/uvmReuseLeaf.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module uvmReuseLeaf;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace uvmReuseLeaf_ns {
//constants

} // namespace uvmReuseLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace uvmReuseLeaf_ns {
// types
typedef uint16_t uvmReuseWordT; // [16] One data word
typedef uint8_t uvmReuseBitT; // [1] A one-bit flag
typedef uint32_t uvmReuseBusT; // [32] Register bus address and data
template<uint32_t UVM_REUSE_OFF_W> using uvmReuseOffT_v = uint64_t; // [max:8] Offset added to each word
template<typename Config> using uvmReuseOffT = uvmReuseOffT_v<Config::UVM_REUSE_OFF_W>;

} // namespace uvmReuseLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace uvmReuseLeaf_ns {
// enums

} // namespace uvmReuseLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace uvmReuseLeaf_ns {
// structures
struct uvmReuseBeatSt {
    uvmReuseBitT last; //Final beat of a packet
    uvmReuseWordT word; //Data word

    uvmReuseBeatSt() {}

    static constexpr uint16_t _bitWidth = 1 + 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const uvmReuseBeatSt & rhs) const {
        bool ret = true;
        ret = ret && (word == rhs.word);
        ret = ret && (last == rhs.last);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmReuseBeatSt & v, const std::string & NAME ) {
        sc_trace(tf,v.word, NAME + ".word");
        sc_trace(tf,v.last, NAME + ".last");
    }
    inline friend ostream& operator << ( ostream& os,  uvmReuseBeatSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("word:0x{:04x} last:0x{:01x}",
           (uint64_t) word,
           (uint64_t) last
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = last;
        _ret |= (uint32_t)word << (1 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        last = (uvmReuseBitT)((_src >> (_pos & 31)) & 1);
        _pos += 1;
        word = (uvmReuseWordT)((_src >> (_pos & 31)) & ((1ULL << 16) - 1));
    }
    inline sc_bv<uvmReuseBeatSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmReuseBeatSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + 31) / 32; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + 31) / 32 - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * 32))) == 0,
                     "uvmReuseBeatSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmReuseBeatSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + 31) / 32; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmReuseBeatSt(const sc_bv<uvmReuseBeatSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmReuseBeatSt(
        uvmReuseBitT last_,
        uvmReuseWordT word_) :
        last(last_),
        word(word_)
    {}
    explicit uvmReuseBeatSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmReuseAddrSt {
    uvmReuseBusT address; //

    uvmReuseAddrSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const uvmReuseAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmReuseAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  uvmReuseAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("address:0x{:08x}",
           (uint64_t) address
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline uvmReuseBusT _getAddress(void) { return( address); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (uvmReuseBusT)((_src));
    }
    inline sc_bv<uvmReuseAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmReuseAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + 31) / 32; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + 31) / 32 - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * 32))) == 0,
                     "uvmReuseAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmReuseAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + 31) / 32; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmReuseAddrSt(const sc_bv<uvmReuseAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmReuseAddrSt(
        uvmReuseBusT address_) :
        address(address_)
    {}
    explicit uvmReuseAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmReuseDataSt {
    uvmReuseBusT data; //

    uvmReuseDataSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const uvmReuseDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmReuseDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  uvmReuseDataSt const & v ) {
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
    inline uvmReuseBusT _getData(void) { return( data); }
    inline void _setData(uvmReuseBusT value) { data = value; }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (uvmReuseBusT)((_src));
    }
    inline sc_bv<uvmReuseDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmReuseDataSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + 31) / 32; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + 31) / 32 - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * 32))) == 0,
                     "uvmReuseDataSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmReuseDataSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + 31) / 32; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmReuseDataSt(const sc_bv<uvmReuseDataSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmReuseDataSt(
        uvmReuseBusT data_) :
        data(data_)
    {}
    explicit uvmReuseDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<uint32_t UVM_REUSE_OFF_W>
struct uvmReuseOffSt_v {
    uvmReuseOffT_v<UVM_REUSE_OFF_W> offset; //Added to each word

    uvmReuseOffSt_v() {}

    static constexpr uint16_t _bitWidth = UVM_REUSE_OFF_W;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const uvmReuseOffSt_v<UVM_REUSE_OFF_W> & rhs) const {
        bool ret = true;
        ret = ret && (offset == rhs.offset);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmReuseOffSt_v<UVM_REUSE_OFF_W> & v, const std::string & NAME ) {
        sc_trace(tf,v.offset, NAME + ".offset");
    }
    inline friend ostream& operator << ( ostream& os,  uvmReuseOffSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("offset:0x{:01x}",
           (uint64_t) offset
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, offset, UVM_REUSE_OFF_W);
        _pos += UVM_REUSE_OFF_W;
    }
    inline void unpack(const _packedSt &_src)
    {
        offset = (uvmReuseOffT_v<UVM_REUSE_OFF_W>)((_src) & (~0ULL >> (64 - (UVM_REUSE_OFF_W))));
    }
    inline sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + 31) / 32; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + 31) / 32 - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * 32))) == 0,
                     "uvmReuseOffSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + 31) / 32; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmReuseOffSt_v(const sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmReuseOffSt_v(
        uvmReuseOffT_v<UVM_REUSE_OFF_W> offset_) :
        offset(offset_)
    {}
    explicit uvmReuseOffSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using uvmReuseOffSt = uvmReuseOffSt_v<Config::UVM_REUSE_OFF_W>;
} // namespace uvmReuseLeaf_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace uvmReuseLeaf_ns {
inline sc_bv<uvmReuseBeatSt::_bitWidth> testRefPack(const uvmReuseBeatSt &x);
inline void testRefUnpack(uvmReuseBeatSt &x, const sc_bv<uvmReuseBeatSt::_bitWidth> &packed_data);
inline sc_bv<uvmReuseAddrSt::_bitWidth> testRefPack(const uvmReuseAddrSt &x);
inline void testRefUnpack(uvmReuseAddrSt &x, const sc_bv<uvmReuseAddrSt::_bitWidth> &packed_data);
inline sc_bv<uvmReuseDataSt::_bitWidth> testRefPack(const uvmReuseDataSt &x);
inline void testRefUnpack(uvmReuseDataSt &x, const sc_bv<uvmReuseDataSt::_bitWidth> &packed_data);
template<uint32_t UVM_REUSE_OFF_W> inline sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> testRefPack(const uvmReuseOffSt_v<UVM_REUSE_OFF_W> &x);
template<uint32_t UVM_REUSE_OFF_W> inline void testRefUnpack(uvmReuseOffSt_v<UVM_REUSE_OFF_W> &x, const sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> &packed_data);
inline sc_bv<uvmReuseBeatSt::_bitWidth> testRefPack(const uvmReuseBeatSt &x)
{
    sc_bv<uvmReuseBeatSt::_bitWidth> packed_data;
    packed_data.range(0+1-1, 0) = x.last;
    packed_data.range(1+16-1, 1) = x.word;
    return packed_data;
}
inline void testRefUnpack(uvmReuseBeatSt &x, const sc_bv<uvmReuseBeatSt::_bitWidth> &packed_data)
{
    x.last = (uvmReuseBitT) packed_data.range(0+1-1, 0).to_uint64();
    x.word = (uvmReuseWordT) packed_data.range(1+16-1, 1).to_uint64();
}
inline sc_bv<uvmReuseAddrSt::_bitWidth> testRefPack(const uvmReuseAddrSt &x)
{
    sc_bv<uvmReuseAddrSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.address;
    return packed_data;
}
inline void testRefUnpack(uvmReuseAddrSt &x, const sc_bv<uvmReuseAddrSt::_bitWidth> &packed_data)
{
    x.address = (uvmReuseBusT) packed_data.range(0+32-1, 0).to_uint64();
}
inline sc_bv<uvmReuseDataSt::_bitWidth> testRefPack(const uvmReuseDataSt &x)
{
    sc_bv<uvmReuseDataSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.data;
    return packed_data;
}
inline void testRefUnpack(uvmReuseDataSt &x, const sc_bv<uvmReuseDataSt::_bitWidth> &packed_data)
{
    x.data = (uvmReuseBusT) packed_data.range(0+32-1, 0).to_uint64();
}
template<uint32_t UVM_REUSE_OFF_W> inline sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> testRefPack(const uvmReuseOffSt_v<UVM_REUSE_OFF_W> &x)
{
    sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+UVM_REUSE_OFF_W-1, _pos) = x.offset;
    _pos += UVM_REUSE_OFF_W;
    return packed_data;
}
template<uint32_t UVM_REUSE_OFF_W> inline void testRefUnpack(uvmReuseOffSt_v<UVM_REUSE_OFF_W> &x, const sc_bv<uvmReuseOffSt_v<UVM_REUSE_OFF_W>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.offset = (uvmReuseOffT_v<UVM_REUSE_OFF_W>) packed_data.range(_pos+UVM_REUSE_OFF_W-1, _pos).to_uint64();
    _pos += UVM_REUSE_OFF_W;
}
} // namespace uvmReuseLeaf_ns
export namespace uvmReuseLeaf_test_ns {
class test_uvmReuseLeaf_structs {
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
} // namespace uvmReuseLeaf_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace uvmReuseLeaf_test_ns {
using namespace uvmReuseLeaf_ns;
struct uvmReuseLeafTestConfigDefault {
    static constexpr uint32_t UVM_REUSE_OFF_W = 4;
};
struct uvmReuseLeafTestConfigMax {
    static constexpr uint32_t UVM_REUSE_OFF_W = 8;
};
std::string test_uvmReuseLeaf_structs::name(void) { return "test_uvmReuseLeaf_structs"; }
void test_uvmReuseLeaf_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<uvmReuseBeatSt>("uvmReuseBeatSt", patterns);
    roundTrip<uvmReuseAddrSt>("uvmReuseAddrSt", patterns);
    roundTrip<uvmReuseDataSt>("uvmReuseDataSt", patterns);
    roundTrip<uvmReuseOffSt<uvmReuseLeafTestConfigDefault>>("uvmReuseOffSt", patterns);
    roundTrip<uvmReuseOffSt<uvmReuseLeafTestConfigMax>>("uvmReuseOffSt", patterns);
}
} // namespace uvmReuseLeaf_test_ns

// GENERATED_CODE_END
