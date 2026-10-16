
// GENERATED_CODE_PARAM --project=vlTiming --context=../../yaml/vlt.yaml --mode=module
//

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module vlTiming_vlt;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace vlTiming_vlt_ns {
//constants
inline constexpr uint32_t VLT_START_DELAY_PS = 2000;  // Source start-up delay in picoseconds, ending before the first clock edge

} // namespace vlTiming_vlt_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace vlTiming_vlt_ns {
// types
typedef uint32_t vltStampT; // [32] Simulation time in picoseconds

} // namespace vlTiming_vlt_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace vlTiming_vlt_ns {
// enums

} // namespace vlTiming_vlt_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace vlTiming_vlt_ns {
// structures
struct vltSt {
    vltStampT stamp; //Time the source's start-up delay ended

    vltSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const vltSt & rhs) const {
        bool ret = true;
        ret = ret && (stamp == rhs.stamp);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const vltSt & v, const std::string & NAME ) {
        sc_trace(tf,v.stamp, NAME + ".stamp");
    }
    inline friend ostream& operator << ( ostream& os,  vltSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("stamp:0x{:08x}",
           (uint64_t) stamp
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = stamp;
    }
    inline void unpack(const _packedSt &_src)
    {
        stamp = (vltStampT)((_src));
    }
    inline sc_bv<vltSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<vltSt::_bitWidth> packed_data;
        packed_data.range(31, 0) = stamp;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<vltSt::_bitWidth> packed_data)
    {
        stamp = (vltStampT) packed_data.range(31, 0).to_uint64();
    }
    explicit vltSt(sc_bv<vltSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit vltSt(
        vltStampT stamp_) :
        stamp(stamp_)
    {}
    explicit vltSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace vlTiming_vlt_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace vlTiming_vlt_test_ns {
class test_vlt_structs {
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
} // namespace vlTiming_vlt_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace vlTiming_vlt_test_ns {
using namespace vlTiming_vlt_ns;
std::string test_vlt_structs::name(void) { return "test_vlt_structs"; }
void test_vlt_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<vltSt>("vltSt", patterns);
}
} // namespace vlTiming_vlt_test_ns

// GENERATED_CODE_END
