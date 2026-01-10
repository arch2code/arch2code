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
    for(unsigned int i=0; i<ASIZE2; i++) {
        ret = ret && (variablea[i] == rhs.variablea[i]);
    }
    ret = ret && (variablea2 == rhs.variablea2);
    return ( ret );
    }
std::string aSt::prt(bool all) const
{
    return (std::format("variablea[0:1]: {} variablea2:0x{:01x}",
       staticArrayPrt<aSizeT, ASIZE2>(variablea, all),
       (uint64_t) variablea2
    ));
}
void aSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aSt::_byteWidth);
    _ret = variablea2;
    uint16_t _pos{2};
    for(unsigned int i=0; i<ASIZE2; i++) {
        pack_bits((uint64_t *)&_ret, _pos, variablea[i], 1);
        _pos += 1;
    }
}
void aSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    variablea2 = (twoBitT)((_src >> (_pos & 7)) & ((1ULL << 2) - 1));
    _pos += 2;
    for(unsigned int i=0; i<ASIZE2; i++) {
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
    for(unsigned int i=0; i<ASIZE2; i++) {
        packed_data.range(2+(i+1)*1-1, 2+i*1) = variablea[i];
    }
    return packed_data;
}
void aSt::sc_unpack(sc_bv<4> packed_data)
{
    variablea2 = (twoBitT) packed_data.range(1, 0).to_uint64();
    for(unsigned int i=0; i<ASIZE2; i++) {
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
    return (std::format("variablea:0x{:01x}",
       (uint64_t) variablea
    ));
}
void aASt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aASt::_byteWidth);
    _ret = variablea;
}
void aASt::unpack(const _packedSt &_src)
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
    return (std::format("a:0x{:02x}",
       (uint64_t) a
    ));
}
void aRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aRegSt::_byteWidth);
    _ret = a;
}
void aRegSt::unpack(const _packedSt &_src)
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
    return (std::format("d:0x{:02x}",
       (uint64_t) d
    ));
}
void dRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, dRegSt::_byteWidth);
    _ret = d;
}
void dRegSt::unpack(const _packedSt &_src)
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
    return (std::format("variabled:0x{:01x} variabled2:0x{:01x}",
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
void dSt::unpack(const _packedSt &_src)
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
bool bigSt::operator == (const bigSt & rhs) const {
    bool ret = true;
    ret = ret && (big == rhs.big);
    return ( ret );
    }
std::string bigSt::prt(bool all) const
{
    return (std::format("big:0x{:016x}",
       (uint64_t) big
    ));
}
void bigSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bigSt::_byteWidth);
    _ret = big;
}
void bigSt::unpack(const _packedSt &_src)
{
    big = (bigT)((_src));
}
sc_bv<64> bigSt::sc_pack(void) const
{
    sc_bv<64> packed_data;
    packed_data.range(63, 0) = big;
    return packed_data;
}
void bigSt::sc_unpack(sc_bv<64> packed_data)
{
    big = (bigT) packed_data.range(63, 0).to_uint64();
}
bool nestedSt::operator == (const nestedSt & rhs) const {
    bool ret = true;
    ret = ret && (variablea == rhs.variablea);
    ret = ret && (bob == rhs.bob);
    for(unsigned int i=0; i<2; i++) {
        ret = ret && (joe[i] == rhs.joe[i]);
    }
    return ( ret );
    }
std::string nestedSt::prt(bool all) const
{
    return (std::format("variablea:0x{:01x} bob:<{}>{}",
       (uint64_t) variablea,
       bob.prt(all),
       structArrayPrt<seeSt, 2>(joe, "joe", all)
    ));
}
void nestedSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, nestedSt::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<2; i++) {
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
void nestedSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<2; i++) {
        uint16_t _bits = 5;
        uint16_t _consume;
        {
            uint64_t _tmp{0};
            _tmp = (_src >> _pos) & ((1ULL << 5) - 1);
            joe[i].unpack(*((seeSt::_packedSt*)&_tmp));
        }
        _pos += 5;
    }
    {
        uint64_t _tmp{0};
        _tmp = (_src >> _pos) & ((1ULL << 7) - 1);
        bob.unpack(*((dSt::_packedSt*)&_tmp));
    }
    _pos += 7;
    variablea = (aSizeT)((_src >> (_pos & 31)) & 1);
}
sc_bv<18> nestedSt::sc_pack(void) const
{
    sc_bv<18> packed_data;
    for(unsigned int i=0; i<2; i++) {
        packed_data.range(0+(i+1)*5-1, 0+i*5) = joe[i].sc_pack();
    }
    packed_data.range(16, 10) = bob.sc_pack();
    packed_data.range(17, 17) = variablea;
    return packed_data;
}
void nestedSt::sc_unpack(sc_bv<18> packed_data)
{
    for(unsigned int i=0; i<2; i++) {
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
    return (std::format("index:0x{:01x}",
       (uint64_t) index
    ));
}
void bSizeRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bSizeRegSt::_byteWidth);
    _ret = index;
}
void bSizeRegSt::unpack(const _packedSt &_src)
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
    return (std::format("index:0x{:01x}",
       (uint64_t) index
    ));
}
void bSizeSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bSizeSt::_byteWidth);
    _ret = index;
}
void bSizeSt::unpack(const _packedSt &_src)
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
    return (std::format("address:0x{:08x}",
       (uint64_t) address
    ));
}
void apbAddrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, apbAddrSt::_byteWidth);
    _ret = address;
}
void apbAddrSt::unpack(const _packedSt &_src)
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
    return (std::format("data:0x{:08x}",
       (uint64_t) data
    ));
}
void apbDataSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, apbDataSt::_byteWidth);
    _ret = data;
}
void apbDataSt::unpack(const _packedSt &_src)
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
bool cSt::operator == (const cSt & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<5; i++) {
        ret = ret && (sevenBitArray[i] == rhs.sevenBitArray[i]);
    }
    return ( ret );
    }
