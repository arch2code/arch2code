
// GENERATED_CODE_PARAM --project=xpCppAxis --context=../../yaml/xpCppWrap.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpCppAxis_xpCppWrap;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import xpCppLeaf;
using namespace xpCppLeaf_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpCppAxis_xpCppWrap_ns {
//constants

} // namespace xpCppAxis_xpCppWrap_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpCppAxis_xpCppWrap_ns {
// types
template<typename Config> using wrapPixelT = uint64_t; // [max:32] Parameterizable pixel word
typedef uint8_t wrapTagT; // [8] Sample sequence tag
typedef uint32_t wrapWordT; // [32] 32-bit header word
typedef uint8_t wrapFlagT; // [8] 8-bit header flag

} // namespace xpCppAxis_xpCppWrap_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpCppAxis_xpCppWrap_ns {
// enums

} // namespace xpCppAxis_xpCppWrap_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpCppAxis_xpCppWrap_ns {
// structures
template<typename Config>
struct wrapEqSt {
    wrapPixelT<Config> data; //Pixel payload
    wrapTagT tag; //Sample sequence tag

    wrapEqSt() {}

    static constexpr uint16_t _bitWidth = Config::WRAP_PIXEL_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const wrapEqSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapEqSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  wrapEqSt const & v ) {
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
        memset(&_ret, 0, wrapEqSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::WRAP_PIXEL_WIDTH);
        _pos += Config::WRAP_PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (wrapPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::WRAP_PIXEL_WIDTH)) - 1));
        _pos += Config::WRAP_PIXEL_WIDTH;
        tag = (wrapTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<wrapEqSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapEqSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::WRAP_PIXEL_WIDTH-1, _pos) = data;
        _pos += Config::WRAP_PIXEL_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<wrapEqSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (wrapPixelT<Config>) packed_data.range(_pos+Config::WRAP_PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::WRAP_PIXEL_WIDTH;
        tag = (wrapTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit wrapEqSt(sc_bv<wrapEqSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit wrapEqSt(
        wrapPixelT<Config> data_,
        wrapTagT tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit wrapEqSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct wrapOrderSt {
    wrapFlagT second; //Literal member at the high packed position
    wrapPixelT<Config> first; //Parameterizable member at the low packed position

    wrapOrderSt() {}

    static constexpr uint16_t _bitWidth = 8 + Config::WRAP_PIXEL_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const wrapOrderSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (first == rhs.first);
        ret = ret && (second == rhs.second);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapOrderSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.first, NAME + ".first");
        sc_trace(tf,v.second, NAME + ".second");
    }
    inline friend ostream& operator << ( ostream& os,  wrapOrderSt const & v ) {
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
        memset(&_ret, 0, wrapOrderSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, second, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, first, Config::WRAP_PIXEL_WIDTH);
        _pos += Config::WRAP_PIXEL_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        second = (wrapFlagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        first = (wrapPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::WRAP_PIXEL_WIDTH)) - 1));
    }
    inline sc_bv<wrapOrderSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapOrderSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+8-1, _pos) = second;
        _pos += 8;
        packed_data.range(_pos+Config::WRAP_PIXEL_WIDTH-1, _pos) = first;
        _pos += Config::WRAP_PIXEL_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<wrapOrderSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        second = (wrapFlagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        first = (wrapPixelT<Config>) packed_data.range(_pos+Config::WRAP_PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::WRAP_PIXEL_WIDTH;
    }
    explicit wrapOrderSt(sc_bv<wrapOrderSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit wrapOrderSt(
        wrapFlagT second_,
        wrapPixelT<Config> first_) :
        second(second_),
        first(first_)
    {}
    explicit wrapOrderSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct wrapSignSt {
    wrapPixelT<Config> data; //Pixel payload

    wrapSignSt() {}

    static constexpr uint16_t _bitWidth = Config::WRAP_PIXEL_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const wrapSignSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapSignSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  wrapSignSt const & v ) {
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
        memset(&_ret, 0, wrapSignSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::WRAP_PIXEL_WIDTH);
        _pos += Config::WRAP_PIXEL_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (wrapPixelT<Config>)((_src) & ((1ULL << (Config::WRAP_PIXEL_WIDTH)) - 1));
    }
    inline sc_bv<wrapSignSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapSignSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::WRAP_PIXEL_WIDTH-1, _pos) = data;
        _pos += Config::WRAP_PIXEL_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<wrapSignSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (wrapPixelT<Config>) packed_data.range(_pos+Config::WRAP_PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::WRAP_PIXEL_WIDTH;
    }
    explicit wrapSignSt(sc_bv<wrapSignSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit wrapSignSt(
        wrapPixelT<Config> data_) :
        data(data_)
    {}
    explicit wrapSignSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct wrapNestHdrSt {
    wrapFlagT flag; //Header flag
    wrapWordT word; //Header word

    wrapNestHdrSt() {}

    static constexpr uint16_t _bitWidth = 8 + 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const wrapNestHdrSt & rhs) const {
        bool ret = true;
        ret = ret && (word == rhs.word);
        ret = ret && (flag == rhs.flag);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapNestHdrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.word, NAME + ".word");
        sc_trace(tf,v.flag, NAME + ".flag");
    }
    inline friend ostream& operator << ( ostream& os,  wrapNestHdrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("word:0x{:08x} flag:0x{:02x}",
           (uint64_t) word,
           (uint64_t) flag
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, wrapNestHdrSt::_byteWidth);
        _ret = flag;
        _ret |= (uint64_t)word << (8 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        flag = (wrapFlagT)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
        _pos += 8;
        word = (wrapWordT)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
    }
    inline sc_bv<wrapNestHdrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapNestHdrSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = flag;
        packed_data.range(39, 8) = word;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<wrapNestHdrSt::_bitWidth> packed_data)
    {
        flag = (wrapFlagT) packed_data.range(7, 0).to_uint64();
        word = (wrapWordT) packed_data.range(39, 8).to_uint64();
    }
    explicit wrapNestHdrSt(sc_bv<wrapNestHdrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit wrapNestHdrSt(
        wrapFlagT flag_,
        wrapWordT word_) :
        flag(flag_),
        word(word_)
    {}
    explicit wrapNestHdrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct wrapNestSt {
    wrapPixelT<Config> data; //Pixel payload
    wrapFlagT tail; //Trailing flag
    wrapNestHdrSt hdr; //Nested header

    wrapNestSt() {}

    static constexpr uint16_t _bitWidth = Config::WRAP_PIXEL_WIDTH + 8 + wrapNestHdrSt::_bitWidth;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const wrapNestSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (hdr == rhs.hdr);
        ret = ret && (tail == rhs.tail);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapNestSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.hdr, NAME + ".hdr");
        sc_trace(tf,v.tail, NAME + ".tail");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  wrapNestSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("hdr:<{}> tail:0x{:02x} data:0x{:02x}",
           hdr.prt(all),
           (uint64_t) tail,
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, wrapNestSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::WRAP_PIXEL_WIDTH);
        _pos += Config::WRAP_PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tail, 8);
        _pos += 8;
        {
            wrapNestHdrSt::_packedSt _tmp{0};
            hdr.pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, _tmp, wrapNestHdrSt::_bitWidth);
            _pos += wrapNestHdrSt::_bitWidth;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (wrapPixelT<Config>)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (Config::WRAP_PIXEL_WIDTH)) - 1));
        _pos += Config::WRAP_PIXEL_WIDTH;
        tail = (wrapFlagT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        {
            wrapNestHdrSt::_packedSt _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, wrapNestHdrSt::_bitWidth);
            hdr.unpack(_tmp);
        }
    }
    inline sc_bv<wrapNestSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapNestSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::WRAP_PIXEL_WIDTH-1, _pos) = data;
        _pos += Config::WRAP_PIXEL_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tail;
        _pos += 8;
        packed_data.range(_pos+wrapNestHdrSt::_bitWidth-1, _pos) = hdr.sc_pack();
        _pos += wrapNestHdrSt::_bitWidth;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<wrapNestSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (wrapPixelT<Config>) packed_data.range(_pos+Config::WRAP_PIXEL_WIDTH-1, _pos).to_uint64();
        _pos += Config::WRAP_PIXEL_WIDTH;
        tail = (wrapFlagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        hdr.sc_unpack(packed_data.range(_pos+wrapNestHdrSt::_bitWidth-1, _pos));
        _pos += wrapNestHdrSt::_bitWidth;
    }
    explicit wrapNestSt(sc_bv<wrapNestSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit wrapNestSt(
        wrapPixelT<Config> data_,
        wrapFlagT tail_,
        wrapNestHdrSt hdr_) :
        data(data_),
        tail(tail_),
        hdr(hdr_)
    {}
    explicit wrapNestSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpCppAxis_xpCppWrap_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpCppAxis_xpCppWrap_test_ns {
class test_xpCppWrap_structs {
public:
    static std::string name(void);
    static void test(void);
private:
    template<typename T>
    static void roundTrip(const char* sName, const std::vector<uint8_t>& patterns) {
        for(auto pattern : patterns) {
            typename T::_packedSt packed;
            memset(&packed, pattern, T::_byteWidth);
            sc_bv<T::_bitWidth> aInit;
            sc_bv<T::_bitWidth> aTest;
            for (int i = 0; i < T::_byteWidth; i++) {
                int end = std::min((i+1)*8-1, T::_bitWidth-1);
                aInit.range(end, i*8) = pattern;
            }
            T a;
            a.sc_unpack(aInit);
            T b;
            b.unpack(packed);
            if (!(b == a)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false, sName);
            }
            uint64_t test;
            memset(&test, pattern, 8);
            b.pack(packed);
            aTest = a.sc_pack();
            if (!(aTest == aInit)) {;
                cout << a.prt();
                cout << aTest;
                Q_ASSERT(false, sName);
            }
            uint64_t *ptr = (uint64_t *)&packed;
            uint16_t bitsLeft = T::_bitWidth;
            do {
                int bits = std::min((uint16_t)64, bitsLeft);
                uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
                if ((*ptr & mask) != (test & mask)) {;
                    cout << a.prt();
                    cout << b.prt();
                    Q_ASSERT(false, sName);
                }
                bitsLeft -= bits;
                ptr++;
            } while(bitsLeft > 0);
        }
    }
};
} // namespace xpCppAxis_xpCppWrap_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpCppAxis_xpCppWrap_test_ns {
using namespace xpCppAxis_xpCppWrap_ns;
struct xpCppWrapTestConfigDefault {
    static constexpr uint32_t WRAP_PIXEL_WIDTH = 8;
};
struct xpCppWrapTestConfigMid {
    static constexpr uint32_t WRAP_PIXEL_WIDTH = 16;
};
struct xpCppWrapTestConfigMax {
    static constexpr uint32_t WRAP_PIXEL_WIDTH = 32;
};
std::string test_xpCppWrap_structs::name(void) { return "test_xpCppWrap_structs"; }
void test_xpCppWrap_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<wrapEqSt<xpCppWrapTestConfigDefault>>("wrapEqSt", patterns);
    roundTrip<wrapEqSt<xpCppWrapTestConfigMid>>("wrapEqSt", patterns);
    roundTrip<wrapEqSt<xpCppWrapTestConfigMax>>("wrapEqSt", patterns);
    roundTrip<wrapOrderSt<xpCppWrapTestConfigDefault>>("wrapOrderSt", patterns);
    roundTrip<wrapOrderSt<xpCppWrapTestConfigMid>>("wrapOrderSt", patterns);
    roundTrip<wrapOrderSt<xpCppWrapTestConfigMax>>("wrapOrderSt", patterns);
    roundTrip<wrapSignSt<xpCppWrapTestConfigDefault>>("wrapSignSt", patterns);
    roundTrip<wrapSignSt<xpCppWrapTestConfigMid>>("wrapSignSt", patterns);
    roundTrip<wrapSignSt<xpCppWrapTestConfigMax>>("wrapSignSt", patterns);
    roundTrip<wrapNestHdrSt>("wrapNestHdrSt", patterns);
    roundTrip<wrapNestSt<xpCppWrapTestConfigDefault>>("wrapNestSt", patterns);
    roundTrip<wrapNestSt<xpCppWrapTestConfigMid>>("wrapNestSt", patterns);
    roundTrip<wrapNestSt<xpCppWrapTestConfigMax>>("wrapNestSt", patterns);
}
} // namespace xpCppAxis_xpCppWrap_test_ns

// GENERATED_CODE_END
