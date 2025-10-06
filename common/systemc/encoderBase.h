#ifndef ENCODERBASE_H
#define ENCODERBASE_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "logging.h"
#include <format>
#include <tuple>
#include "q_assert.h"

struct encodedTypeInfo {
        uint64_t encodingValue;
        uint64_t encodingMask;
        uint64_t max;
        uint64_t hexWidth;
        std::string name;
        std::string varName;
};

// ENCODEDTYPE is the type of the encoded value
// ENUMTYPE is the type of value being encoded
// ie
// ENCODEDTYPE encValue = f(ENUMTYPE encType, value)
template <typename ENCODEDTYPE, typename ENUMTYPE>
struct encoderBase
{
public:
    encoderBase(std::vector<encodedTypeInfo> encodeInfo_, uint8_t totalBits_, uint64_t maxEncodedValue_, bool zeroBased_) :
        encodeInfo(encodeInfo_),
        totalBits(totalBits_),
        maxEncodedValue(maxEncodedValue_),
        zeroBased(zeroBased_),
        maxEncodedValueMask((((uint64_t)1<<totalBits_) - 1 ))
         {}
    ENCODEDTYPE encode(uint64_t tag, ENUMTYPE tagType)
    {
        Q_ASSERT_CTX(tag <= encodeInfo[tagType].max, getName(tagType), std::format("Tag out of range tag=0x{:x}", tag));
        return( encodeInfo[tagType].encodingValue | tag );
    }
    std::tuple<uint64_t, ENUMTYPE> decode(ENCODEDTYPE encodedTag)
    {
        int type = 0;
        // simple linear search as there are only a few entries
        for (auto it = begin(encodeInfo); it != end(encodeInfo); it++)
        {
            if ((encodedTag & it->encodingMask) == it->encodingValue )
            {
                // tag is in the range
                return {encodedTag & (it->encodingMask ^ maxEncodedValueMask) , (ENUMTYPE)type};
            }
            type++;
        }
        Q_ASSERT_CTX(false, "", std::format("Tag out of range tag=0x{:x}", encodedTag));
        return {0,(ENUMTYPE)0};
    }
    std::string getName(ENUMTYPE tagType) {return(encodeInfo[tagType].name);}
    std::string prt(ENCODEDTYPE encodedTag)
    {
        auto [tag, tagType] = decode(encodedTag);
        std::stringstream ss;
        ss << encodeInfo[tagType].varName << ":0x" << std::hex << std::setw(encodeInfo[tagType].hexWidth) << std::setfill('0') << tag;
        return(ss.str());
    }
    uint64_t getSize(void) {return(encodeInfo.size());}

private:
    std::vector<encodedTypeInfo> encodeInfo;
    uint8_t totalBits;
    uint64_t maxEncodedValue;
    bool zeroBased;
    uint64_t maxEncodedValueMask;
};


enum  encodedTagTestTypeT {
    TAG_TYPE_THIRDTAGA=0,     // Tag type 3
    TAG_TYPE_SECONDTAGA=1,    // Tag type 2
    TAG_TYPE_FIRSTTAGA=2,     // Tag type 1
    TAG_OTHER=3 };

class encodeTagTest : public encoderBase<uint32_t, encodedTagTestTypeT>
{
public:
    encodeTagTest() : encoderBase<uint32_t, encodedTagTestTypeT>(
        {   // encVal    encMask     max       hexdigits name            varname
            {0x00000000, 0xFFFFFF80, 0x0000007F, 2, "TAG_TYPE_THIRDTAG", "third"},
            {0x00000080, 0xFFFFFF80, 0x0000007F, 2, "TAG_TYPE_SECONDTAG", "second"},
            {0x00000100, 0xFFFFFFC0, 0x0000003F, 2, "TAG_TYPE_FIRSTTAG", "first"}
        }, 32, 0x0000013F, true) {}

};
class encodeTagTest2 : public encoderBase<uint32_t, encodedTagTestTypeT>
{
public:
    encodeTagTest2() : encoderBase<uint32_t, encodedTagTestTypeT>(
        { // encVal  encMask max   hexdigits  name           varname
            {0xFF80, 0xFF80, 0x007F, 2, "TAG_TYPE_THIRDTAG", "third"},
            {0xFF00, 0xFF80, 0x007F, 2, "TAG_TYPE_SECONDTAG", "second"},
            {0xFEC0, 0xFFC0, 0x003F, 2, "TAG_TYPE_FIRSTTAG", "first"},
            {0x0000, 0x0000, 0xFEC0, 4, "TAG_OTHER", "other"}

        }, 16, 0xFFFF, true) {}

};

#endif //(ENCODERBASE_H)