std::string cSt::prt(bool all) const
{
    return (std::format("sevenBitArray[0:4]: {}",
       staticArrayPrt<sevenBitT, 5>(sevenBitArray, all)
    ));
}
void cSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, cSt::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        pack_bits((uint64_t *)&_ret, _pos, sevenBitArray[i], 7);
        _pos += 7;
    }
}
void cSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        uint16_t _bits = 7;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
        sevenBitArray[i] = (sevenBitT)((_src >> (_pos & 63)) & ((1ULL << 7) - 1));
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 64)) {
            sevenBitArray[i] = (sevenBitT)(sevenBitArray[i] | ((_src << _consume) & ((1ULL << 7) - 1)));
            _pos += _bits;
        }
    }
}
sc_bv<35> cSt::sc_pack(void) const
{
    sc_bv<35> packed_data;
    for(unsigned int i=0; i<5; i++) {
        packed_data.range(0+(i+1)*7-1, 0+i*7) = sevenBitArray[i];
    }
    return packed_data;
}
void cSt::sc_unpack(sc_bv<35> packed_data)
{
    for(unsigned int i=0; i<5; i++) {
        sevenBitArray[i] = (sevenBitT) packed_data.range(0+(i+1)*7-1, 0+i*7).to_uint64();
    }
}
bool test1St::operator == (const test1St & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<5; i++) {
        ret = ret && (sevenBitArray[i] == rhs.sevenBitArray[i]);
    }
    for(unsigned int i=0; i<5; i++) {
        ret = ret && (sevenBitArray2[i] == rhs.sevenBitArray2[i]);
    }
    return ( ret );
    }
std::string test1St::prt(bool all) const
{
    return (std::format("sevenBitArray[0:4]: {} sevenBitArray2[0:4]: {}",
       staticArrayPrt<sevenBitT, 5>(sevenBitArray, all),
       staticArrayPrt<sevenBitT, 5>(sevenBitArray2, all)
    ));
}
void test1St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test1St::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        pack_bits((uint64_t *)&_ret, _pos, sevenBitArray2[i], 7);
        _pos += 7;
    }
    for(unsigned int i=0; i<5; i++) {
        pack_bits((uint64_t *)&_ret, _pos, sevenBitArray[i], 7);
        _pos += 7;
    }
}
void test1St::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        uint16_t _bits = 7;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
        sevenBitArray2[i] = (sevenBitT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 7) - 1));
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 64)) {
            sevenBitArray2[i] = (sevenBitT)(sevenBitArray2[i] | ((_src[ _pos >> 6 ] << _consume) & ((1ULL << 7) - 1)));
            _pos += _bits;
        }
    }
    for(unsigned int i=0; i<5; i++) {
        uint16_t _bits = 7;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
        sevenBitArray[i] = (sevenBitT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 7) - 1));
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 64)) {
            sevenBitArray[i] = (sevenBitT)(sevenBitArray[i] | ((_src[ _pos >> 6 ] << _consume) & ((1ULL << 7) - 1)));
            _pos += _bits;
        }
    }
}
sc_bv<70> test1St::sc_pack(void) const
{
    sc_bv<70> packed_data;
    for(unsigned int i=0; i<5; i++) {
        packed_data.range(0+(i+1)*7-1, 0+i*7) = sevenBitArray2[i];
    }
    for(unsigned int i=0; i<5; i++) {
        packed_data.range(35+(i+1)*7-1, 35+i*7) = sevenBitArray[i];
    }
    return packed_data;
}
void test1St::sc_unpack(sc_bv<70> packed_data)
{
    for(unsigned int i=0; i<5; i++) {
        sevenBitArray2[i] = (sevenBitT) packed_data.range(0+(i+1)*7-1, 0+i*7).to_uint64();
    }
    for(unsigned int i=0; i<5; i++) {
        sevenBitArray[i] = (sevenBitT) packed_data.range(35+(i+1)*7-1, 35+i*7).to_uint64();
    }
}
bool test2St::operator == (const test2St & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<5; i++) {
        ret = ret && (thirtyFiveBitArray[i] == rhs.thirtyFiveBitArray[i]);
    }
    return ( ret );
    }
std::string test2St::prt(bool all) const
{
    return (std::format("{}",
       structArrayPrt<cSt, 5>(thirtyFiveBitArray, "thirtyFiveBitArray", all)
    ));
}
void test2St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test2St::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        cSt::_packedSt _tmp{0};
        thirtyFiveBitArray[i].pack(_tmp);
        pack_bits((uint64_t *)&_ret, _pos, _tmp, 35);
        _pos += 35;
    }
}
void test2St::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        uint16_t _bits = 35;
        uint16_t _consume;
        {
            cSt::_packedSt _tmp{0};
            pack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, 35);
            thirtyFiveBitArray[i].unpack(_tmp);
        }
        _pos += 35;
    }
}
sc_bv<175> test2St::sc_pack(void) const
{
    sc_bv<175> packed_data;
    for(unsigned int i=0; i<5; i++) {
        packed_data.range(0+(i+1)*35-1, 0+i*35) = thirtyFiveBitArray[i].sc_pack();
    }
    return packed_data;
}
void test2St::sc_unpack(sc_bv<175> packed_data)
{
    for(unsigned int i=0; i<5; i++) {
        thirtyFiveBitArray[i].sc_unpack(packed_data.range(0+(i+1)*35-1, 0+i*35));
    }
}
bool test3St::operator == (const test3St & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<5; i++) {
        ret = ret && (sevenBitArray[i] == rhs.sevenBitArray[i]);
    }
    return ( ret );
    }
std::string test3St::prt(bool all) const
{
    return (std::format("{}",
       structArrayPrt<aRegSt, 5>(sevenBitArray, "sevenBitArray", all)
    ));
}
void test3St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test3St::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        aRegSt::_packedSt _tmp{0};
        sevenBitArray[i].pack(_tmp);
        _ret |= (uint64_t)_tmp << (_pos & 63);
        _pos += 7;
    }
}
void test3St::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        uint16_t _bits = 7;
        uint16_t _consume;
        {
            uint64_t _tmp{0};
            _tmp = (_src >> _pos) & ((1ULL << 7) - 1);
            sevenBitArray[i].unpack(*((aRegSt::_packedSt*)&_tmp));
        }
        _pos += 7;
    }
}
sc_bv<35> test3St::sc_pack(void) const
{
    sc_bv<35> packed_data;
    for(unsigned int i=0; i<5; i++) {
        packed_data.range(0+(i+1)*7-1, 0+i*7) = sevenBitArray[i].sc_pack();
    }
    return packed_data;
}
void test3St::sc_unpack(sc_bv<35> packed_data)
{
    for(unsigned int i=0; i<5; i++) {
        sevenBitArray[i].sc_unpack(packed_data.range(0+(i+1)*7-1, 0+i*7));
    }
}
bool test4St::operator == (const test4St & rhs) const {
    bool ret = true;
    ret = ret && (sevenBitArray == rhs.sevenBitArray);
    return ( ret );
    }
