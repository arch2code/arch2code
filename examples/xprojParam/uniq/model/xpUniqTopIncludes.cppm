
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
        memset(&_ret, 0, boundarySt::_byteWidth);
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
        packed_data.range(7, 0) = data;
        packed_data.range(11, 8) = tag;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<boundarySt::_bitWidth> packed_data)
    {
        data = (boundaryPixelT) packed_data.range(7, 0).to_uint64();
        tag = (boundaryTagT) packed_data.range(11, 8).to_uint64();
    }
    explicit boundarySt(sc_bv<boundarySt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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
export namespace xpUniq_xpUniqTop_test_ns {
class test_xpUniqTop_structs {
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
