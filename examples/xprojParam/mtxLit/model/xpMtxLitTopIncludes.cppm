
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
        memset(&_ret, 0, mlChSt::_byteWidth);
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
        packed_data.range(7, 0) = mark;
        packed_data.range(19, 8) = data;
        packed_data.range(27, 20) = tag;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<mlChSt::_bitWidth> packed_data)
    {
        mark = (mlChMarkT) packed_data.range(7, 0).to_uint64();
        data = (mlChPixelT) packed_data.range(19, 8).to_uint64();
        tag = (mlChTagT) packed_data.range(27, 20).to_uint64();
    }
    explicit mlChSt(sc_bv<mlChSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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
export namespace xpMtxLit_xpMtxLitTop_test_ns {
class test_xpMtxLitTop_structs {
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