std::string test4St::prt(bool all) const
{
    return (std::format("sevenBitArray:<{}>",
       sevenBitArray.prt(all)
    ));
}
void test4St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test4St::_byteWidth);
    {
        sevenBitArray.pack(*(aRegSt::_packedSt*)&_ret);
    }
}
void test4St::unpack(const _packedSt &_src)
{
    {
        sevenBitArray.unpack(*(aRegSt::_packedSt*)&_src);
    }
}
sc_bv<7> test4St::sc_pack(void) const
{
    sc_bv<7> packed_data;
    packed_data.range(6, 0) = sevenBitArray.sc_pack();
    return packed_data;
}
void test4St::sc_unpack(sc_bv<7> packed_data)
{
    sevenBitArray.sc_unpack(packed_data.range(6, 0));
}
bool test5St::operator == (const test5St & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<10; i++) {
        ret = ret && (sevenBitArray[i] == rhs.sevenBitArray[i]);
    }
    return ( ret );
    }
std::string test5St::prt(bool all) const
{
    return (std::format("{}",
       structArrayPrt<aRegSt, 10>(sevenBitArray, "sevenBitArray", all)
    ));
}
void test5St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test5St::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<10; i++) {
        aRegSt::_packedSt _tmp{0};
        sevenBitArray[i].pack(_tmp);
        pack_bits((uint64_t *)&_ret, _pos, _tmp, 7);
        _pos += 7;
    }
}
void test5St::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<10; i++) {
        uint16_t _bits = 7;
        uint16_t _consume;
        {
            uint64_t _tmp{0};
            pack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, 7);
            sevenBitArray[i].unpack(*((aRegSt::_packedSt*)&_tmp));
        }
        _pos += 7;
    }
}
sc_bv<70> test5St::sc_pack(void) const
{
    sc_bv<70> packed_data;
    for(unsigned int i=0; i<10; i++) {
        packed_data.range(0+(i+1)*7-1, 0+i*7) = sevenBitArray[i].sc_pack();
    }
    return packed_data;
}
void test5St::sc_unpack(sc_bv<70> packed_data)
{
    for(unsigned int i=0; i<10; i++) {
        sevenBitArray[i].sc_unpack(packed_data.range(0+(i+1)*7-1, 0+i*7));
    }
}
bool test6St::operator == (const test6St & rhs) const {
    bool ret = true;
    ret = ret && (largeStruct == rhs.largeStruct);
    return ( ret );
    }
std::string test6St::prt(bool all) const
{
    return (std::format("largeStruct:<{}>",
       largeStruct.prt(all)
    ));
}
void test6St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test6St::_byteWidth);
    {
        largeStruct.pack(*(test1St::_packedSt*)&_ret[ 0 ]);
    }
}
void test6St::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    {
        largeStruct.unpack(*(test1St::_packedSt*)&_src[ _pos >> 6 ]);
    }
}
sc_bv<70> test6St::sc_pack(void) const
{
    sc_bv<70> packed_data;
    packed_data.range(69, 0) = largeStruct.sc_pack();
    return packed_data;
}
void test6St::sc_unpack(sc_bv<70> packed_data)
{
    largeStruct.sc_unpack(packed_data.range(69, 0));
}
bool test7St::operator == (const test7St & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<5; i++) {
        ret = ret && (largeStruct[i] == rhs.largeStruct[i]);
    }
    return ( ret );
    }
std::string test7St::prt(bool all) const
{
    return (std::format("{}",
       structArrayPrt<test1St, 5>(largeStruct, "largeStruct", all)
    ));
}
void test7St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test7St::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        test1St::_packedSt _tmp{0};
        largeStruct[i].pack(_tmp);
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&_tmp, 70);
        _pos += 70;
    }
}
void test7St::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<5; i++) {
        uint16_t _bits = 70;
        uint16_t _consume;
        {
            test1St::_packedSt _tmp{0};
            pack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, 70);
            largeStruct[i].unpack(_tmp);
        }
        _pos += 70;
    }
}
sc_bv<350> test7St::sc_pack(void) const
{
    sc_bv<350> packed_data;
    for(unsigned int i=0; i<5; i++) {
        packed_data.range(0+(i+1)*70-1, 0+i*70) = largeStruct[i].sc_pack();
    }
    return packed_data;
}
void test7St::sc_unpack(sc_bv<350> packed_data)
{
    for(unsigned int i=0; i<5; i++) {
        largeStruct[i].sc_unpack(packed_data.range(0+(i+1)*70-1, 0+i*70));
    }
}
bool test8St::operator == (const test8St & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<3; i++) {
        ret = ret && (words[i] == rhs.words[i]);
    }
    return ( ret );
    }
std::string test8St::prt(bool all) const
{
    return (std::format("words[0:2]: {}",
       staticArrayPrt<wordT, 3>(words, all)
    ));
}
void test8St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test8St::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<3; i++) {
        pack_bits((uint64_t *)&_ret, _pos, words[i], 16);
        _pos += 16;
    }
}
void test8St::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<3; i++) {
        uint16_t _bits = 16;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
        words[i] = (wordT)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 64)) {
            words[i] = (wordT)(words[i] | ((_src << _consume) & ((1ULL << 16) - 1)));
            _pos += _bits;
        }
    }
}
sc_bv<48> test8St::sc_pack(void) const
{
    sc_bv<48> packed_data;
    for(unsigned int i=0; i<3; i++) {
        packed_data.range(0+(i+1)*16-1, 0+i*16) = words[i];
    }
    return packed_data;
}
void test8St::sc_unpack(sc_bv<48> packed_data)
{
    for(unsigned int i=0; i<3; i++) {
        words[i] = (wordT) packed_data.range(0+(i+1)*16-1, 0+i*16).to_uint64();
    }
}
bool test9St::operator == (const test9St & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<4; i++) {
        ret = ret && (wordArray[i] == rhs.wordArray[i]);
    }
    return ( ret );
    }
std::string test9St::prt(bool all) const
{
    return (std::format("{}",
       structArrayPrt<test8St, 4>(wordArray, "wordArray", all)
    ));
}
void test9St::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test9St::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<4; i++) {
        test8St::_packedSt _tmp{0};
        wordArray[i].pack(_tmp);
        pack_bits((uint64_t *)&_ret, _pos, _tmp, 48);
        _pos += 48;
    }
}
void test9St::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<4; i++) {
        uint16_t _bits = 48;
        uint16_t _consume;
        {
            test8St::_packedSt _tmp{0};
            pack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, 48);
            wordArray[i].unpack(_tmp);
        }
        _pos += 48;
    }
}
sc_bv<192> test9St::sc_pack(void) const
{
    sc_bv<192> packed_data;
    for(unsigned int i=0; i<4; i++) {
        packed_data.range(0+(i+1)*48-1, 0+i*48) = wordArray[i].sc_pack();
    }
    return packed_data;
}
void test9St::sc_unpack(sc_bv<192> packed_data)
{
    for(unsigned int i=0; i<4; i++) {
        wordArray[i].sc_unpack(packed_data.range(0+(i+1)*48-1, 0+i*48));
    }
}
bool signedTestSt::operator == (const signedTestSt & rhs) const {
    bool ret = true;
    ret = ret && (signedValue == rhs.signedValue);
    ret = ret && (unsignedValue == rhs.unsignedValue);
    return ( ret );
    }
