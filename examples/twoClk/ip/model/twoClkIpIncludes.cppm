
// GENERATED_CODE_PARAM --project=twoClkIp --context=../../yaml/twoClkIp.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module twoClkIp;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace twoClkIp_ns {
//constants
inline constexpr uint32_t TWO_CLK_BURST_WORDS = 4;  // Words in the twoClkIpSrc -> sink burst
inline constexpr uint32_t TWO_CLK_BURST_BASE = 161;  // Payload of the first word of the burst; word i is BASE + i

} // namespace twoClkIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace twoClkIp_ns {
// types
typedef uint8_t twoClkDataT; // [8] 8-bit payload word

} // namespace twoClkIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace twoClkIp_ns {
// enums

} // namespace twoClkIp_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace twoClkIp_ns {
// structures
struct twoClkDataSt {
    twoClkDataT data; //payload word

    twoClkDataSt() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const twoClkDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const twoClkDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  twoClkDataSt const & v ) {
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
        memset(&_ret, 0, twoClkDataSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (twoClkDataT)((_src));
    }
    inline sc_bv<twoClkDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkDataSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = data;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<twoClkDataSt::_bitWidth> packed_data)
    {
        data = (twoClkDataT) packed_data.range(7, 0).to_uint64();
    }
    explicit twoClkDataSt(sc_bv<twoClkDataSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit twoClkDataSt(
        twoClkDataT data_) :
        data(data_)
    {}
    explicit twoClkDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace twoClkIp_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace twoClkIp_test_ns {
class test_twoClkIp_structs {
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
} // namespace twoClkIp_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace twoClkIp_test_ns {
using namespace twoClkIp_ns;
std::string test_twoClkIp_structs::name(void) { return "test_twoClkIp_structs"; }
void test_twoClkIp_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<twoClkDataSt>("twoClkDataSt", patterns);
}
} // namespace twoClkIp_test_ns

// GENERATED_CODE_END
