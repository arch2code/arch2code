
#ifndef NESTEDINCLUDESFW_H_
#define NESTEDINCLUDESFW_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=nested.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
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

    test_st() { memset(this, 0, sizeof(test_st)); }

    static constexpr uint16_t _bitWidth = NUM_COMMANDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test_st::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    explicit test_st(
        cmdidT a_) :
        a(a_)
    {}

};
struct bigSt {
    bigT b; //

    bigSt() { memset(this, 0, sizeof(bigSt)); }

    static constexpr uint16_t _bitWidth = BIG_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
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
    explicit bigSt(
        bigT b_) :
        b(b_)
    {}

};
struct testDataSt {
    dataT data; //

    testDataSt() { memset(this, 0, sizeof(testDataSt)); }

    static constexpr uint16_t _bitWidth = 128;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
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
    explicit testDataSt(
        dataT data_) :
        data(data_)
    {}

};
struct testDataHdrSt {
    cmdidT cmdid; //Command context

    testDataHdrSt() { memset(this, 0, sizeof(testDataHdrSt)); }

    static constexpr uint16_t _bitWidth = NUM_COMMANDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, testDataHdrSt::_byteWidth);
        _ret = cmdid;
    }
    inline void unpack(const _packedSt &_src)
    {
        cmdid = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    explicit testDataHdrSt(
        cmdidT cmdid_) :
        cmdid(cmdid_)
    {}

};
struct lengthHdrSt {
    lengthT length; //

    lengthHdrSt() { memset(this, 0, sizeof(lengthHdrSt)); }

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, lengthHdrSt::_byteWidth);
        _ret = length;
    }
    inline void unpack(const _packedSt &_src)
    {
        length = (lengthT)((_src));
    }
    explicit lengthHdrSt(
        lengthT length_) :
        length(length_)
    {}

};
struct cmdidHdrSt {
    cmdidT cmdid; //Command context

    cmdidHdrSt() { memset(this, 0, sizeof(cmdidHdrSt)); }

    static constexpr uint16_t _bitWidth = NUM_COMMANDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, cmdidHdrSt::_byteWidth);
        _ret = cmdid;
    }
    inline void unpack(const _packedSt &_src)
    {
        cmdid = (cmdidT)((_src) & ((1ULL << 10) - 1));
    }
    explicit cmdidHdrSt(
        cmdidT cmdid_) :
        cmdid(cmdid_)
    {}

};

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //NESTEDINCLUDESFW_H_
