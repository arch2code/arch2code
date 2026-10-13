
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
template<uint32_t WRAP_PIXEL_WIDTH> using wrapPixelT_v = uint64_t; // [max:32] Parameterizable pixel word
template<typename Config> using wrapPixelT = wrapPixelT_v<Config::WRAP_PIXEL_WIDTH>;
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
template<uint32_t WRAP_PIXEL_WIDTH>
struct wrapEqSt_v {
    wrapPixelT_v<WRAP_PIXEL_WIDTH> data; //Pixel payload
    wrapTagT tag; //Sample sequence tag

    wrapEqSt_v() {}

    static constexpr uint16_t _bitWidth = WRAP_PIXEL_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const wrapEqSt_v<WRAP_PIXEL_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapEqSt_v<WRAP_PIXEL_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  wrapEqSt_v const & v ) {
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
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, WRAP_PIXEL_WIDTH);
        _pos += WRAP_PIXEL_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (wrapPixelT_v<WRAP_PIXEL_WIDTH>)((_src >> (_pos & 63)) & (~0ULL >> (64 - (WRAP_PIXEL_WIDTH))));
        _pos += WRAP_PIXEL_WIDTH;
        tag = (wrapTagT)((_src >> (_pos & 63)) & (~0ULL >> (64 - (8))));
    }
    inline sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "wrapEqSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit wrapEqSt_v(const sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit wrapEqSt_v(
        wrapPixelT_v<WRAP_PIXEL_WIDTH> data_,
        wrapTagT tag_) :
        data(data_),
        tag(tag_)
    {}
    explicit wrapEqSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using wrapEqSt = wrapEqSt_v<Config::WRAP_PIXEL_WIDTH>;
template<uint32_t WRAP_PIXEL_WIDTH>
struct wrapOrderSt_v {
    wrapFlagT second; //Literal member at the high packed position
    wrapPixelT_v<WRAP_PIXEL_WIDTH> first; //Parameterizable member at the low packed position

    wrapOrderSt_v() {}

    static constexpr uint16_t _bitWidth = 8 + WRAP_PIXEL_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const wrapOrderSt_v<WRAP_PIXEL_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (first == rhs.first);
        ret = ret && (second == rhs.second);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapOrderSt_v<WRAP_PIXEL_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.first, NAME + ".first");
        sc_trace(tf,v.second, NAME + ".second");
    }
    inline friend ostream& operator << ( ostream& os,  wrapOrderSt_v const & v ) {
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
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, second, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, first, WRAP_PIXEL_WIDTH);
        _pos += WRAP_PIXEL_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        second = (wrapFlagT)((_src >> (_pos & 63)) & (~0ULL >> (64 - (8))));
        _pos += 8;
        first = (wrapPixelT_v<WRAP_PIXEL_WIDTH>)((_src >> (_pos & 63)) & (~0ULL >> (64 - (WRAP_PIXEL_WIDTH))));
    }
    inline sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "wrapOrderSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit wrapOrderSt_v(const sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit wrapOrderSt_v(
        wrapFlagT second_,
        wrapPixelT_v<WRAP_PIXEL_WIDTH> first_) :
        second(second_),
        first(first_)
    {}
    explicit wrapOrderSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using wrapOrderSt = wrapOrderSt_v<Config::WRAP_PIXEL_WIDTH>;
template<uint32_t WRAP_PIXEL_WIDTH>
struct wrapSignSt_v {
    wrapPixelT_v<WRAP_PIXEL_WIDTH> data; //Pixel payload

    wrapSignSt_v() {}

    static constexpr uint16_t _bitWidth = WRAP_PIXEL_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const wrapSignSt_v<WRAP_PIXEL_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapSignSt_v<WRAP_PIXEL_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  wrapSignSt_v const & v ) {
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
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, WRAP_PIXEL_WIDTH);
        _pos += WRAP_PIXEL_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (wrapPixelT_v<WRAP_PIXEL_WIDTH>)((_src) & (~0ULL >> (64 - (WRAP_PIXEL_WIDTH))));
    }
    inline sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "wrapSignSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit wrapSignSt_v(const sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit wrapSignSt_v(
        wrapPixelT_v<WRAP_PIXEL_WIDTH> data_) :
        data(data_)
    {}
    explicit wrapSignSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using wrapSignSt = wrapSignSt_v<Config::WRAP_PIXEL_WIDTH>;
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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "wrapNestHdrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<wrapNestHdrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit wrapNestHdrSt(const sc_bv<wrapNestHdrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit wrapNestHdrSt(
        wrapFlagT flag_,
        wrapWordT word_) :
        flag(flag_),
        word(word_)
    {}
    explicit wrapNestHdrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<uint32_t WRAP_PIXEL_WIDTH>
