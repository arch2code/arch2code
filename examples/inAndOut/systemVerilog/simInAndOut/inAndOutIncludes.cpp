// copyright QiStor 2024
#include "inAndOutIncludes.h"
#include "logging.h"
// GENERATED_CODE_PARAM --context=inAndOut.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool aSt::operator == (const aSt & rhs) const {
    bool ret = true; 
    for(int i=0; i<ASIZE2; i++) {
        ret = ret && (variablea[i] == rhs.variablea[i]);
    }
    return ( ret );
    }
std::string aSt::prt(bool all) const
{
    return (fmt::format("variablea[0:1]: {}",
       staticArrayPrt<aSizeT, ASIZE2>(variablea, all)
    ));
}
void aSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aSt::_byteWidth);
    uint16_t _pos{0};
    for(int i=0; i<ASIZE2; i++) {
        pack_bits((uint64_t *)&_ret, _pos, variablea[i], 1);
        _pos += 1;
    }
}
void aSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    for(int i=0; i<ASIZE2; i++) {
        uint16_t _bits = 1;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(8-(_pos & 7)));
        variablea[i] = (aSizeT)((_src >> (_pos & 7)) & 1);
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 8)) {
            variablea[i] = (aSizeT)(variablea[i] | ((_src << _consume) & 1));
            _pos += _bits;
        }
    }
}
sc_bv<2> aSt::sc_pack(void) const
{
    sc_bv<2> packed_data;
    for(int i=0; i<ASIZE2; i++) {
        packed_data.range(0+(i+1)*1-1, 0+i*1) = variablea[i];
    }
    return packed_data;
}
void aSt::sc_unpack(sc_bv<2> packed_data)
{
    for(int i=0; i<ASIZE2; i++) {
        variablea[i] = (aSizeT) packed_data.range(0+(i+1)*1-1, 0+i*1).to_uint64();
    }
}
bool bSt::operator == (const bSt & rhs) const {
    bool ret = true; 
    ret = ret && (variableb == rhs.variableb);
    return ( ret );
    }
std::string bSt::prt(bool all) const
{
    return (fmt::format("variableb:0x{:02x}",
       (uint64_t) variableb
    ));
}
void bSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bSt::_byteWidth);
    _ret = variableb;
}
void bSt::unpack(_packedSt &_src)
{
    variableb = (bSizeT)((_src) & ((1ULL << 5) - 1));
}
sc_bv<5> bSt::sc_pack(void) const
{
    sc_bv<5> packed_data;
    packed_data.range(4, 0) = variableb;
    return packed_data;
}
void bSt::sc_unpack(sc_bv<5> packed_data)
{
    variableb = (bSizeT) packed_data.range(4, 0).to_uint64();
}
bool bBSt::operator == (const bBSt & rhs) const {
    bool ret = true; 
    ret = ret && (ready == rhs.ready);
    return ( ret );
    }
std::string bBSt::prt(bool all) const
{
    return (fmt::format("ready:{}",
       readyT_prt( ready )
    ));
}
void bBSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bBSt::_byteWidth);
    _ret = ready;
}
void bBSt::unpack(_packedSt &_src)
{
    ready = (readyT)((_src) & 1);
}
bool bBSt::sc_pack(void) const
{
    bool packed_data;
    packed_data = (bool) ready;
    return packed_data;
}
void bBSt::sc_unpack(bool packed_data)
{
    ready = (readyT) packed_data;
}
void bBSt::sc_unpack(sc_bv<1> packed_data)
{
    ready = (readyT) packed_data.range(0, 0).to_uint64();
}
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
    variablec2 = (threeBitT)((_src >> (_pos & 7)) & ((1ULL << 3) - 1));
    _pos += 3;
    variablec = (twoBitT)((_src >> (_pos & 7)) & ((1ULL << 2) - 1));
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
    variablec2 = (threeBitT) packed_data.range(2, 0).to_uint64();
    variablec = (twoBitT) packed_data.range(4, 3).to_uint64();
}
bool dSt::operator == (const dSt & rhs) const {
    bool ret = true; 
    ret = ret && (variabled == rhs.variabled);
    ret = ret && (variabled2 == rhs.variabled2);
    return ( ret );
    }
