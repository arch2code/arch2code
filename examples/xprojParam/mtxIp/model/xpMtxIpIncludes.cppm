
// GENERATED_CODE_PARAM --project=xpMtxIp --context=../../yaml/xpMtxIp.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module xpMtxIp;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xpMtxIp_ns {
//constants

} // namespace xpMtxIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xpMtxIp_ns {
// types
template<typename Config> using miSrcPixelT = uint64_t; // [max:32] Producer parameterizable pixel word
template<typename Config> using miDstPixelT = uint64_t; // [max:64] Consumer parameterizable pixel word
typedef uint8_t miTagT; // [8] Sample sequence tag; low packed position
typedef uint8_t miMarkT; // [8] Trailing marker; sits above the pixel so a wrong-width pixel shifts it
typedef uint16_t miLitPixelT; // [12] Literal pixel word at the same resolved width as the parameterized ones

} // namespace xpMtxIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xpMtxIp_ns {
// enums

} // namespace xpMtxIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xpMtxIp_ns {
// structures
struct miSrcLitSt {
    miMarkT mark; //Trailing marker
    miLitPixelT data; //Literal pixel payload
    miTagT tag; //Sample sequence tag

    miSrcLitSt() {}

    static constexpr uint16_t _bitWidth = 8 + 12 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const miSrcLitSt & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const miSrcLitSt & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  miSrcLitSt const & v ) {
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
        memset(&_ret, 0, miSrcLitSt::_byteWidth);
        _ret = mark;
        _ret |= (uint32_t)data << (8 & 31);
        _ret |= (uint32_t)tag << (20 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (miMarkT)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
        _pos += 8;
        data = (miLitPixelT)((_src >> (_pos & 31)) & ((1ULL << 12) - 1));
        _pos += 12;
        tag = (miTagT)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
    }
    inline sc_bv<miSrcLitSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<miSrcLitSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = mark;
        packed_data.range(19, 8) = data;
        packed_data.range(27, 20) = tag;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<miSrcLitSt::_bitWidth> packed_data)
    {
        mark = (miMarkT) packed_data.range(7, 0).to_uint64();
        data = (miLitPixelT) packed_data.range(19, 8).to_uint64();
        tag = (miTagT) packed_data.range(27, 20).to_uint64();
    }
    explicit miSrcLitSt(sc_bv<miSrcLitSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit miSrcLitSt(
        miMarkT mark_,
        miLitPixelT data_,
        miTagT tag_) :
        mark(mark_),
        data(data_),
        tag(tag_)
    {}
    explicit miSrcLitSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct miSrcParSt {
    miMarkT mark; //Trailing marker
    miSrcPixelT<Config> data; //Parameterizable pixel payload
    miTagT tag; //Sample sequence tag

    miSrcParSt() {}

    static constexpr uint16_t _bitWidth = 8 + Config::MI_SRC_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const miSrcParSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const miSrcParSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  miSrcParSt const & v ) {
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
        memset(&_ret, 0, miSrcParSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, mark, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, data, Config::MI_SRC_WIDTH);
        _pos += Config::MI_SRC_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (miMarkT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        data = (miSrcPixelT<Config>)((_src >> (_pos & 63)) & ((1ULL << (Config::MI_SRC_WIDTH)) - 1));
        _pos += Config::MI_SRC_WIDTH;
        tag = (miTagT)((_src >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<miSrcParSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<miSrcParSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+8-1, _pos) = mark;
        _pos += 8;
        packed_data.range(_pos+Config::MI_SRC_WIDTH-1, _pos) = data;
        _pos += Config::MI_SRC_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<miSrcParSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        mark = (miMarkT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        data = (miSrcPixelT<Config>) packed_data.range(_pos+Config::MI_SRC_WIDTH-1, _pos).to_uint64();
        _pos += Config::MI_SRC_WIDTH;
        tag = (miTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit miSrcParSt(sc_bv<miSrcParSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit miSrcParSt(
        miMarkT mark_,
        miSrcPixelT<Config> data_,
        miTagT tag_) :
        mark(mark_),
        data(data_),
        tag(tag_)
    {}
    explicit miSrcParSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct miDstLitSt {
    miMarkT mark; //Trailing marker
    miLitPixelT data; //Literal pixel payload
    miTagT tag; //Sample sequence tag

    miDstLitSt() {}

    static constexpr uint16_t _bitWidth = 8 + 12 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const miDstLitSt & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const miDstLitSt & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  miDstLitSt const & v ) {
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
        memset(&_ret, 0, miDstLitSt::_byteWidth);
        _ret = mark;
        _ret |= (uint32_t)data << (8 & 31);
        _ret |= (uint32_t)tag << (20 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (miMarkT)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
        _pos += 8;
        data = (miLitPixelT)((_src >> (_pos & 31)) & ((1ULL << 12) - 1));
        _pos += 12;
        tag = (miTagT)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
    }
    inline sc_bv<miDstLitSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<miDstLitSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = mark;
        packed_data.range(19, 8) = data;
        packed_data.range(27, 20) = tag;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<miDstLitSt::_bitWidth> packed_data)
    {
        mark = (miMarkT) packed_data.range(7, 0).to_uint64();
        data = (miLitPixelT) packed_data.range(19, 8).to_uint64();
        tag = (miTagT) packed_data.range(27, 20).to_uint64();
    }
    explicit miDstLitSt(sc_bv<miDstLitSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit miDstLitSt(
        miMarkT mark_,
        miLitPixelT data_,
        miTagT tag_) :
        mark(mark_),
        data(data_),
        tag(tag_)
    {}
    explicit miDstLitSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct miDstParSt {
    miMarkT mark; //Trailing marker
    miDstPixelT<Config> data; //Parameterizable pixel payload
    miTagT tag; //Sample sequence tag

    miDstParSt() {}

    static constexpr uint16_t _bitWidth = 8 + Config::MI_DST_WIDTH + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const miDstParSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (data == rhs.data);
        ret = ret && (mark == rhs.mark);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const miDstParSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.data, NAME + ".data");
        sc_trace(tf,v.mark, NAME + ".mark");
    }
    inline friend ostream& operator << ( ostream& os,  miDstParSt const & v ) {
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
        memset(&_ret, 0, miDstParSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, mark, 8);
        _pos += 8;
        pack_bits((uint64_t *)&_ret, _pos, data, Config::MI_DST_WIDTH);
        _pos += Config::MI_DST_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, tag, 8);
        _pos += 8;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        mark = (miMarkT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (8)) - 1));
        _pos += 8;
        data = (miDstPixelT<Config>)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (Config::MI_DST_WIDTH)) - 1));
        _pos += Config::MI_DST_WIDTH;
        tag = (miTagT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << (8)) - 1));
    }
    inline sc_bv<miDstParSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<miDstParSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+8-1, _pos) = mark;
        _pos += 8;
        packed_data.range(_pos+Config::MI_DST_WIDTH-1, _pos) = data;
        _pos += Config::MI_DST_WIDTH;
        packed_data.range(_pos+8-1, _pos) = tag;
        _pos += 8;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<miDstParSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        mark = (miMarkT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
        data = (miDstPixelT<Config>) packed_data.range(_pos+Config::MI_DST_WIDTH-1, _pos).to_uint64();
        _pos += Config::MI_DST_WIDTH;
        tag = (miTagT) packed_data.range(_pos+8-1, _pos).to_uint64();
        _pos += 8;
    }
    explicit miDstParSt(sc_bv<miDstParSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit miDstParSt(
        miMarkT mark_,
        miDstPixelT<Config> data_,
        miTagT tag_) :
        mark(mark_),
        data(data_),
        tag(tag_)
    {}
    explicit miDstParSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xpMtxIp_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xpMtxIp_test_ns {
class test_xpMtxIp_structs {
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
} // namespace xpMtxIp_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xpMtxIp_test_ns {
using namespace xpMtxIp_ns;
struct xpMtxIpTestConfigDefault {
    static constexpr uint32_t MI_SRC_WIDTH = 12;
    static constexpr uint32_t MI_DST_WIDTH = 12;
};
struct xpMtxIpTestConfigMid {
    static constexpr uint32_t MI_SRC_WIDTH = 16;
    static constexpr uint32_t MI_DST_WIDTH = 32;
};
struct xpMtxIpTestConfigMax {
    static constexpr uint32_t MI_SRC_WIDTH = 32;
    static constexpr uint32_t MI_DST_WIDTH = 64;
};
std::string test_xpMtxIp_structs::name(void) { return "test_xpMtxIp_structs"; }
void test_xpMtxIp_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<miSrcLitSt>("miSrcLitSt", patterns);
    roundTrip<miSrcParSt<xpMtxIpTestConfigDefault>>("miSrcParSt", patterns);
    roundTrip<miSrcParSt<xpMtxIpTestConfigMid>>("miSrcParSt", patterns);
    roundTrip<miSrcParSt<xpMtxIpTestConfigMax>>("miSrcParSt", patterns);
    roundTrip<miDstLitSt>("miDstLitSt", patterns);
    roundTrip<miDstParSt<xpMtxIpTestConfigDefault>>("miDstParSt", patterns);
    roundTrip<miDstParSt<xpMtxIpTestConfigMid>>("miDstParSt", patterns);
    roundTrip<miDstParSt<xpMtxIpTestConfigMax>>("miDstParSt", patterns);
}
} // namespace xpMtxIp_test_ns

// GENERATED_CODE_END
