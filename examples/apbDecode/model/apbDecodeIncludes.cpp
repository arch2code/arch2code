// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "apbDecodeIncludes.h"

// GENERATED_CODE_PARAM --context=apbDecode.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool aRegSt::operator == (const aRegSt & rhs) const {
    bool ret = true; 
    ret = ret && (a == rhs.a);
    return ( ret );
    }
std::string aRegSt::prt(bool all) const
{
    return (fmt::format("a:0x{:010x}",
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
    a = (thirtySevenBitT)((_src) & ((1ULL << 37) - 1));
}
sc_bv<37> aRegSt::sc_pack(void) const
{
    sc_bv<37> packed_data;
    packed_data.range(36, 0) = a;
    return packed_data;
}
void aRegSt::sc_unpack(sc_bv<37> packed_data)
{
    a = (thirtySevenBitT) packed_data.range(36, 0).to_uint64();
}
bool un0BRegSt::operator == (const un0BRegSt & rhs) const {
    bool ret = true; 
    ret = ret && (fa == rhs.fa);
    ret = ret && (fb == rhs.fb);
    return ( ret );
    }
std::string un0BRegSt::prt(bool all) const
{
    return (fmt::format("fa:0x{:02x} fb:0x{:04x}",
       (uint64_t) fa,
       (uint64_t) fb
    ));
}
void un0BRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, un0BRegSt::_byteWidth);
    _ret = fb;
    _ret |= (uint32_t)fa << (16 & 31);
}
void un0BRegSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    fb = (u16T)((_src >> (_pos & 31)) & ((1ULL << 16) - 1));
    _pos += 16;
    fa = (u8T)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
}
sc_bv<24> un0BRegSt::sc_pack(void) const
{
    sc_bv<24> packed_data;
    packed_data.range(15, 0) = fb;
    packed_data.range(23, 16) = fa;
    return packed_data;
}
void un0BRegSt::sc_unpack(sc_bv<24> packed_data)
{
    fb = (u16T) packed_data.range(15, 0).to_uint64();
    fa = (u8T) packed_data.range(23, 16).to_uint64();
}
bool un0ARegSt::operator == (const un0ARegSt & rhs) const {
    bool ret = true; 
    ret = ret && (fa == rhs.fa);
    ret = ret && (fb == rhs.fb);
    ret = ret && (fc == rhs.fc);
    return ( ret );
    }
std::string un0ARegSt::prt(bool all) const
{
    return (fmt::format("fa:0x{:02x} fb:0x{:08x} fc:0x{:02x}",
       (uint64_t) fa,
       (uint64_t) fb,
       (uint64_t) fc
    ));
}
void un0ARegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, un0ARegSt::_byteWidth);
    _ret = fc;
    _ret |= (uint64_t)fb << (8 & 63);
    _ret |= (uint64_t)fa << (40 & 63);
}
void un0ARegSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    fc = (u8T)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
    _pos += 8;
    fb = (u32T)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
    _pos += 32;
    fa = (u8T)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
}
sc_bv<48> un0ARegSt::sc_pack(void) const
{
    sc_bv<48> packed_data;
    packed_data.range(7, 0) = fc;
    packed_data.range(39, 8) = fb;
    packed_data.range(47, 40) = fa;
    return packed_data;
}
void un0ARegSt::sc_unpack(sc_bv<48> packed_data)
{
    fc = (u8T) packed_data.range(7, 0).to_uint64();
    fb = (u32T) packed_data.range(39, 8).to_uint64();
    fa = (u8T) packed_data.range(47, 40).to_uint64();
}
bool aSizeRegSt::operator == (const aSizeRegSt & rhs) const {
    bool ret = true; 
    ret = ret && (index == rhs.index);
    return ( ret );
    }
