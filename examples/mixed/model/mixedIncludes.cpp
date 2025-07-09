// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "mixedIncludes.h"
#include "logging.h"
// GENERATED_CODE_PARAM --context=mixed.yaml
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
    ret = ret && (variablea2 == rhs.variablea2);
    return ( ret );
    }
std::string aSt::prt(bool all) const
{
    return (fmt::format("variablea[0:1]: {} variablea2:0x{:01x}",
       staticArrayPrt<aSizeT, ASIZE2>(variablea, all),
       (uint64_t) variablea2
    ));
}
void aSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aSt::_byteWidth);
    _ret = variablea2;
    uint16_t _pos{2};
    for(int i=0; i<ASIZE2; i++) {
        pack_bits((uint64_t *)&_ret, _pos, variablea[i], 1);
        _pos += 1;
    }
}
void aSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    variablea2 = (twoBitT)((_src >> (_pos & 7)) & ((1ULL << 2) - 1));
    _pos += 2;
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
sc_bv<4> aSt::sc_pack(void) const
{
    sc_bv<4> packed_data;
    packed_data.range(1, 0) = variablea2;
    for(int i=0; i<ASIZE2; i++) {
        packed_data.range(2+(i+1)*1-1, 2+i*1) = variablea[i];
    }
    return packed_data;
}
void aSt::sc_unpack(sc_bv<4> packed_data)
{
    variablea2 = (twoBitT) packed_data.range(1, 0).to_uint64();
    for(int i=0; i<ASIZE2; i++) {
        variablea[i] = (aSizeT) packed_data.range(2+(i+1)*1-1, 2+i*1).to_uint64();
    }
}
bool aASt::operator == (const aASt & rhs) const {
    bool ret = true; 
    ret = ret && (variablea == rhs.variablea);
    return ( ret );
    }
std::string aASt::prt(bool all) const
{
    return (fmt::format("variablea:0x{:01x}",
       (uint64_t) variablea
    ));
}
void aASt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aASt::_byteWidth);
    _ret = variablea;
}
void aASt::unpack(_packedSt &_src)
{
    variablea = (aSizeT)((_src) & 1);
}
bool aASt::sc_pack(void) const
{
    bool packed_data;
    packed_data = (bool) variablea;
    return packed_data;
}
void aASt::sc_unpack(bool packed_data)
{
    variablea = (aSizeT) packed_data;
}
void aASt::sc_unpack(sc_bv<1> packed_data)
{
    variablea = (aSizeT) packed_data.range(0, 0).to_uint64();
}
bool aRegSt::operator == (const aRegSt & rhs) const {
    bool ret = true; 
    ret = ret && (a == rhs.a);
    return ( ret );
    }
std::string aRegSt::prt(bool all) const
{
    return (fmt::format("a:0x{:02x}",
       (uint64_t) a
    ));
}
void aRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aRegSt::_byteWidth);
    _ret = a;
}
void aRegSt::unpack(_packedSt &_src)
{
    a = (sevenBitT)((_src) & ((1ULL << 7) - 1));
}
sc_bv<7> aRegSt::sc_pack(void) const
{
    sc_bv<7> packed_data;
    packed_data.range(6, 0) = a;
    return packed_data;
}
void aRegSt::sc_unpack(sc_bv<7> packed_data)
{
    a = (sevenBitT) packed_data.range(6, 0).to_uint64();
}
bool dRegSt::operator == (const dRegSt & rhs) const {
    bool ret = true; 
    ret = ret && (d == rhs.d);
    return ( ret );
    }