std::string dSt::prt(bool all) const
{
    return (fmt::format("variabled:0x{:01x} variabled2:0x{:01x}",
       (uint64_t) variabled,
       (uint64_t) variabled2
    ));
}
void dSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, dSt::_byteWidth);
    _ret = variabled2;
    _ret |= (uint8_t)variabled << (4 & 7);
}
void dSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    variabled2 = (fourBitT)((_src >> (_pos & 7)) & ((1ULL << 4) - 1));
    _pos += 4;
    variabled = (threeBitT)((_src >> (_pos & 7)) & ((1ULL << 3) - 1));
}
sc_bv<7> dSt::sc_pack(void) const
{
    sc_bv<7> packed_data;
    packed_data.range(3, 0) = variabled2;
    packed_data.range(6, 4) = variabled;
    return packed_data;
}
void dSt::sc_unpack(sc_bv<7> packed_data)
{
    variabled2 = (fourBitT) packed_data.range(3, 0).to_uint64();
    variabled = (threeBitT) packed_data.range(6, 4).to_uint64();
}
bool eNestedSt::operator == (const eNestedSt & rhs) const {
    bool ret = true; 
    ret = ret && (variablea == rhs.variablea);
    ret = ret && (bob == rhs.bob);
    for(int i=0; i<2; i++) {
        ret = ret && (joe[i] == rhs.joe[i]);
    }
    return ( ret );
    }
std::string eNestedSt::prt(bool all) const
{
    return (fmt::format("variablea:0x{:01x} bob:<{}>{}",
       (uint64_t) variablea,
       bob.prt(all),
       structArrayPrt<seeSt, 2>(joe, "joe", all)
    ));
}
void eNestedSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, eNestedSt::_byteWidth);
    uint16_t _pos{0};
    for(int i=0; i<2; i++) {
        seeSt::_packedSt _tmp{0};
        joe[i].pack(_tmp);
        _ret |= (uint32_t)_tmp << (_pos & 31);
        _pos += 5;
    }
    {
        dSt::_packedSt _tmp{0};
        bob.pack(_tmp);
        _ret |= (uint32_t)_tmp << (10 & 31);
    }
    _ret |= (uint32_t)variablea << (17 & 31);
}
void eNestedSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    for(int i=0; i<2; i++) {
        uint16_t _bits = 5;
        uint16_t _consume;
        {
            seeSt::_packedSt _tmp{0};
            pack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, 10);
            joe[i].unpack(_tmp);
        }
        _pos += 5;
    }
    {
        dSt::_packedSt _tmp{0};
        pack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, 7);
        bob.unpack(_tmp);
    }
    _pos += 7;
    variablea = (aSizeT)((_src >> (_pos & 31)) & 1);
}
sc_bv<18> eNestedSt::sc_pack(void) const
{
    sc_bv<18> packed_data;
    for(int i=0; i<2; i++) {
        packed_data.range(0+(i+1)*5-1, 0+i*5) = joe[i].sc_pack();
    }
    packed_data.range(16, 10) = bob.sc_pack();
    packed_data.range(17, 17) = variablea;
    return packed_data;
}
void eNestedSt::sc_unpack(sc_bv<18> packed_data)
{
    for(int i=0; i<2; i++) {
        joe[i].sc_unpack(packed_data.range(0+(i+1)*5-1, 0+i*5));
    }
    bob.sc_unpack(packed_data.range(16, 10));
    variablea = (aSizeT) packed_data.range(17, 17).to_uint64();
}
bool bSizeSt::operator == (const bSizeSt & rhs) const {
    bool ret = true; 
    ret = ret && (index == rhs.index);
    return ( ret );
    }
std::string bSizeSt::prt(bool all) const
{
    return (fmt::format("index:0x{:02x}",
       (uint64_t) index
    ));
}
void bSizeSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bSizeSt::_byteWidth);
    _ret = index;
}
void bSizeSt::unpack(_packedSt &_src)
{
    index = (bSizeT)((_src) & ((1ULL << 5) - 1));
}
sc_bv<5> bSizeSt::sc_pack(void) const
{
    sc_bv<5> packed_data;
    packed_data.range(4, 0) = index;
    return packed_data;
}
void bSizeSt::sc_unpack(sc_bv<5> packed_data)
{
    index = (bSizeT) packed_data.range(4, 0).to_uint64();
}
bool eHeaderSt::operator == (const eHeaderSt & rhs) const {
    bool ret = true; 
    ret = ret && (hdr == rhs.hdr);
    return ( ret );
    }
std::string eHeaderSt::prt(bool all) const
{
    return (fmt::format("hdr:0x{:01x}",
       (uint64_t) hdr
    ));
}
void eHeaderSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, eHeaderSt::_byteWidth);
    _ret = hdr;
}
void eHeaderSt::unpack(_packedSt &_src)
{
    hdr = (aBiggerT)((_src) & ((1ULL << 2) - 1));
}
sc_bv<2> eHeaderSt::sc_pack(void) const
{
    sc_bv<2> packed_data;
    packed_data.range(1, 0) = hdr;
    return packed_data;
}
void eHeaderSt::sc_unpack(sc_bv<2> packed_data)
{
    hdr = (aBiggerT) packed_data.range(1, 0).to_uint64();
}

// GENERATED_CODE_END


