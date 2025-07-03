// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "mixedBlockCIncludes.h"

// GENERATED_CODE_PARAM --context=mixedBlockC.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool seeSt::operator == (const seeSt & rhs) const {
    bool ret = true; 
    ret = ret && (variablec == rhs.variablec);
    ret = ret && (variablec2 == rhs.variablec2);
    return ( ret );
    }
std::string seeSt::prt(bool all) const
{
    return (fmt::format("variablec:0x{:01x} variablec2:0x{:01x}",
       (uint64_t) variablec,
       (uint64_t) variablec2
    ));
}
void seeSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, seeSt::_byteWidth);
    _ret = variablec2;
    _ret |= (uint8_t)variablec << (3 & 7);
}
void seeSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    variablec2 = (cSizePlusT)((_src >> (_pos & 7)) & ((1ULL << 3) - 1));
    _pos += 3;
    variablec = (cSizeT)((_src >> (_pos & 7)) & ((1ULL << 2) - 1));
}
sc_bv<5> seeSt::sc_pack(void) const
{
    sc_bv<5> packed_data;
    packed_data.range(2, 0) = variablec2;
    packed_data.range(4, 3) = variablec;
    return packed_data;
}
void seeSt::sc_unpack(sc_bv<5> packed_data)
{
    variablec2 = (cSizePlusT) packed_data.range(2, 0).to_uint64();
    variablec = (cSizeT) packed_data.range(4, 3).to_uint64();
}
bool cHeaderSt::operator == (const cHeaderSt & rhs) const {
    bool ret = true; 
    ret = ret && (hdr == rhs.hdr);
    return ( ret );
    }
std::string cHeaderSt::prt(bool all) const
{
    return (fmt::format("hdr:0x{:04x}",
       (uint64_t) hdr
    ));
}
void cHeaderSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, cHeaderSt::_byteWidth);
    _ret = hdr;
}
void cHeaderSt::unpack(_packedSt &_src)
{
    hdr = (cBiggerT)((_src) & ((1ULL << 13) - 1));
}
sc_bv<13> cHeaderSt::sc_pack(void) const
{
    sc_bv<13> packed_data;
    packed_data.range(12, 0) = hdr;
    return packed_data;
}
void cHeaderSt::sc_unpack(sc_bv<13> packed_data)
{
    hdr = (cBiggerT) packed_data.range(12, 0).to_uint64();
}

// GENERATED_CODE_END