std::string signedTestSt::prt(bool all) const
{
    return (std::format("signedValue:0x{:02x} unsignedValue:0x{:01x}",
       (uint64_t) signedValue,
       (uint64_t) unsignedValue
    ));
}
void signedTestSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, signedTestSt::_byteWidth);
    _ret = unsignedValue;
    _ret |= ((uint16_t)(signedValue & ((1ULL << 8) - 1))) << (2 & 15);
}
void signedTestSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    unsignedValue = (twoBitT)((_src >> (_pos & 15)) & ((1ULL << 2) - 1));
    _pos += 2;
    signedValue = (signedByte_t)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
    _pos += 8;
    // Sign extension for signed type
    if (signedValue & (1ULL << (8 - 1))) {
        signedValue = (signedByte_t)(signedValue | ~((1ULL << 8) - 1));
    }
}
sc_bv<10> signedTestSt::sc_pack(void) const
{
    sc_bv<10> packed_data;
    packed_data.range(1, 0) = unsignedValue;
    packed_data.range(9, 2) = signedValue;
    return packed_data;
}
void signedTestSt::sc_unpack(sc_bv<10> packed_data)
{
    unsignedValue = (twoBitT) packed_data.range(1, 0).to_uint64();
    signedValue = (signedByte_t) packed_data.range(9, 2).to_uint64();
    // Sign extension for signed type
    if (signedValue & (1ULL << (8 - 1))) {
        signedValue = (signedByte_t)(signedValue | ~((1ULL << 8) - 1));
    }
}
bool mixedSignedSt::operator == (const mixedSignedSt & rhs) const {
    bool ret = true;
    ret = ret && (temp == rhs.temp);
    ret = ret && (offset == rhs.offset);
    ret = ret && (flags == rhs.flags);
    return ( ret );
    }
std::string mixedSignedSt::prt(bool all) const
{
    return (std::format("temp:0x{:04x} offset:0x{:02x} flags:0x{:01x}",
       (uint64_t) temp,
       (uint64_t) offset,
       (uint64_t) flags
    ));
}
void mixedSignedSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, mixedSignedSt::_byteWidth);
    _ret = flags;
    _ret |= ((uint32_t)(offset & ((1ULL << 8) - 1))) << (4 & 31);
    _ret |= ((uint32_t)(temp & ((1ULL << 16) - 1))) << (12 & 31);
}
void mixedSignedSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    flags = (fourBitT)((_src >> (_pos & 31)) & ((1ULL << 4) - 1));
    _pos += 4;
    offset = (signedByte_t)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
    _pos += 8;
    // Sign extension for signed type
    if (offset & (1ULL << (8 - 1))) {
        offset = (signedByte_t)(offset | ~((1ULL << 8) - 1));
    }
    temp = (signedWord_t)((_src >> (_pos & 31)) & ((1ULL << 16) - 1));
    _pos += 16;
    // Sign extension for signed type
    if (temp & (1ULL << (16 - 1))) {
        temp = (signedWord_t)(temp | ~((1ULL << 16) - 1));
    }
}
sc_bv<28> mixedSignedSt::sc_pack(void) const
{
    sc_bv<28> packed_data;
    packed_data.range(3, 0) = flags;
    packed_data.range(11, 4) = offset;
    packed_data.range(27, 12) = temp;
    return packed_data;
}
void mixedSignedSt::sc_unpack(sc_bv<28> packed_data)
{
    flags = (fourBitT) packed_data.range(3, 0).to_uint64();
    offset = (signedByte_t) packed_data.range(11, 4).to_uint64();
    // Sign extension for signed type
    if (offset & (1ULL << (8 - 1))) {
        offset = (signedByte_t)(offset | ~((1ULL << 8) - 1));
    }
    temp = (signedWord_t) packed_data.range(27, 12).to_uint64();
    // Sign extension for signed type
    if (temp & (1ULL << (16 - 1))) {
        temp = (signedWord_t)(temp | ~((1ULL << 16) - 1));
    }
}
bool signedArraySt::operator == (const signedArraySt & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<3; i++) {
        ret = ret && (values[i] == rhs.values[i]);
    }
    return ( ret );
    }
std::string signedArraySt::prt(bool all) const
{
    return (std::format("values[0:2]: {}",
       staticArrayPrt<signedNibble_t, 3>(values, all)
    ));
}
void signedArraySt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, signedArraySt::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<3; i++) {
        pack_bits((uint64_t *)&_ret, _pos, values[i] & ((1ULL << 4) - 1), 4);
        _pos += 4;
    }
}
void signedArraySt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<3; i++) {
        uint16_t _bits = 4;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(16-(_pos & 15)));
        values[i] = (signedNibble_t)((_src >> (_pos & 15)) & ((1ULL << 4) - 1));
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 16)) {
            values[i] = (signedNibble_t)(values[i] | ((_src << _consume) & ((1ULL << 4) - 1)));
            _pos += _bits;
        }
        // Sign extension for signed type
        if (values[i] & (1ULL << (4 - 1))) {
            values[i] = (signedNibble_t)(values[i] | ~((1ULL << 4) - 1));
        }
    }
}
sc_bv<12> signedArraySt::sc_pack(void) const
{
    sc_bv<12> packed_data;
    for(unsigned int i=0; i<3; i++) {
        packed_data.range(0+(i+1)*4-1, 0+i*4) = values[i];
    }
    return packed_data;
}
void signedArraySt::sc_unpack(sc_bv<12> packed_data)
{
    for(unsigned int i=0; i<3; i++) {
        values[i] = (signedNibble_t) packed_data.range(0+(i+1)*4-1, 0+i*4).to_uint64();
        // Sign extension for signed type
        if (values[i] & (1ULL << (4 - 1))) {
            values[i] = (signedNibble_t)(values[i] | ~((1ULL << 4) - 1));
        }
    }
}
bool nonByteAlignedSignedSt::operator == (const nonByteAlignedSignedSt & rhs) const {
    bool ret = true;
    ret = ret && (field1 == rhs.field1);
    ret = ret && (field2 == rhs.field2);
    ret = ret && (field3 == rhs.field3);
    ret = ret && (field4 == rhs.field4);
    return ( ret );
    }