struct wrapNestSt_v {
    wrapPixelT_v<WRAP_PIXEL_WIDTH> data; //Pixel payload
    wrapFlagT tail; //Trailing flag
    wrapNestHdrSt hdr; //Nested header

    wrapNestSt_v() {}

    static constexpr uint16_t _bitWidth = WRAP_PIXEL_WIDTH + 8 + wrapNestHdrSt::_bitWidth;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const wrapNestSt_v<WRAP_PIXEL_WIDTH> & rhs) const {
        bool ret = true;
        ret = ret && (hdr == rhs.hdr);
        ret = ret && (tail == rhs.tail);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wrapNestSt_v<WRAP_PIXEL_WIDTH> & v, const std::string & NAME ) {
        sc_trace(tf,v.hdr, NAME + ".hdr");
        sc_trace(tf,v.tail, NAME + ".tail");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  wrapNestSt_v const & v ) {
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
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, WRAP_PIXEL_WIDTH);
        _pos += WRAP_PIXEL_WIDTH;
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
        data = (wrapPixelT_v<WRAP_PIXEL_WIDTH>)((_src[ _pos >> 6 ] >> (_pos & 63)) & (~0ULL >> (64 - (WRAP_PIXEL_WIDTH))));
        _pos += WRAP_PIXEL_WIDTH;
        tail = (wrapFlagT)((_src[ _pos >> 6 ] >> (_pos & 63)) & (~0ULL >> (64 - (8))));
        if ((_pos & 63) + 8 > 64) {
            tail = (wrapFlagT)(tail | ((_src[ (_pos >> 6) + 1 ] << (64 - (_pos & 63))) & (~0ULL >> (64 - (8)))));
        }
        _pos += 8;
        {
            wrapNestHdrSt::_packedSt _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, wrapNestHdrSt::_bitWidth);
            hdr.unpack(_tmp);
        }
    }
    inline sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> sc_pack(void) const
    {
        sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)(_packed[i >> 1] >> ((i & 1) * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "wrapNestSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data)
    {
        _packedSt _words{};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _words[i >> 1] |= (uint64_t)packed_data.get_word(i) << ((i & 1) * 32);
        }
        unpack(_words);
    }
    explicit wrapNestSt_v(const sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit wrapNestSt_v(
        wrapPixelT_v<WRAP_PIXEL_WIDTH> data_,
        wrapFlagT tail_,
        wrapNestHdrSt hdr_) :
        data(data_),
        tail(tail_),
        hdr(hdr_)
    {}
    explicit wrapNestSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using wrapNestSt = wrapNestSt_v<Config::WRAP_PIXEL_WIDTH>;
} // namespace xpCppAxis_xpCppWrap_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpCppAxis_xpCppWrap_ns {
template<uint32_t WRAP_PIXEL_WIDTH> inline sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> testRefPack(const wrapEqSt_v<WRAP_PIXEL_WIDTH> &x);
template<uint32_t WRAP_PIXEL_WIDTH> inline void testRefUnpack(wrapEqSt_v<WRAP_PIXEL_WIDTH> &x, const sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data);
template<uint32_t WRAP_PIXEL_WIDTH> inline sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> testRefPack(const wrapOrderSt_v<WRAP_PIXEL_WIDTH> &x);
template<uint32_t WRAP_PIXEL_WIDTH> inline void testRefUnpack(wrapOrderSt_v<WRAP_PIXEL_WIDTH> &x, const sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data);
template<uint32_t WRAP_PIXEL_WIDTH> inline sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> testRefPack(const wrapSignSt_v<WRAP_PIXEL_WIDTH> &x);
template<uint32_t WRAP_PIXEL_WIDTH> inline void testRefUnpack(wrapSignSt_v<WRAP_PIXEL_WIDTH> &x, const sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data);
inline sc_bv<wrapNestHdrSt::_bitWidth> testRefPack(const wrapNestHdrSt &x);
inline void testRefUnpack(wrapNestHdrSt &x, const sc_bv<wrapNestHdrSt::_bitWidth> &packed_data);
template<uint32_t WRAP_PIXEL_WIDTH> inline sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> testRefPack(const wrapNestSt_v<WRAP_PIXEL_WIDTH> &x);
template<uint32_t WRAP_PIXEL_WIDTH> inline void testRefUnpack(wrapNestSt_v<WRAP_PIXEL_WIDTH> &x, const sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data);
template<uint32_t WRAP_PIXEL_WIDTH> inline sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> testRefPack(const wrapEqSt_v<WRAP_PIXEL_WIDTH> &x)
{
    sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+WRAP_PIXEL_WIDTH-1, _pos) = x.data;
    _pos += WRAP_PIXEL_WIDTH;
    packed_data.range(_pos+8-1, _pos) = x.tag;
    _pos += 8;
    return packed_data;
}
template<uint32_t WRAP_PIXEL_WIDTH> inline void testRefUnpack(wrapEqSt_v<WRAP_PIXEL_WIDTH> &x, const sc_bv<wrapEqSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.data = (wrapPixelT_v<WRAP_PIXEL_WIDTH>) packed_data.range(_pos+WRAP_PIXEL_WIDTH-1, _pos).to_uint64();
    _pos += WRAP_PIXEL_WIDTH;
    x.tag = (wrapTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
    _pos += 8;
}
template<uint32_t WRAP_PIXEL_WIDTH> inline sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> testRefPack(const wrapOrderSt_v<WRAP_PIXEL_WIDTH> &x)
{
    sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+8-1, _pos) = x.second;
    _pos += 8;
    packed_data.range(_pos+WRAP_PIXEL_WIDTH-1, _pos) = x.first;
    _pos += WRAP_PIXEL_WIDTH;
    return packed_data;
}
template<uint32_t WRAP_PIXEL_WIDTH> inline void testRefUnpack(wrapOrderSt_v<WRAP_PIXEL_WIDTH> &x, const sc_bv<wrapOrderSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.second = (wrapFlagT) packed_data.range(_pos+8-1, _pos).to_uint64();
    _pos += 8;
    x.first = (wrapPixelT_v<WRAP_PIXEL_WIDTH>) packed_data.range(_pos+WRAP_PIXEL_WIDTH-1, _pos).to_uint64();
    _pos += WRAP_PIXEL_WIDTH;
}
template<uint32_t WRAP_PIXEL_WIDTH> inline sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> testRefPack(const wrapSignSt_v<WRAP_PIXEL_WIDTH> &x)
{
    sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+WRAP_PIXEL_WIDTH-1, _pos) = x.data;
    _pos += WRAP_PIXEL_WIDTH;
    return packed_data;
}
template<uint32_t WRAP_PIXEL_WIDTH> inline void testRefUnpack(wrapSignSt_v<WRAP_PIXEL_WIDTH> &x, const sc_bv<wrapSignSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.data = (wrapPixelT_v<WRAP_PIXEL_WIDTH>) packed_data.range(_pos+WRAP_PIXEL_WIDTH-1, _pos).to_uint64();
    _pos += WRAP_PIXEL_WIDTH;
}
inline sc_bv<wrapNestHdrSt::_bitWidth> testRefPack(const wrapNestHdrSt &x)
{
    sc_bv<wrapNestHdrSt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.flag;
    packed_data.range(8+32-1, 8) = x.word;
    return packed_data;
}
inline void testRefUnpack(wrapNestHdrSt &x, const sc_bv<wrapNestHdrSt::_bitWidth> &packed_data)
{
    x.flag = (wrapFlagT) packed_data.range(0+8-1, 0).to_uint64();
    x.word = (wrapWordT) packed_data.range(8+32-1, 8).to_uint64();
}
template<uint32_t WRAP_PIXEL_WIDTH> inline sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> testRefPack(const wrapNestSt_v<WRAP_PIXEL_WIDTH> &x)
{
    sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+WRAP_PIXEL_WIDTH-1, _pos) = x.data;
    _pos += WRAP_PIXEL_WIDTH;
    packed_data.range(_pos+8-1, _pos) = x.tail;
    _pos += 8;
    packed_data.range(_pos+wrapNestHdrSt::_bitWidth-1, _pos) = testRefPack(x.hdr);
    _pos += wrapNestHdrSt::_bitWidth;
    return packed_data;
}
template<uint32_t WRAP_PIXEL_WIDTH> inline void testRefUnpack(wrapNestSt_v<WRAP_PIXEL_WIDTH> &x, const sc_bv<wrapNestSt_v<WRAP_PIXEL_WIDTH>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.data = (wrapPixelT_v<WRAP_PIXEL_WIDTH>) packed_data.range(_pos+WRAP_PIXEL_WIDTH-1, _pos).to_uint64();
    _pos += WRAP_PIXEL_WIDTH;
    x.tail = (wrapFlagT) packed_data.range(_pos+8-1, _pos).to_uint64();
    _pos += 8;
    testRefUnpack(x.hdr, packed_data.range(_pos+wrapNestHdrSt::_bitWidth-1, _pos));
    _pos += wrapNestHdrSt::_bitWidth;
}
} // namespace xpCppAxis_xpCppWrap_ns
export namespace xpCppAxis_xpCppWrap_test_ns {
class test_xpCppWrap_structs {
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
