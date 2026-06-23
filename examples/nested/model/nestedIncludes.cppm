
// GENERATED_CODE_PARAM --context=nested.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module nested;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace nested_ns {
//constants
const uint32_t NUM_COMMANDS = 1024;  // Number of Commands
const uint32_t NUM_COMMANDS_LOG2 = 10;  // Number of Commands log2
const uint32_t BIG_WIDTH = 96;  // big width test case
const uint32_t NUM_FIRST_TAGS = 64;  // Num first Tags
const uint32_t NUM_FIRST_TAGS_LOG2 = 6;  // Num first Tags Log2
const uint32_t NUM_SECOND_TAGS = 1024;  // Num second Tags
const uint32_t NUM_SECOND_TAGS_LOG2 = 10;  // Num second Tags Log2
const uint32_t NUM_THIRD_TAGS = 1024;  // Num third Tags
const uint32_t NUM_THIRD_TAGS_LOG2 = 10;  // Num third Tags Log2
const uint32_t NUM_TAGS = 2112;  // Num Tags
const uint32_t NUM_TAGS_LOG2 = 12;  // Num Tags Log2
const uint32_t TAGBASE_SECONDTAG = 0;  // base value for Tag type 2
const uint32_t TAGBASE_THIRDTAG = 1024;  // base value for Tag type 3
const uint32_t TAGBASE_FIRSTTAG = 2048;  // base value for Tag type 1

} // namespace nested_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace nested_ns {
// types
typedef uint16_t tagT; // [12] Read Tag
typedef uint16_t cmdidT; // [10] Command ID
struct bigT { uint64_t word[ 2 ]; }; // [96] big width test case
struct dataT { uint64_t word[ 2 ]; }; // [128] Data
typedef uint16_t lengthT; // [16] Length of transfer

} // namespace nested_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace nested_ns {
// enums
enum  tagTypeT {             //type of tag for encode
    TAGTYPE_SECONDTAG=0,     // Tag type 2
    TAGTYPE_THIRDTAG=1,      // Tag type 3
    TAGTYPE_FIRSTTAG=2 };    // Tag type 1
inline const char* tagTypeT_prt( tagTypeT val )
{
    switch( val )
    {
        case TAGTYPE_SECONDTAG: return( "TAGTYPE_SECONDTAG" );
        case TAGTYPE_THIRDTAG: return( "TAGTYPE_THIRDTAG" );
        case TAGTYPE_FIRSTTAG: return( "TAGTYPE_FIRSTTAG" );
    }
    return("!!!BADENUM!!!");
}
enum  locT {                 //type of location for encode
    LOC_FIRSTTAG=0,          // Tag type 1
    LOC_FLASH=1 };           // Flash location
inline const char* locT_prt( locT val )
{
    switch( val )
    {
        case LOC_FIRSTTAG: return( "LOC_FIRSTTAG" );
        case LOC_FLASH: return( "LOC_FLASH" );
    }
    return("!!!BADENUM!!!");
}
enum  enumType {             //Example of an enum
    ENUM_TYPE_1=1,           // this type of enum
    ENUM_TYPE_2=NUM_COMMANDS }; // other type of enum
inline const char* enumType_prt( enumType val )
{
    switch( val )
    {
        case ENUM_TYPE_1: return( "ENUM_TYPE_1" );
        case ENUM_TYPE_2: return( "ENUM_TYPE_2" );
    }
    return("!!!BADENUM!!!");
}

} // namespace nested_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace nested_ns {
// structures
struct test_st {
    cmdidT a; //

    test_st() {}