std::string dRegSt::prt(bool all) const
{
    return (fmt::format("d:0x{:02x}",
       (uint64_t) d
    ));
}
void dRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, dRegSt::_byteWidth);
    _ret = d;
}
void dRegSt::unpack(_packedSt &_src)
{
    d = (sevenBitT)((_src) & ((1ULL << 7) - 1));
}
sc_bv<7> dRegSt::sc_pack(void) const
{
    sc_bv<7> packed_data;
    packed_data.range(6, 0) = d;
    return packed_data;
}
void dRegSt::sc_unpack(sc_bv<7> packed_data)
{
    d = (sevenBitT) packed_data.range(6, 0).to_uint64();
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
bool nestedSt::operator == (const nestedSt & rhs) const {
    bool ret = true; 
    ret = ret && (variablea == rhs.variablea);
    ret = ret && (bob == rhs.bob);
    for(int i=0; i<2; i++) {
        ret = ret && (joe[i] == rhs.joe[i]);
    }
    return ( ret );
    }
std::string nestedSt::prt(bool all) const
{
    return (fmt::format("variablea:0x{:01x} bob:<{}>{}",
       (uint64_t) variablea,
       bob.prt(all),
       structArrayPrt<seeSt, 2>(joe, "joe", all)
    ));
}
void nestedSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, nestedSt::_byteWidth);
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
void nestedSt::unpack(_packedSt &_src)
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
sc_bv<18> nestedSt::sc_pack(void) const
{
    sc_bv<18> packed_data;
    for(int i=0; i<2; i++) {
        packed_data.range(0+(i+1)*5-1, 0+i*5) = joe[i].sc_pack();
    }
    packed_data.range(16, 10) = bob.sc_pack();
    packed_data.range(17, 17) = variablea;
    return packed_data;
}
void nestedSt::sc_unpack(sc_bv<18> packed_data)
{
    for(int i=0; i<2; i++) {
        joe[i].sc_unpack(packed_data.range(0+(i+1)*5-1, 0+i*5));
    }
    bob.sc_unpack(packed_data.range(16, 10));
    variablea = (aSizeT) packed_data.range(17, 17).to_uint64();
}
bool bSizeRegSt::operator == (const bSizeRegSt & rhs) const {
    bool ret = true; 
    ret = ret && (index == rhs.index);
    return ( ret );
    }
std::string bSizeRegSt::prt(bool all) const
{
    return (fmt::format("index:0x{:01x}",
       (uint64_t) index
    ));
}
void bSizeRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bSizeRegSt::_byteWidth);
    _ret = index;
}
void bSizeRegSt::unpack(_packedSt &_src)
{
    index = (bSizeT)((_src) & ((1ULL << 4) - 1));
}
sc_bv<4> bSizeRegSt::sc_pack(void) const
{
    sc_bv<4> packed_data;
    packed_data.range(3, 0) = index;
    return packed_data;
}
void bSizeRegSt::sc_unpack(sc_bv<4> packed_data)
{
    index = (bSizeT) packed_data.range(3, 0).to_uint64();
}
bool bSizeSt::operator == (const bSizeSt & rhs) const {
    bool ret = true; 
    ret = ret && (index == rhs.index);
    return ( ret );
    }
std::string bSizeSt::prt(bool all) const
{
    return (fmt::format("index:0x{:01x}",
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
    index = (bSizeT)((_src) & ((1ULL << 4) - 1));
}
sc_bv<4> bSizeSt::sc_pack(void) const
{
    sc_bv<4> packed_data;
    packed_data.range(3, 0) = index;
    return packed_data;
}
void bSizeSt::sc_unpack(sc_bv<4> packed_data)
{
    index = (bSizeT) packed_data.range(3, 0).to_uint64();
}
bool apbAddrSt::operator == (const apbAddrSt & rhs) const {
    bool ret = true; 
    ret = ret && (address == rhs.address);
    return ( ret );
    }
std::string apbAddrSt::prt(bool all) const
{
    return (fmt::format("address:0x{:08x}",
       (uint64_t) address
    ));
}
void apbAddrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, apbAddrSt::_byteWidth);
    _ret = address;
}
void apbAddrSt::unpack(_packedSt &_src)
{
    address = (apbAddrT)((_src));
}
sc_bv<32> apbAddrSt::sc_pack(void) const
{
    sc_bv<32> packed_data;
    packed_data.range(31, 0) = address;
    return packed_data;
}
void apbAddrSt::sc_unpack(sc_bv<32> packed_data)
{
    address = (apbAddrT) packed_data.range(31, 0).to_uint64();
}
bool apbDataSt::operator == (const apbDataSt & rhs) const {
    bool ret = true; 
    ret = ret && (data == rhs.data);
    return ( ret );
    }
std::string apbDataSt::prt(bool all) const
{
    return (fmt::format("data:0x{:08x}",
       (uint64_t) data
    ));
}
void apbDataSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, apbDataSt::_byteWidth);
    _ret = data;
}
void apbDataSt::unpack(_packedSt &_src)
{
    data = (apbDataT)((_src));
}
sc_bv<32> apbDataSt::sc_pack(void) const
{
    sc_bv<32> packed_data;
    packed_data.range(31, 0) = data;
    return packed_data;
}
void apbDataSt::sc_unpack(sc_bv<32> packed_data)
{
    data = (apbDataT) packed_data.range(31, 0).to_uint64();
}

// GENERATED_CODE_END