std::string nonByteAlignedSignedSt::prt(bool all) const
{
    return (std::format("field1:0x{:01x} field2:0x{:02x} field3:0x{:02x} field4:0x{:01x}",
       (uint64_t) field1,
       (uint64_t) field2,
       (uint64_t) field3,
       (uint64_t) field4
    ));
}
void nonByteAlignedSignedSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, nonByteAlignedSignedSt::_byteWidth);
    _ret = field4;
    _ret |= ((uint16_t)(field3 & ((1ULL << 5) - 1))) << (3 & 15);
    _ret |= (uint16_t)field2 << (8 & 15);
    _ret |= ((uint16_t)(field1 & ((1ULL << 3) - 1))) << (13 & 15);
}
void nonByteAlignedSignedSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    field4 = (threeBitT)((_src >> (_pos & 15)) & ((1ULL << 3) - 1));
    _pos += 3;
    field3 = (signed5bit_t)((_src >> (_pos & 15)) & ((1ULL << 5) - 1));
    _pos += 5;
    // Sign extension for signed type
    if (field3 & (1ULL << (5 - 1))) {
        field3 = (signed5bit_t)(field3 | ~((1ULL << 5) - 1));
    }
    field2 = (unsigned5bit_t)((_src >> (_pos & 15)) & ((1ULL << 5) - 1));
    _pos += 5;
    field1 = (signed3bit_t)((_src >> (_pos & 15)) & ((1ULL << 3) - 1));
    _pos += 3;
    // Sign extension for signed type
    if (field1 & (1ULL << (3 - 1))) {
        field1 = (signed3bit_t)(field1 | ~((1ULL << 3) - 1));
    }
}
sc_bv<16> nonByteAlignedSignedSt::sc_pack(void) const
{
    sc_bv<16> packed_data;
    packed_data.range(2, 0) = field4;
    packed_data.range(7, 3) = field3;
    packed_data.range(12, 8) = field2;
    packed_data.range(15, 13) = field1;
    return packed_data;
}
void nonByteAlignedSignedSt::sc_unpack(sc_bv<16> packed_data)
{
    field4 = (threeBitT) packed_data.range(2, 0).to_uint64();
    field3 = (signed5bit_t) packed_data.range(7, 3).to_uint64();
    // Sign extension for signed type
    if (field3 & (1ULL << (5 - 1))) {
        field3 = (signed5bit_t)(field3 | ~((1ULL << 5) - 1));
    }
    field2 = (unsigned5bit_t) packed_data.range(12, 8).to_uint64();
    field1 = (signed3bit_t) packed_data.range(15, 13).to_uint64();
    // Sign extension for signed type
    if (field1 & (1ULL << (3 - 1))) {
        field1 = (signed3bit_t)(field1 | ~((1ULL << 3) - 1));
    }
}
bool complexMixedSt::operator == (const complexMixedSt & rhs) const {
    bool ret = true;
    ret = ret && (signedA == rhs.signedA);
    ret = ret && (unsignedB == rhs.unsignedB);
    ret = ret && (signedC == rhs.signedC);
    ret = ret && (unsignedD == rhs.unsignedD);
    ret = ret && (signedE == rhs.signedE);
    return ( ret );
    }
std::string complexMixedSt::prt(bool all) const
{
    return (std::format("signedA:0x{:02x} unsignedB:0x{:03x} signedC:0x{:03x} unsignedD:0x{:01x} signedE:0x{:02x}",
       (uint64_t) signedA,
       (uint64_t) unsignedB,
       (uint64_t) signedC,
       (uint64_t) unsignedD,
       (uint64_t) signedE
    ));
}
void complexMixedSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, complexMixedSt::_byteWidth);
    _ret = signedE & ((1ULL << 8) - 1);
    _ret |= (uint64_t)unsignedD << (8 & 63);
    _ret |= ((uint64_t)(signedC & ((1ULL << 11) - 1))) << (12 & 63);
    _ret |= (uint64_t)unsignedB << (23 & 63);
    _ret |= ((uint64_t)(signedA & ((1ULL << 7) - 1))) << (32 & 63);
}
void complexMixedSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    signedE = (signedByte_t)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
    _pos += 8;
    // Sign extension for signed type
    if (signedE & (1ULL << (8 - 1))) {
        signedE = (signedByte_t)(signedE | ~((1ULL << 8) - 1));
    }
    unsignedD = (fourBitT)((_src >> (_pos & 63)) & ((1ULL << 4) - 1));
    _pos += 4;
    signedC = (signed11bit_t)((_src >> (_pos & 63)) & ((1ULL << 11) - 1));
    _pos += 11;
    // Sign extension for signed type
    if (signedC & (1ULL << (11 - 1))) {
        signedC = (signed11bit_t)(signedC | ~((1ULL << 11) - 1));
    }
    unsignedB = (unsigned9bit_t)((_src >> (_pos & 63)) & ((1ULL << 9) - 1));
    _pos += 9;
    signedA = (signed7bit_t)((_src >> (_pos & 63)) & ((1ULL << 7) - 1));
    _pos += 7;
    // Sign extension for signed type
    if (signedA & (1ULL << (7 - 1))) {
        signedA = (signed7bit_t)(signedA | ~((1ULL << 7) - 1));
    }
}
sc_bv<39> complexMixedSt::sc_pack(void) const
{
    sc_bv<39> packed_data;
    packed_data.range(7, 0) = signedE;
    packed_data.range(11, 8) = unsignedD;
    packed_data.range(22, 12) = signedC;
    packed_data.range(31, 23) = unsignedB;
    packed_data.range(38, 32) = signedA;
    return packed_data;
}
void complexMixedSt::sc_unpack(sc_bv<39> packed_data)
{
    signedE = (signedByte_t) packed_data.range(7, 0).to_uint64();
    // Sign extension for signed type
    if (signedE & (1ULL << (8 - 1))) {
        signedE = (signedByte_t)(signedE | ~((1ULL << 8) - 1));
    }
    unsignedD = (fourBitT) packed_data.range(11, 8).to_uint64();
    signedC = (signed11bit_t) packed_data.range(22, 12).to_uint64();
    // Sign extension for signed type
    if (signedC & (1ULL << (11 - 1))) {
        signedC = (signed11bit_t)(signedC | ~((1ULL << 11) - 1));
    }
    unsignedB = (unsigned9bit_t) packed_data.range(31, 23).to_uint64();
    signedA = (signed7bit_t) packed_data.range(38, 32).to_uint64();
    // Sign extension for signed type
    if (signedA & (1ULL << (7 - 1))) {
        signedA = (signed7bit_t)(signedA | ~((1ULL << 7) - 1));
    }
}
bool edgeCaseSignedSt::operator == (const edgeCaseSignedSt & rhs) const {
    bool ret = true;
    ret = ret && (tiny == rhs.tiny);
    ret = ret && (smallVal == rhs.smallVal);
    ret = ret && (mediumVal == rhs.mediumVal);
    ret = ret && (largeVal == rhs.largeVal);
    return ( ret );
    }
