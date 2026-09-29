
// GENERATED_CODE_PARAM --project=hierVlDemo --context=../../yaml/hierVlSharedTypes.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module hierVlDemo_hierVlSharedTypes;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace hierVlDemo_hierVlSharedTypes_ns {
//constants

} // namespace hierVlDemo_hierVlSharedTypes_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace hierVlDemo_hierVlSharedTypes_ns {
// types
typedef uint8_t shared_bv8_t; // [8] Shared 8-bit vector
typedef uint32_t shared_bv32_t; // [32] Shared 32-bit vector

} // namespace hierVlDemo_hierVlSharedTypes_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace hierVlDemo_hierVlSharedTypes_ns {
// enums

} // namespace hierVlDemo_hierVlSharedTypes_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace hierVlDemo_hierVlSharedTypes_ns {
// structures
struct sharedInfoSt {
    shared_bv32_t value; //
    shared_bv8_t tag; //

    sharedInfoSt() {}

    static constexpr uint16_t _bitWidth = 32 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const sharedInfoSt & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (value == rhs.value);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const sharedInfoSt & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.value, NAME + ".value");
    }
    inline friend ostream& operator << ( ostream& os,  sharedInfoSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:02x} value:0x{:08x}",
           (uint64_t) tag,
           (uint64_t) value
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sharedInfoSt::_byteWidth);
        _ret = value;
        _ret |= (uint64_t)tag << (32 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        value = (shared_bv32_t)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += 32;
        tag = (shared_bv8_t)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
    }
    inline sc_bv<sharedInfoSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<sharedInfoSt::_bitWidth> packed_data;
        packed_data.range(31, 0) = value;
        packed_data.range(39, 32) = tag;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<sharedInfoSt::_bitWidth> packed_data)
    {
        value = (shared_bv32_t) packed_data.range(31, 0).to_uint64();
        tag = (shared_bv8_t) packed_data.range(39, 32).to_uint64();
    }
    explicit sharedInfoSt(sc_bv<sharedInfoSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit sharedInfoSt(
        shared_bv32_t value_,
        shared_bv8_t tag_) :
        value(value_),
        tag(tag_)
    {}
    explicit sharedInfoSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace hierVlDemo_hierVlSharedTypes_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace hierVlDemo_hierVlSharedTypes_test_ns {
class test_hierVlSharedTypes_structs {
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
} // namespace hierVlDemo_hierVlSharedTypes_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace hierVlDemo_hierVlSharedTypes_test_ns {
using namespace hierVlDemo_hierVlSharedTypes_ns;
std::string test_hierVlSharedTypes_structs::name(void) { return "test_hierVlSharedTypes_structs"; }
void test_hierVlSharedTypes_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<sharedInfoSt>("sharedInfoSt", patterns);
}
} // namespace hierVlDemo_hierVlSharedTypes_test_ns

// GENERATED_CODE_END
