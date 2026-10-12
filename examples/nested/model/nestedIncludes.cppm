
// GENERATED_CODE_PARAM --project=nested --context=../../yaml/nested.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module nested;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace nested_ns {
//constants
inline constexpr uint32_t NUM_COMMANDS = 1024;  // Number of Commands
inline constexpr uint32_t NUM_COMMANDS_LOG2 = 10;  // Number of Commands log2
inline constexpr uint32_t BIG_WIDTH = 96;  // big width test case
inline constexpr uint32_t NUM_FIRST_TAGS = 64;  // Num first Tags
inline constexpr uint32_t NUM_FIRST_TAGS_LOG2 = 6;  // Num first Tags Log2
inline constexpr uint32_t NUM_SECOND_TAGS = 1024;  // Num second Tags
inline constexpr uint32_t NUM_SECOND_TAGS_LOG2 = 10;  // Num second Tags Log2
inline constexpr uint32_t NUM_THIRD_TAGS = 1024;  // Num third Tags
inline constexpr uint32_t NUM_THIRD_TAGS_LOG2 = 10;  // Num third Tags Log2
inline constexpr uint32_t NUM_TAGS = 2112;  // Num Tags
inline constexpr uint32_t NUM_TAGS_LOG2 = 12;  // Num Tags Log2
inline constexpr uint32_t TAGBASE_SECONDTAG = 0;  // base value for Tag type 2
inline constexpr uint32_t TAGBASE_THIRDTAG = 1024;  // base value for Tag type 3
inline constexpr uint32_t TAGBASE_FIRSTTAG = 2048;  // base value for Tag type 1

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
        memset(&_ret, 0, sizeof(_ret));
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    inline sc_bv<test_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<test_st::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "test_st", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<test_st::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit test_st(const sc_bv<test_st::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)(_packed[i >> 1] >> ((i & 1) * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "bigSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<bigSt::_bitWidth> &packed_data)
    {
        _packedSt _words{};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _words[i >> 1] |= (uint64_t)packed_data.get_word(i) << ((i & 1) * 32);
        }
        unpack(_words);
    }
    explicit bigSt(const sc_bv<bigSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
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
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)(_packed[i >> 1] >> ((i & 1) * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "testDataSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<testDataSt::_bitWidth> &packed_data)
    {
        _packedSt _words{};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _words[i >> 1] |= (uint64_t)packed_data.get_word(i) << ((i & 1) * 32);
        }
        unpack(_words);
    }
    explicit testDataSt(const sc_bv<testDataSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
        _ret = cmdid;
    }
    inline void unpack(const _packedSt &_src)
    {
        cmdid = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    inline sc_bv<testDataHdrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<testDataHdrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "testDataHdrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<testDataHdrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit testDataHdrSt(const sc_bv<testDataHdrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
        _ret = length;
    }
    inline void unpack(const _packedSt &_src)
    {
        length = (lengthT)((_src));
    }
    inline sc_bv<lengthHdrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<lengthHdrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "lengthHdrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<lengthHdrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit lengthHdrSt(const sc_bv<lengthHdrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, sizeof(_ret));
        _ret = cmdid;
    }
    inline void unpack(const _packedSt &_src)
    {
        cmdid = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    inline sc_bv<cmdidHdrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<cmdidHdrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "cmdidHdrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<cmdidHdrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit cmdidHdrSt(const sc_bv<cmdidHdrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
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
inline sc_bv<test_st::_bitWidth> testRefPack(const test_st &x);
inline void testRefUnpack(test_st &x, const sc_bv<test_st::_bitWidth> &packed_data);
inline sc_bv<bigSt::_bitWidth> testRefPack(const bigSt &x);
inline void testRefUnpack(bigSt &x, const sc_bv<bigSt::_bitWidth> &packed_data);
inline sc_bv<testDataSt::_bitWidth> testRefPack(const testDataSt &x);
inline void testRefUnpack(testDataSt &x, const sc_bv<testDataSt::_bitWidth> &packed_data);
inline sc_bv<testDataHdrSt::_bitWidth> testRefPack(const testDataHdrSt &x);
inline void testRefUnpack(testDataHdrSt &x, const sc_bv<testDataHdrSt::_bitWidth> &packed_data);
inline sc_bv<lengthHdrSt::_bitWidth> testRefPack(const lengthHdrSt &x);
inline void testRefUnpack(lengthHdrSt &x, const sc_bv<lengthHdrSt::_bitWidth> &packed_data);
inline sc_bv<cmdidHdrSt::_bitWidth> testRefPack(const cmdidHdrSt &x);
inline void testRefUnpack(cmdidHdrSt &x, const sc_bv<cmdidHdrSt::_bitWidth> &packed_data);
inline sc_bv<test_st::_bitWidth> testRefPack(const test_st &x)
{
    sc_bv<test_st::_bitWidth> packed_data;
    packed_data.range(0+NUM_COMMANDS_LOG2-1, 0) = x.a;
    return packed_data;
}
inline void testRefUnpack(test_st &x, const sc_bv<test_st::_bitWidth> &packed_data)
{
    x.a = (cmdidT) packed_data.range(0+NUM_COMMANDS_LOG2-1, 0).to_uint64();
}
inline sc_bv<bigSt::_bitWidth> testRefPack(const bigSt &x)
{
    sc_bv<bigSt::_bitWidth> packed_data;
    packed_data.range(0+63, 0+0) = x.b.word[0];
    packed_data.range(0+95, 0+64) = x.b.word[1];
    return packed_data;
}
inline void testRefUnpack(bigSt &x, const sc_bv<bigSt::_bitWidth> &packed_data)
{
    x.b.word[0] = (uint64_t) packed_data.range(0+63, 0+0).to_uint64();
    x.b.word[1] = (uint64_t) packed_data.range(0+95, 0+64).to_uint64();
}
inline sc_bv<testDataSt::_bitWidth> testRefPack(const testDataSt &x)
{
    sc_bv<testDataSt::_bitWidth> packed_data;
    packed_data.range(0+63, 0+0) = x.data.word[0];
    packed_data.range(0+127, 0+64) = x.data.word[1];
    return packed_data;
}
inline void testRefUnpack(testDataSt &x, const sc_bv<testDataSt::_bitWidth> &packed_data)
{
    x.data.word[0] = (uint64_t) packed_data.range(0+63, 0+0).to_uint64();
    x.data.word[1] = (uint64_t) packed_data.range(0+127, 0+64).to_uint64();
}
inline sc_bv<testDataHdrSt::_bitWidth> testRefPack(const testDataHdrSt &x)
{
    sc_bv<testDataHdrSt::_bitWidth> packed_data;
    packed_data.range(0+NUM_COMMANDS_LOG2-1, 0) = x.cmdid;
    return packed_data;
}
inline void testRefUnpack(testDataHdrSt &x, const sc_bv<testDataHdrSt::_bitWidth> &packed_data)
{
    x.cmdid = (cmdidT) packed_data.range(0+NUM_COMMANDS_LOG2-1, 0).to_uint64();
}
inline sc_bv<lengthHdrSt::_bitWidth> testRefPack(const lengthHdrSt &x)
{
    sc_bv<lengthHdrSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.length;
    return packed_data;
}
inline void testRefUnpack(lengthHdrSt &x, const sc_bv<lengthHdrSt::_bitWidth> &packed_data)
{
    x.length = (lengthT) packed_data.range(0+16-1, 0).to_uint64();
}
inline sc_bv<cmdidHdrSt::_bitWidth> testRefPack(const cmdidHdrSt &x)
{
    sc_bv<cmdidHdrSt::_bitWidth> packed_data;
    packed_data.range(0+NUM_COMMANDS_LOG2-1, 0) = x.cmdid;
    return packed_data;
}
inline void testRefUnpack(cmdidHdrSt &x, const sc_bv<cmdidHdrSt::_bitWidth> &packed_data)
{
    x.cmdid = (cmdidT) packed_data.range(0+NUM_COMMANDS_LOG2-1, 0).to_uint64();
}
} // namespace nested_ns
export namespace nested_test_ns {
class test_nested_structs {
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
} // namespace nested_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace nested_test_ns {
using namespace nested_ns;
std::string test_nested_structs::name(void) { return "test_nested_structs"; }
void test_nested_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<test_st>("test_st", patterns);
    roundTrip<bigSt>("bigSt", patterns);
    roundTrip<testDataSt>("testDataSt", patterns);
    roundTrip<testDataHdrSt>("testDataHdrSt", patterns);
    roundTrip<lengthHdrSt>("lengthHdrSt", patterns);
    roundTrip<cmdidHdrSt>("cmdidHdrSt", patterns);
}
} // namespace nested_test_ns

// GENERATED_CODE_END