std::string edgeCaseSignedSt::prt(bool all) const
{
    return (std::format("tiny:0x{:01x} smallVal:0x{:01x} mediumVal:0x{:03x} largeVal:0x{:04x}",
       (uint64_t) tiny,
       (uint64_t) smallVal,
       (uint64_t) mediumVal,
       (uint64_t) largeVal
    ));
}
void edgeCaseSignedSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, edgeCaseSignedSt::_byteWidth);
    _ret = largeVal & ((1ULL << 16) - 1);
    _ret |= ((uint64_t)(mediumVal & ((1ULL << 11) - 1))) << (16 & 63);
    _ret |= ((uint64_t)(smallVal & ((1ULL << 4) - 1))) << (27 & 63);
    _ret |= ((uint64_t)(tiny & ((1ULL << 3) - 1))) << (31 & 63);
}
void edgeCaseSignedSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    largeVal = (signedWord_t)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
    _pos += 16;
    // Sign extension for signed type
    if (largeVal & (1ULL << (16 - 1))) {
        largeVal = (signedWord_t)(largeVal | ~((1ULL << 16) - 1));
    }
    mediumVal = (signed11bit_t)((_src >> (_pos & 63)) & ((1ULL << 11) - 1));
    _pos += 11;
    // Sign extension for signed type
    if (mediumVal & (1ULL << (11 - 1))) {
        mediumVal = (signed11bit_t)(mediumVal | ~((1ULL << 11) - 1));
    }
    smallVal = (signedNibble_t)((_src >> (_pos & 63)) & ((1ULL << 4) - 1));
    _pos += 4;
    // Sign extension for signed type
    if (smallVal & (1ULL << (4 - 1))) {
        smallVal = (signedNibble_t)(smallVal | ~((1ULL << 4) - 1));
    }
    tiny = (signed3bit_t)((_src >> (_pos & 63)) & ((1ULL << 3) - 1));
    _pos += 3;
    // Sign extension for signed type
    if (tiny & (1ULL << (3 - 1))) {
        tiny = (signed3bit_t)(tiny | ~((1ULL << 3) - 1));
    }
}
sc_bv<34> edgeCaseSignedSt::sc_pack(void) const
{
    sc_bv<34> packed_data;
    packed_data.range(15, 0) = largeVal;
    packed_data.range(26, 16) = mediumVal;
    packed_data.range(30, 27) = smallVal;
    packed_data.range(33, 31) = tiny;
    return packed_data;
}
void edgeCaseSignedSt::sc_unpack(sc_bv<34> packed_data)
{
    largeVal = (signedWord_t) packed_data.range(15, 0).to_uint64();
    // Sign extension for signed type
    if (largeVal & (1ULL << (16 - 1))) {
        largeVal = (signedWord_t)(largeVal | ~((1ULL << 16) - 1));
    }
    mediumVal = (signed11bit_t) packed_data.range(26, 16).to_uint64();
    // Sign extension for signed type
    if (mediumVal & (1ULL << (11 - 1))) {
        mediumVal = (signed11bit_t)(mediumVal | ~((1ULL << 11) - 1));
    }
    smallVal = (signedNibble_t) packed_data.range(30, 27).to_uint64();
    // Sign extension for signed type
    if (smallVal & (1ULL << (4 - 1))) {
        smallVal = (signedNibble_t)(smallVal | ~((1ULL << 4) - 1));
    }
    tiny = (signed3bit_t) packed_data.range(33, 31).to_uint64();
    // Sign extension for signed type
    if (tiny & (1ULL << (3 - 1))) {
        tiny = (signed3bit_t)(tiny | ~((1ULL << 3) - 1));
    }
}
bool mixedArraySignedSt::operator == (const mixedArraySignedSt & rhs) const {
    bool ret = true;
    for(unsigned int i=0; i<4; i++) {
        ret = ret && (signedVals[i] == rhs.signedVals[i]);
    }
    for(unsigned int i=0; i<3; i++) {
        ret = ret && (unsignedVals[i] == rhs.unsignedVals[i]);
    }
    return ( ret );
    }
std::string mixedArraySignedSt::prt(bool all) const
{
    return (std::format("signedVals[0:3]: {} unsignedVals[0:2]: {}",
       staticArrayPrt<signed5bit_t, 4>(signedVals, all),
       staticArrayPrt<unsigned5bit_t, 3>(unsignedVals, all)
    ));
}
void mixedArraySignedSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, mixedArraySignedSt::_byteWidth);
    uint16_t _pos{0};
    for(unsigned int i=0; i<3; i++) {
        pack_bits((uint64_t *)&_ret, _pos, unsignedVals[i], 5);
        _pos += 5;
    }
    for(unsigned int i=0; i<4; i++) {
        pack_bits((uint64_t *)&_ret, _pos, signedVals[i] & ((1ULL << 5) - 1), 5);
        _pos += 5;
    }
}
void mixedArraySignedSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    for(unsigned int i=0; i<3; i++) {
        uint16_t _bits = 5;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
        unsignedVals[i] = (unsigned5bit_t)((_src >> (_pos & 63)) & ((1ULL << 5) - 1));
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 64)) {
            unsignedVals[i] = (unsigned5bit_t)(unsignedVals[i] | ((_src << _consume) & ((1ULL << 5) - 1)));
            _pos += _bits;
        }
    }
    for(unsigned int i=0; i<4; i++) {
        uint16_t _bits = 5;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
        signedVals[i] = (signed5bit_t)((_src >> (_pos & 63)) & ((1ULL << 5) - 1));
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 64)) {
            signedVals[i] = (signed5bit_t)(signedVals[i] | ((_src << _consume) & ((1ULL << 5) - 1)));
            _pos += _bits;
        }
        // Sign extension for signed type
        if (signedVals[i] & (1ULL << (5 - 1))) {
            signedVals[i] = (signed5bit_t)(signedVals[i] | ~((1ULL << 5) - 1));
        }
    }
}
sc_bv<35> mixedArraySignedSt::sc_pack(void) const
{
    sc_bv<35> packed_data;
    for(unsigned int i=0; i<3; i++) {
        packed_data.range(0+(i+1)*5-1, 0+i*5) = unsignedVals[i];
    }
    for(unsigned int i=0; i<4; i++) {
        packed_data.range(15+(i+1)*5-1, 15+i*5) = signedVals[i];
    }
    return packed_data;
}
void mixedArraySignedSt::sc_unpack(sc_bv<35> packed_data)
{
    for(unsigned int i=0; i<3; i++) {
        unsignedVals[i] = (unsigned5bit_t) packed_data.range(0+(i+1)*5-1, 0+i*5).to_uint64();
    }
    for(unsigned int i=0; i<4; i++) {
        signedVals[i] = (signed5bit_t) packed_data.range(15+(i+1)*5-1, 15+i*5).to_uint64();
        // Sign extension for signed type
        if (signedVals[i] & (1ULL << (5 - 1))) {
            signedVals[i] = (signed5bit_t)(signedVals[i] | ~((1ULL << 5) - 1));
        }
    }
}
bool test37BitRegSt::operator == (const test37BitRegSt & rhs) const {
    bool ret = true;
    ret = ret && (value37 == rhs.value37);
    return ( ret );
    }