std::string aSizeRegSt::prt(bool all) const
{
    return (fmt::format("index:0x{:08x}",
       (uint64_t) index
    ));
}
void aSizeRegSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aSizeRegSt::_byteWidth);
    _ret = index;
}
void aSizeRegSt::unpack(_packedSt &_src)
{
    index = (aSizeT)((_src) & ((1ULL << 29) - 1));
}
sc_bv<29> aSizeRegSt::sc_pack(void) const
{
    sc_bv<29> packed_data;
    packed_data.range(28, 0) = index;
    return packed_data;
}
void aSizeRegSt::sc_unpack(sc_bv<29> packed_data)
{
    index = (aSizeT) packed_data.range(28, 0).to_uint64();
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
bool aMemAddrSt::operator == (const aMemAddrSt & rhs) const {
    bool ret = true; 
    ret = ret && (address == rhs.address);
    return ( ret );
    }
std::string aMemAddrSt::prt(bool all) const
{
    return (fmt::format("address:0x{:02x}",
       (uint64_t) address
    ));
}
void aMemAddrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aMemAddrSt::_byteWidth);
    _ret = address;
}
void aMemAddrSt::unpack(_packedSt &_src)
{
    address = (aAddrBitsT)((_src) & ((1ULL << 5) - 1));
}
sc_bv<5> aMemAddrSt::sc_pack(void) const
{
    sc_bv<5> packed_data;
    packed_data.range(4, 0) = address;
    return packed_data;
}
void aMemAddrSt::sc_unpack(sc_bv<5> packed_data)
{
    address = (aAddrBitsT) packed_data.range(4, 0).to_uint64();
}
bool aMemSt::operator == (const aMemSt & rhs) const {
    bool ret = true; 
    ret = ret && (data == rhs.data);
    return ( ret );
    }
std::string aMemSt::prt(bool all) const
{
    return (fmt::format("data:0x{:016x}",
       (uint64_t) data
    ));
}
void aMemSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, aMemSt::_byteWidth);
    _ret = data;
}
void aMemSt::unpack(_packedSt &_src)
{
    data = (aDataBitsT)((_src) & ((1ULL << 63) - 1));
}
sc_bv<63> aMemSt::sc_pack(void) const
{
    sc_bv<63> packed_data;
    packed_data.range(62, 0) = data;
    return packed_data;
}
void aMemSt::sc_unpack(sc_bv<63> packed_data)
{
    data = (aDataBitsT) packed_data.range(62, 0).to_uint64();
}
bool bMemAddrSt::operator == (const bMemAddrSt & rhs) const {
    bool ret = true; 
    ret = ret && (address == rhs.address);
    return ( ret );
    }
std::string bMemAddrSt::prt(bool all) const
{
    return (fmt::format("address:0x{:02x}",
       (uint64_t) address
    ));
}
void bMemAddrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bMemAddrSt::_byteWidth);
    _ret = address;
}
void bMemAddrSt::unpack(_packedSt &_src)
{
    address = (bAddrBitsT)((_src) & ((1ULL << 5) - 1));
}
sc_bv<5> bMemAddrSt::sc_pack(void) const
{
    sc_bv<5> packed_data;
    packed_data.range(4, 0) = address;
    return packed_data;
}
void bMemAddrSt::sc_unpack(sc_bv<5> packed_data)
{
    address = (bAddrBitsT) packed_data.range(4, 0).to_uint64();
}
bool bMemSt::operator == (const bMemSt & rhs) const {
    bool ret = true; 
    for(int i=0; i<3; i++) {
        ret = ret && (data[i] == rhs.data[i]);
    }
    return ( ret );
    }
std::string bMemSt::prt(bool all) const
{
    return (fmt::format("data[0:2]: {}",
       staticArrayPrt<u32T, 3>(data, all)
    ));
}
void bMemSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bMemSt::_byteWidth);
    uint16_t _pos{0};
    for(int i=0; i<3; i++) {
        pack_bits((uint64_t *)&_ret, _pos, data[i], 32);
        _pos += 32;
    }
}
void bMemSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    for(int i=0; i<3; i++) {
        uint16_t _bits = 32;
        uint16_t _consume;
        _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
        data[i] = (u32T)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += _consume;
        _bits -= _consume;
        if ((_bits > 0) && (_consume != 64)) {
            data[i] = (u32T)(data[i] | ((_src[ _pos >> 6 ] << _consume) & ((1ULL << 32) - 1)));
            _pos += _bits;
        }
    }
}
sc_bv<96> bMemSt::sc_pack(void) const
{
    sc_bv<96> packed_data;
    for(int i=0; i<3; i++) {
        packed_data.range(0+(i+1)*32-1, 0+i*32) = data[i];
    }
    return packed_data;
}
void bMemSt::sc_unpack(sc_bv<96> packed_data)
{
    for(int i=0; i<3; i++) {
        data[i] = (u32T) packed_data.range(0+(i+1)*32-1, 0+i*32).to_uint64();
    }
}

// GENERATED_CODE_END


