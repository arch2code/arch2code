#ifndef NESTEDTOPINCLUDES_H
#define NESTEDTOPINCLUDES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <cstdint>

// GENERATED_CODE_PARAM --context=nestedTop.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
#define NUM_COMMANDS                  1024  // Number of Commands
#define NUM_COMMANDS_LOG2               10  // Number of Commands log2
#define BIG_WIDTH                       96  // big width test case
#define NUM_FIRST_TAGS                  64  // Num first Tags
#define NUM_FIRST_TAGS_LOG2              6  // Num first Tags Log2
#define NUM_SECOND_TAGS               1024  // Num second Tags
#define NUM_SECOND_TAGS_LOG2            10  // Num second Tags Log2
#define NUM_THIRD_TAGS                1024  // Num third Tags
#define NUM_THIRD_TAGS_LOG2             10  // Num third Tags Log2
#define NUM_TAGS                      2112  // Num Tags
#define NUM_TAGS_LOG2                   12  // Num Tags Log2
#define TAGBASE_SECONDTAG                0  // base value for Tag type 2
#define TAGBASE_THIRDTAG              1024  // base value for Tag type 3
#define TAGBASE_FIRSTTAG              2048  // base value for Tag type 1

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types 
// types
typedef uint16_t tagT; // [12] Read Tag
typedef uint16_t cmdidT; // [10] Command ID
struct bigT { uint64_t word[ 2 ]; }; // [96] big width test case
struct dataT { uint64_t word[ 2 ]; }; // [128] Data
typedef uint16_t lengthT; // [16] Length of transfer

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums 
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

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct test_st {
    cmdidT a; //

    test_st() {}

    static constexpr uint16_t _bitWidth = 10;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const test_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test_st & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  test_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<10> sc_pack(void) const;
    void sc_unpack(sc_bv<10> packed_data);
    explicit test_st(sc_bv<10> packed_data) { sc_unpack(packed_data); }
    explicit test_st(
        cmdidT a_) :
        a(a_)
    {}
    explicit test_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bigSt {
    bigT b; //

    bigSt() {}

    static constexpr uint16_t _bitWidth = 96;
    static constexpr uint16_t _byteWidth = 12;
    typedef uint64_t _packedSt[2];
    bool operator == (const bigSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const bigSt & v, const std::string & NAME ) {
        sc_trace(tf,v.b.word[ 0 ], NAME + ".b.word[ 0 ]");
        sc_trace(tf,v.b.word[ 1 ], NAME + ".b.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  bigSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<96> sc_pack(void) const;
    void sc_unpack(sc_bv<96> packed_data);
    explicit bigSt(sc_bv<96> packed_data) { sc_unpack(packed_data); }
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
    static constexpr uint16_t _byteWidth = 16;
    typedef uint64_t _packedSt[2];
    bool operator == (const testDataSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const testDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  testDataSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<128> sc_pack(void) const;
    void sc_unpack(sc_bv<128> packed_data);
    explicit testDataSt(sc_bv<128> packed_data) { sc_unpack(packed_data); }
    explicit testDataSt(
        dataT data_) :
        data(data_)
    {}
    explicit testDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct testDataHdrSt {
    cmdidT cmdid; //

    testDataHdrSt() {}

    static constexpr uint16_t _bitWidth = 10;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const testDataHdrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const testDataHdrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.cmdid, NAME + ".cmdid");
    }
    inline friend ostream& operator << ( ostream& os,  testDataHdrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<10> sc_pack(void) const;
    void sc_unpack(sc_bv<10> packed_data);
    explicit testDataHdrSt(sc_bv<10> packed_data) { sc_unpack(packed_data); }
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
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const lengthHdrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const lengthHdrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.length, NAME + ".length");
    }
    inline friend ostream& operator << ( ostream& os,  lengthHdrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "length" );}
    inline uint64_t getStructValue(void) const { return( length );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<16> sc_pack(void) const;
    void sc_unpack(sc_bv<16> packed_data);
    explicit lengthHdrSt(sc_bv<16> packed_data) { sc_unpack(packed_data); }
    explicit lengthHdrSt(
        lengthT length_) :
        length(length_)
    {}
    explicit lengthHdrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cmdidHdrSt {
    cmdidT cmdid; //

    cmdidHdrSt() {}

    static constexpr uint16_t _bitWidth = 10;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const cmdidHdrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const cmdidHdrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.cmdid, NAME + ".cmdid");
    }
    inline friend ostream& operator << ( ostream& os,  cmdidHdrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "tracker:cmdid" );}
    inline uint64_t getStructValue(void) const { return( cmdid );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<10> sc_pack(void) const;
    void sc_unpack(sc_bv<10> packed_data);
    explicit cmdidHdrSt(sc_bv<10> packed_data) { sc_unpack(packed_data); }
    explicit cmdidHdrSt(
        cmdidT cmdid_) :
        cmdid(cmdid_)
    {}
    explicit cmdidHdrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END

#endif //NESTEDTOPINCLUDES_H