std::string test37BitRegSt::prt(bool all) const
{
    return (std::format("value37:0x{:010x}",
       (uint64_t) value37
    ));
}
void test37BitRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test37BitRegSt::_byteWidth);
    _ret = value37;
}
void test37BitRegSt::unpack(const _packedSt &_src)
{
    value37 = (test37BitT)((_src) & ((1ULL << 37) - 1));
}
sc_bv<37> test37BitRegSt::sc_pack(void) const
{
    sc_bv<37> packed_data;
    packed_data.range(36, 0) = value37;
    return packed_data;
}
void test37BitRegSt::sc_unpack(sc_bv<37> packed_data)
{
    value37 = (test37BitT) packed_data.range(36, 0).to_uint64();
}

// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
#include "q_assert.h"
std::string test_mixed_structs::name(void) { return "test_mixed_structs"; }
void test_mixed_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        aSt::_packedSt packed;
        memset(&packed, pattern, aSt::_byteWidth);
        sc_bv<aSt::_bitWidth> aInit;
        sc_bv<aSt::_bitWidth> aTest;
        for (int i = 0; i < aSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, aSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        aSt a;
        a.sc_unpack(aInit);
        aSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"aSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"aSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = aSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"aSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        aASt::_packedSt packed;
        memset(&packed, pattern, aASt::_byteWidth);
        sc_bv<aASt::_bitWidth> aInit;
        sc_bv<aASt::_bitWidth> aTest;
        for (int i = 0; i < aASt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, aASt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        aASt a;
        a.sc_unpack(aInit);
        aASt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"aASt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"aASt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = aASt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"aASt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        aRegSt::_packedSt packed;
        memset(&packed, pattern, aRegSt::_byteWidth);
        sc_bv<aRegSt::_bitWidth> aInit;
        sc_bv<aRegSt::_bitWidth> aTest;
        for (int i = 0; i < aRegSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, aRegSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        aRegSt a;
        a.sc_unpack(aInit);
        aRegSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"aRegSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"aRegSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = aRegSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"aRegSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        dRegSt::_packedSt packed;
        memset(&packed, pattern, dRegSt::_byteWidth);
        sc_bv<dRegSt::_bitWidth> aInit;
        sc_bv<dRegSt::_bitWidth> aTest;
        for (int i = 0; i < dRegSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, dRegSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        dRegSt a;
        a.sc_unpack(aInit);
        dRegSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"dRegSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"dRegSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = dRegSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"dRegSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        dSt::_packedSt packed;
        memset(&packed, pattern, dSt::_byteWidth);
        sc_bv<dSt::_bitWidth> aInit;
        sc_bv<dSt::_bitWidth> aTest;
        for (int i = 0; i < dSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, dSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        dSt a;
        a.sc_unpack(aInit);
        dSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"dSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"dSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = dSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"dSt fail");
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
        nestedSt::_packedSt packed;
        memset(&packed, pattern, nestedSt::_byteWidth);
        sc_bv<nestedSt::_bitWidth> aInit;
        sc_bv<nestedSt::_bitWidth> aTest;
        for (int i = 0; i < nestedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, nestedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        nestedSt a;
        a.sc_unpack(aInit);
        nestedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"nestedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"nestedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = nestedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"nestedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        bSizeRegSt::_packedSt packed;
        memset(&packed, pattern, bSizeRegSt::_byteWidth);
        sc_bv<bSizeRegSt::_bitWidth> aInit;
        sc_bv<bSizeRegSt::_bitWidth> aTest;
        for (int i = 0; i < bSizeRegSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, bSizeRegSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        bSizeRegSt a;
        a.sc_unpack(aInit);
        bSizeRegSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"bSizeRegSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"bSizeRegSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = bSizeRegSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"bSizeRegSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        bSizeSt::_packedSt packed;
        memset(&packed, pattern, bSizeSt::_byteWidth);
        sc_bv<bSizeSt::_bitWidth> aInit;
        sc_bv<bSizeSt::_bitWidth> aTest;
        for (int i = 0; i < bSizeSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, bSizeSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        bSizeSt a;
        a.sc_unpack(aInit);
        bSizeSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"bSizeSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"bSizeSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = bSizeSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"bSizeSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        apbAddrSt::_packedSt packed;
        memset(&packed, pattern, apbAddrSt::_byteWidth);
        sc_bv<apbAddrSt::_bitWidth> aInit;
        sc_bv<apbAddrSt::_bitWidth> aTest;
        for (int i = 0; i < apbAddrSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, apbAddrSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        apbAddrSt a;
        a.sc_unpack(aInit);
        apbAddrSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"apbAddrSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"apbAddrSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = apbAddrSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"apbAddrSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        apbDataSt::_packedSt packed;
        memset(&packed, pattern, apbDataSt::_byteWidth);
        sc_bv<apbDataSt::_bitWidth> aInit;
        sc_bv<apbDataSt::_bitWidth> aTest;
        for (int i = 0; i < apbDataSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, apbDataSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        apbDataSt a;
        a.sc_unpack(aInit);
        apbDataSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"apbDataSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"apbDataSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = apbDataSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"apbDataSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        cSt::_packedSt packed;
        memset(&packed, pattern, cSt::_byteWidth);
        sc_bv<cSt::_bitWidth> aInit;
        sc_bv<cSt::_bitWidth> aTest;
        for (int i = 0; i < cSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, cSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        cSt a;
        a.sc_unpack(aInit);
        cSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"cSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"cSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = cSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"cSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test1St::_packedSt packed;
        memset(&packed, pattern, test1St::_byteWidth);
        sc_bv<test1St::_bitWidth> aInit;
        sc_bv<test1St::_bitWidth> aTest;
        for (int i = 0; i < test1St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test1St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test1St a;
        a.sc_unpack(aInit);
        test1St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test1St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test1St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test1St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test1St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test2St::_packedSt packed;
        memset(&packed, pattern, test2St::_byteWidth);
        sc_bv<test2St::_bitWidth> aInit;
        sc_bv<test2St::_bitWidth> aTest;
        for (int i = 0; i < test2St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test2St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test2St a;
        a.sc_unpack(aInit);
        test2St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test2St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test2St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test2St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test2St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test3St::_packedSt packed;
        memset(&packed, pattern, test3St::_byteWidth);
        sc_bv<test3St::_bitWidth> aInit;
        sc_bv<test3St::_bitWidth> aTest;
        for (int i = 0; i < test3St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test3St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test3St a;
        a.sc_unpack(aInit);
        test3St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test3St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test3St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test3St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test3St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test4St::_packedSt packed;
        memset(&packed, pattern, test4St::_byteWidth);
        sc_bv<test4St::_bitWidth> aInit;
        sc_bv<test4St::_bitWidth> aTest;
        for (int i = 0; i < test4St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test4St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test4St a;
        a.sc_unpack(aInit);
        test4St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test4St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test4St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test4St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test4St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test5St::_packedSt packed;
        memset(&packed, pattern, test5St::_byteWidth);
        sc_bv<test5St::_bitWidth> aInit;
        sc_bv<test5St::_bitWidth> aTest;
        for (int i = 0; i < test5St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test5St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test5St a;
        a.sc_unpack(aInit);
        test5St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test5St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test5St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test5St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test5St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test6St::_packedSt packed;
        memset(&packed, pattern, test6St::_byteWidth);
        sc_bv<test6St::_bitWidth> aInit;
        sc_bv<test6St::_bitWidth> aTest;
        for (int i = 0; i < test6St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test6St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test6St a;
        a.sc_unpack(aInit);
        test6St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test6St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test6St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test6St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test6St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test7St::_packedSt packed;
        memset(&packed, pattern, test7St::_byteWidth);
        sc_bv<test7St::_bitWidth> aInit;
        sc_bv<test7St::_bitWidth> aTest;
        for (int i = 0; i < test7St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test7St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test7St a;
        a.sc_unpack(aInit);
        test7St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test7St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test7St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test7St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test7St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test8St::_packedSt packed;
        memset(&packed, pattern, test8St::_byteWidth);
        sc_bv<test8St::_bitWidth> aInit;
        sc_bv<test8St::_bitWidth> aTest;
        for (int i = 0; i < test8St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test8St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test8St a;
        a.sc_unpack(aInit);
        test8St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test8St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test8St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test8St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test8St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test9St::_packedSt packed;
        memset(&packed, pattern, test9St::_byteWidth);
        sc_bv<test9St::_bitWidth> aInit;
        sc_bv<test9St::_bitWidth> aTest;
        for (int i = 0; i < test9St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test9St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test9St a;
        a.sc_unpack(aInit);
        test9St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test9St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test9St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test9St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test9St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        signedTestSt::_packedSt packed;
        memset(&packed, pattern, signedTestSt::_byteWidth);
        sc_bv<signedTestSt::_bitWidth> aInit;
        sc_bv<signedTestSt::_bitWidth> aTest;
        for (int i = 0; i < signedTestSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, signedTestSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        signedTestSt a;
        a.sc_unpack(aInit);
        signedTestSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"signedTestSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"signedTestSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = signedTestSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"signedTestSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        mixedSignedSt::_packedSt packed;
        memset(&packed, pattern, mixedSignedSt::_byteWidth);
        sc_bv<mixedSignedSt::_bitWidth> aInit;
        sc_bv<mixedSignedSt::_bitWidth> aTest;
        for (int i = 0; i < mixedSignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, mixedSignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        mixedSignedSt a;
        a.sc_unpack(aInit);
        mixedSignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"mixedSignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"mixedSignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = mixedSignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"mixedSignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        signedArraySt::_packedSt packed;
        memset(&packed, pattern, signedArraySt::_byteWidth);
        sc_bv<signedArraySt::_bitWidth> aInit;
        sc_bv<signedArraySt::_bitWidth> aTest;
        for (int i = 0; i < signedArraySt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, signedArraySt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        signedArraySt a;
        a.sc_unpack(aInit);
        signedArraySt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"signedArraySt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"signedArraySt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = signedArraySt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"signedArraySt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        nonByteAlignedSignedSt::_packedSt packed;
        memset(&packed, pattern, nonByteAlignedSignedSt::_byteWidth);
        sc_bv<nonByteAlignedSignedSt::_bitWidth> aInit;
        sc_bv<nonByteAlignedSignedSt::_bitWidth> aTest;
        for (int i = 0; i < nonByteAlignedSignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, nonByteAlignedSignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        nonByteAlignedSignedSt a;
        a.sc_unpack(aInit);
        nonByteAlignedSignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"nonByteAlignedSignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"nonByteAlignedSignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = nonByteAlignedSignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"nonByteAlignedSignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        complexMixedSt::_packedSt packed;
        memset(&packed, pattern, complexMixedSt::_byteWidth);
        sc_bv<complexMixedSt::_bitWidth> aInit;
        sc_bv<complexMixedSt::_bitWidth> aTest;
        for (int i = 0; i < complexMixedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, complexMixedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        complexMixedSt a;
        a.sc_unpack(aInit);
        complexMixedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"complexMixedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"complexMixedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = complexMixedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"complexMixedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        edgeCaseSignedSt::_packedSt packed;
        memset(&packed, pattern, edgeCaseSignedSt::_byteWidth);
        sc_bv<edgeCaseSignedSt::_bitWidth> aInit;
        sc_bv<edgeCaseSignedSt::_bitWidth> aTest;
        for (int i = 0; i < edgeCaseSignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, edgeCaseSignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        edgeCaseSignedSt a;
        a.sc_unpack(aInit);
        edgeCaseSignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"edgeCaseSignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"edgeCaseSignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = edgeCaseSignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"edgeCaseSignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        mixedArraySignedSt::_packedSt packed;
        memset(&packed, pattern, mixedArraySignedSt::_byteWidth);
        sc_bv<mixedArraySignedSt::_bitWidth> aInit;
        sc_bv<mixedArraySignedSt::_bitWidth> aTest;
        for (int i = 0; i < mixedArraySignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, mixedArraySignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        mixedArraySignedSt a;
        a.sc_unpack(aInit);
        mixedArraySignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"mixedArraySignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"mixedArraySignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = mixedArraySignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"mixedArraySignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test37BitRegSt::_packedSt packed;
        memset(&packed, pattern, test37BitRegSt::_byteWidth);
        sc_bv<test37BitRegSt::_bitWidth> aInit;
        sc_bv<test37BitRegSt::_bitWidth> aTest;
        for (int i = 0; i < test37BitRegSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test37BitRegSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test37BitRegSt a;
        a.sc_unpack(aInit);
        test37BitRegSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test37BitRegSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test37BitRegSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test37BitRegSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test37BitRegSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}

// GENERATED_CODE_END
