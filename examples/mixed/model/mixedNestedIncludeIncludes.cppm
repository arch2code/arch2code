
// GENERATED_CODE_PARAM --context=mixedNestedInclude.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module mixedNestedInclude;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace mixedNestedInclude_ns {
//constants
const uint32_t DSIZE = 1;  // The size of D
const uint32_t DSIZE2 = 2;  // The size of D2

} // namespace mixedNestedInclude_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace mixedNestedInclude_ns {
// types
typedef uint16_t dupTestT; // [13] yet another type

} // namespace mixedNestedInclude_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace mixedNestedInclude_ns {
// enums

} // namespace mixedNestedInclude_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace mixedNestedInclude_ns {
// structures
struct dupTestSt {
    dupTestT bob; //A test structure

    dupTestSt() {}

    static constexpr uint16_t _bitWidth = 13;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const dupTestSt & rhs) const {
        bool ret = true;
        ret = ret && (bob == rhs.bob);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const dupTestSt & v, const std::string & NAME ) {
        sc_trace(tf,v.bob, NAME + ".bob");
    }
    inline friend ostream& operator << ( ostream& os,  dupTestSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("bob:0x{:04x}",
           (uint64_t) bob
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, dupTestSt::_byteWidth);
        _ret = bob;
    }
    inline void unpack(const _packedSt &_src)
    {
        bob = (dupTestT)((_src) & ((1ULL << 13) - 1));
    }
    inline sc_bv<dupTestSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<dupTestSt::_bitWidth> packed_data;
        packed_data.range(12, 0) = bob;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<dupTestSt::_bitWidth> packed_data)
    {
        bob = (dupTestT) packed_data.range(12, 0).to_uint64();
    }
    explicit dupTestSt(sc_bv<dupTestSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit dupTestSt(
        dupTestT bob_) :
        bob(bob_)
    {}
    explicit dupTestSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace mixedNestedInclude_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace mixedNestedInclude_ns {
template<typename Config>
class test_mixedNestedInclude_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace mixedNestedInclude_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace mixedNestedInclude_ns {
template<typename Config>
std::string test_mixedNestedInclude_structs<Config>::name(void) { return "test_mixedNestedInclude_structs"; }
template<typename Config>
void test_mixedNestedInclude_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        dupTestSt::_packedSt packed;
        memset(&packed, pattern, dupTestSt::_byteWidth);
        sc_bv<dupTestSt::_bitWidth> aInit;
        sc_bv<dupTestSt::_bitWidth> aTest;
        for (int i = 0; i < dupTestSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, dupTestSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        dupTestSt a;
        a.sc_unpack(aInit);
        dupTestSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"dupTestSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"dupTestSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = dupTestSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"dupTestSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace mixedNestedInclude_ns

// GENERATED_CODE_END
