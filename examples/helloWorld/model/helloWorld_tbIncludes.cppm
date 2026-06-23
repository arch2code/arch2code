
// GENERATED_CODE_PARAM --context=helloWorld_tb.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module helloWorld_tb;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace helloWorld_tb_ns {
//constants
const uint32_t BUFFER_SIZE = 64;  // Buffer size

} // namespace helloWorld_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace helloWorld_tb_ns {
// types
typedef uint8_t byteT; // [8] Byte
typedef uint64_t qwordT; // [64] 64 bits

} // namespace helloWorld_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace helloWorld_tb_ns {
// enums

} // namespace helloWorld_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace helloWorld_tb_ns {
// structures
struct test_st {
    byteT a; //

    test_st() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const test_st & rhs) const {
        bool ret = true;
        ret = ret && (a == rhs.a);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test_st & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  test_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("a:0x{:02x}",
           (uint64_t) a
        ));
    }
    static const char* getValueType(void) { return( "tracker:cmd" );}
    inline uint64_t getStructValue(void) const { return( a );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test_st::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (byteT)((_src));
    }
    inline sc_bv<test_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<test_st::_bitWidth> packed_data;
        packed_data.range(7, 0) = a;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test_st::_bitWidth> packed_data)
    {
        a = (byteT) packed_data.range(7, 0).to_uint64();
    }
    explicit test_st(sc_bv<test_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit test_st(
        byteT a_) :
        a(a_)
    {}
    explicit test_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test_no_tracker_st {
    byteT a; //

    test_no_tracker_st() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const test_no_tracker_st & rhs) const {
        bool ret = true;
        ret = ret && (a == rhs.a);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test_no_tracker_st & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  test_no_tracker_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("a:0x{:02x}",
           (uint64_t) a
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test_no_tracker_st::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (byteT)((_src));
    }
    inline sc_bv<test_no_tracker_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<test_no_tracker_st::_bitWidth> packed_data;
        packed_data.range(7, 0) = a;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test_no_tracker_st::_bitWidth> packed_data)
    {
        a = (byteT) packed_data.range(7, 0).to_uint64();
    }
    explicit test_no_tracker_st(sc_bv<test_no_tracker_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit test_no_tracker_st(
        byteT a_) :
        a(a_)
    {}
    explicit test_no_tracker_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct data_st {
    qwordT b; //

    data_st() {}

    static constexpr uint16_t _bitWidth = 64;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const data_st & rhs) const {
        bool ret = true;
        ret = ret && (b == rhs.b);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const data_st & v, const std::string & NAME ) {
        sc_trace(tf,v.b, NAME + ".b");
    }
    inline friend ostream& operator << ( ostream& os,  data_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("b:0x{:016x}",
           (uint64_t) b
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, data_st::_byteWidth);
        _ret = b;
    }
    inline void unpack(const _packedSt &_src)
    {
        b = (qwordT)((_src));
    }
    inline sc_bv<data_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<data_st::_bitWidth> packed_data;
        packed_data.range(63, 0) = b;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<data_st::_bitWidth> packed_data)
    {
        b = (qwordT) packed_data.range(63, 0).to_uint64();
    }
    explicit data_st(sc_bv<data_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit data_st(
        qwordT b_) :
        b(b_)
    {}
    explicit data_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace helloWorld_tb_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace helloWorld_tb_ns {
template<typename Config>
class test_helloWorld_tb_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace helloWorld_tb_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace helloWorld_tb_ns {
template<typename Config>
std::string test_helloWorld_tb_structs<Config>::name(void) { return "test_helloWorld_tb_structs"; }
template<typename Config>
void test_helloWorld_tb_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        test_st::_packedSt packed;
        memset(&packed, pattern, test_st::_byteWidth);
        sc_bv<test_st::_bitWidth> aInit;
        sc_bv<test_st::_bitWidth> aTest;
        for (int i = 0; i < test_st::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test_st::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test_st a;
        a.sc_unpack(aInit);
        test_st b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test_st fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test_st fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test_st::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test_st fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test_no_tracker_st::_packedSt packed;
        memset(&packed, pattern, test_no_tracker_st::_byteWidth);
        sc_bv<test_no_tracker_st::_bitWidth> aInit;
        sc_bv<test_no_tracker_st::_bitWidth> aTest;
        for (int i = 0; i < test_no_tracker_st::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test_no_tracker_st::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test_no_tracker_st a;
        a.sc_unpack(aInit);
        test_no_tracker_st b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test_no_tracker_st fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test_no_tracker_st fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test_no_tracker_st::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test_no_tracker_st fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        data_st::_packedSt packed;
        memset(&packed, pattern, data_st::_byteWidth);
        sc_bv<data_st::_bitWidth> aInit;
        sc_bv<data_st::_bitWidth> aTest;
        for (int i = 0; i < data_st::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, data_st::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        data_st a;
        a.sc_unpack(aInit);
        data_st b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"data_st fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"data_st fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = data_st::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"data_st fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace helloWorld_tb_ns

// GENERATED_CODE_END