    static constexpr uint16_t _bitWidth = NUM_COMMANDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
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
        return (std::format("a:0x{:03x}",
           (uint64_t) a
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test_st::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    inline sc_bv<test_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<test_st::_bitWidth> packed_data;
        packed_data.range(9, 0) = a;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test_st::_bitWidth> packed_data)
    {
        a = (cmdidT) packed_data.range(9, 0).to_uint64();
    }
    explicit test_st(sc_bv<test_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit test_st(
        cmdidT a_) :
        a(a_)
    {}
    explicit test_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bigSt {
    bigT b; //

    bigSt() {}

    static constexpr uint16_t _bitWidth = BIG_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const bigSt & rhs) const {
        bool ret = true;
        ret = ret && (b.word[ 0 ] == rhs.b.word[ 0 ]);
        ret = ret && (b.word[ 1 ] == rhs.b.word[ 1 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bigSt & v, const std::string & NAME ) {
        sc_trace(tf,v.b.word[ 0 ], NAME + ".b.word[ 0 ]");
        sc_trace(tf,v.b.word[ 1 ], NAME + ".b.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  bigSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("b:0x{:08x}{:016x}",
           b.word[1],
           b.word[0]
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, bigSt::_byteWidth);
        pack_bits((uint64_t *)&_ret, 0, (uint64_t *)&b, BIG_WIDTH);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        b.word[0] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        b.word[1] = ((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 32) - 1));
    }
    inline sc_bv<bigSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bigSt::_bitWidth> packed_data;
        packed_data.range(63, 0) = b.word[0];
        packed_data.range(95, 64) = b.word[1];
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bigSt::_bitWidth> packed_data)
    {
        b.word[0] = (uint64_t) packed_data.range(63, 0).to_uint64();
        b.word[1] = (uint64_t) packed_data.range(95, 64).to_uint64();
    }
    explicit bigSt(sc_bv<bigSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bigSt(
        bigT b_) :
        b(b_)
    {}
    explicit bigSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct testDataSt {
    dataT data; //

    testDataSt() {}

    static constexpr uint16_t _bitWidth = 128;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const testDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
        ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const testDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  testDataSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:016x}{:016x}",
           data.word[1],
           data.word[0]
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, testDataSt::_byteWidth);
        pack_bits((uint64_t *)&_ret, 0, (uint64_t *)&data, 128);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data.word[0] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        data.word[1] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
    }
    inline sc_bv<testDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<testDataSt::_bitWidth> packed_data;
        packed_data.range(63, 0) = data.word[0];
        packed_data.range(127, 64) = data.word[1];
        return packed_data;
    }
    inline void sc_unpack(sc_bv<testDataSt::_bitWidth> packed_data)
    {
        data.word[0] = (uint64_t) packed_data.range(63, 0).to_uint64();
        data.word[1] = (uint64_t) packed_data.range(127, 64).to_uint64();
    }
    explicit testDataSt(sc_bv<testDataSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit testDataSt(
        dataT data_) :
        data(data_)
    {}
    explicit testDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct testDataHdrSt {
    cmdidT cmdid; //Command context

    testDataHdrSt() {}

    static constexpr uint16_t _bitWidth = NUM_COMMANDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const testDataHdrSt & rhs) const {
        bool ret = true;
        ret = ret && (cmdid == rhs.cmdid);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const testDataHdrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.cmdid, NAME + ".cmdid");
    }
    inline friend ostream& operator << ( ostream& os,  testDataHdrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("cmdid:0x{:03x}",
           (uint64_t) cmdid
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, testDataHdrSt::_byteWidth);
        _ret = cmdid;
    }
    inline void unpack(const _packedSt &_src)
    {
        cmdid = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    inline sc_bv<testDataHdrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<testDataHdrSt::_bitWidth> packed_data;
        packed_data.range(9, 0) = cmdid;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<testDataHdrSt::_bitWidth> packed_data)
    {
        cmdid = (cmdidT) packed_data.range(9, 0).to_uint64();
    }
    explicit testDataHdrSt(sc_bv<testDataHdrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit testDataHdrSt(
        cmdidT cmdid_) :
        cmdid(cmdid_)
    {}
    explicit testDataHdrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct lengthHdrSt {
    lengthT length; //

    lengthHdrSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const lengthHdrSt & rhs) const {
        bool ret = true;
        ret = ret && (length == rhs.length);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const lengthHdrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.length, NAME + ".length");
    }
    inline friend ostream& operator << ( ostream& os,  lengthHdrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("length:0x{:04x}",
           (uint64_t) length
        ));
    }
    static const char* getValueType(void) { return( "length" );}
    inline uint64_t getStructValue(void) const { return( length );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, lengthHdrSt::_byteWidth);
        _ret = length;
    }
    inline void unpack(const _packedSt &_src)
    {
        length = (lengthT)((_src));
    }
    inline sc_bv<lengthHdrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<lengthHdrSt::_bitWidth> packed_data;
        packed_data.range(15, 0) = length;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<lengthHdrSt::_bitWidth> packed_data)
    {
        length = (lengthT) packed_data.range(15, 0).to_uint64();
    }
    explicit lengthHdrSt(sc_bv<lengthHdrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit lengthHdrSt(
        lengthT length_) :
        length(length_)
    {}
    explicit lengthHdrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cmdidHdrSt {
    cmdidT cmdid; //Command context

    cmdidHdrSt() {}

    static constexpr uint16_t _bitWidth = NUM_COMMANDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const cmdidHdrSt & rhs) const {
        bool ret = true;
        ret = ret && (cmdid == rhs.cmdid);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cmdidHdrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.cmdid, NAME + ".cmdid");
    }
    inline friend ostream& operator << ( ostream& os,  cmdidHdrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("cmdid:0x{:03x}",
           (uint64_t) cmdid
        ));
    }
    static const char* getValueType(void) { return( "tracker:cmdid" );}
    inline uint64_t getStructValue(void) const { return( cmdid );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, cmdidHdrSt::_byteWidth);
        _ret = cmdid;
    }
    inline void unpack(const _packedSt &_src)
    {
        cmdid = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    inline sc_bv<cmdidHdrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<cmdidHdrSt::_bitWidth> packed_data;
        packed_data.range(9, 0) = cmdid;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<cmdidHdrSt::_bitWidth> packed_data)
    {
        cmdid = (cmdidT) packed_data.range(9, 0).to_uint64();
    }
    explicit cmdidHdrSt(sc_bv<cmdidHdrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit cmdidHdrSt(
        cmdidT cmdid_) :
        cmdid(cmdid_)
    {}
    explicit cmdidHdrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace nested_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace nested_ns {
template<typename Config>
class test_nested_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace nested_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace nested_ns {
template<typename Config>
std::string test_nested_structs<Config>::name(void) { return "test_nested_structs"; }
template<typename Config>
void test_nested_structs<Config>::test(void) {
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
        bigSt::_packedSt packed;
        memset(&packed, pattern, bigSt::_byteWidth);
        sc_bv<bigSt::_bitWidth> aInit;
        sc_bv<bigSt::_bitWidth> aTest;
        for (int i = 0; i < bigSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, bigSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        bigSt a;
        a.sc_unpack(aInit);
        bigSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"bigSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"bigSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = bigSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"bigSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        testDataSt::_packedSt packed;
        memset(&packed, pattern, testDataSt::_byteWidth);
        sc_bv<testDataSt::_bitWidth> aInit;
        sc_bv<testDataSt::_bitWidth> aTest;
        for (int i = 0; i < testDataSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, testDataSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        testDataSt a;
        a.sc_unpack(aInit);
        testDataSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"testDataSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"testDataSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = testDataSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"testDataSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        testDataHdrSt::_packedSt packed;
        memset(&packed, pattern, testDataHdrSt::_byteWidth);
        sc_bv<testDataHdrSt::_bitWidth> aInit;
        sc_bv<testDataHdrSt::_bitWidth> aTest;
        for (int i = 0; i < testDataHdrSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, testDataHdrSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        testDataHdrSt a;
        a.sc_unpack(aInit);
        testDataHdrSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"testDataHdrSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"testDataHdrSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = testDataHdrSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"testDataHdrSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        lengthHdrSt::_packedSt packed;
        memset(&packed, pattern, lengthHdrSt::_byteWidth);
        sc_bv<lengthHdrSt::_bitWidth> aInit;
        sc_bv<lengthHdrSt::_bitWidth> aTest;
        for (int i = 0; i < lengthHdrSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, lengthHdrSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        lengthHdrSt a;
        a.sc_unpack(aInit);
        lengthHdrSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"lengthHdrSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"lengthHdrSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = lengthHdrSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"lengthHdrSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        cmdidHdrSt::_packedSt packed;
        memset(&packed, pattern, cmdidHdrSt::_byteWidth);
        sc_bv<cmdidHdrSt::_bitWidth> aInit;
        sc_bv<cmdidHdrSt::_bitWidth> aTest;
        for (int i = 0; i < cmdidHdrSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, cmdidHdrSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        cmdidHdrSt a;
        a.sc_unpack(aInit);
        cmdidHdrSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"cmdidHdrSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"cmdidHdrSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = cmdidHdrSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"cmdidHdrSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace nested_ns

// GENERATED_CODE_END
