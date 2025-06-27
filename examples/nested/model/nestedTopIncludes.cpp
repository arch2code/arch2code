// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "nestedTopIncludes.h"

// GENERATED_CODE_PARAM --context=nestedTop.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool test_st::operator == (const test_st & rhs) const {
    bool ret = true; 
    ret = ret && (a == rhs.a);
    return ( ret );
    }
std::string test_st::prt(bool all) const
{
    return (fmt::format("a:0x{:03x}",
       (uint64_t) a
    ));
}
void test_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test_st::_byteWidth);
    _ret = a;
}
void test_st::unpack(_packedSt &_src)
{
    a = (cmdidT)((_src) & ((1ULL << 10) - 1));
}
sc_bv<10> test_st::sc_pack(void) const
{
    sc_bv<10> packed_data;
    packed_data.range(9, 0) = a;
    return packed_data;
}
void test_st::sc_unpack(sc_bv<10> packed_data)
{
    a = (cmdidT) packed_data.range(9, 0).to_uint64();
}
bool bigSt::operator == (const bigSt & rhs) const {
    bool ret = true; 
    ret = ret && (b.word[ 0 ] == rhs.b.word[ 0 ]);
    ret = ret && (b.word[ 1 ] == rhs.b.word[ 1 ]);
    return ( ret );
    }
std::string bigSt::prt(bool all) const
{
    return (fmt::format("b:0x{:08x}{:016x}",
       b.word[1],
       b.word[0]
    ));
}
void bigSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, bigSt::_byteWidth);
    pack_bits((uint64_t *)&_ret, 0, (uint64_t *)&b, 96);
}
void bigSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    b.word[0] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
    _pos += 64;
    b.word[1] = ((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 32) - 1));
}
sc_bv<96> bigSt::sc_pack(void) const
{
    sc_bv<96> packed_data;
    packed_data.range(63, 0) = b.word[0];
    packed_data.range(95, 64) = b.word[1];
    return packed_data;
}
void bigSt::sc_unpack(sc_bv<96> packed_data)
{
    b.word[0] = (uint64_t) packed_data.range(63, 0).to_uint64();
    b.word[1] = (uint64_t) packed_data.range(95, 64).to_uint64();
}
bool testDataSt::operator == (const testDataSt & rhs) const {
    bool ret = true; 
    ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
    ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
    return ( ret );
    }
std::string testDataSt::prt(bool all) const
{
    return (fmt::format("data:0x{:016x}{:016x}",
       data.word[1],
       data.word[0]
    ));
}
void testDataSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, testDataSt::_byteWidth);
    pack_bits((uint64_t *)&_ret, 0, (uint64_t *)&data, 128);
}
void testDataSt::unpack(_packedSt &_src)
{
    uint16_t _pos{0};
    data.word[0] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
    _pos += 64;
    data.word[1] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
}
sc_bv<128> testDataSt::sc_pack(void) const
{
    sc_bv<128> packed_data;
    packed_data.range(63, 0) = data.word[0];
    packed_data.range(127, 64) = data.word[1];
    return packed_data;
}
void testDataSt::sc_unpack(sc_bv<128> packed_data)
{
    data.word[0] = (uint64_t) packed_data.range(63, 0).to_uint64();
    data.word[1] = (uint64_t) packed_data.range(127, 64).to_uint64();
}
bool testDataHdrSt::operator == (const testDataHdrSt & rhs) const {
    bool ret = true; 
    ret = ret && (cmdid == rhs.cmdid);
    return ( ret );
    }
std::string testDataHdrSt::prt(bool all) const
{
    return (fmt::format("cmdid:0x{:03x}",
       (uint64_t) cmdid
    ));
}
void testDataHdrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, testDataHdrSt::_byteWidth);
    _ret = cmdid;
}
void testDataHdrSt::unpack(_packedSt &_src)
{
    cmdid = (cmdidT)((_src) & ((1ULL << 10) - 1));
}
sc_bv<10> testDataHdrSt::sc_pack(void) const
{
    sc_bv<10> packed_data;
    packed_data.range(9, 0) = cmdid;
    return packed_data;
}
void testDataHdrSt::sc_unpack(sc_bv<10> packed_data)
{
    cmdid = (cmdidT) packed_data.range(9, 0).to_uint64();
}
bool lengthHdrSt::operator == (const lengthHdrSt & rhs) const {
    bool ret = true; 
    ret = ret && (length == rhs.length);
    return ( ret );
    }
std::string lengthHdrSt::prt(bool all) const
{
    return (fmt::format("length:0x{:04x}",
       (uint64_t) length
    ));
}
void lengthHdrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, lengthHdrSt::_byteWidth);
    _ret = length;
}
void lengthHdrSt::unpack(_packedSt &_src)
{
    length = (lengthT)((_src));
}
sc_bv<16> lengthHdrSt::sc_pack(void) const
{
    sc_bv<16> packed_data;
    packed_data.range(15, 0) = length;
    return packed_data;
}
void lengthHdrSt::sc_unpack(sc_bv<16> packed_data)
{
    length = (lengthT) packed_data.range(15, 0).to_uint64();
}
bool cmdidHdrSt::operator == (const cmdidHdrSt & rhs) const {
    bool ret = true; 
    ret = ret && (cmdid == rhs.cmdid);
    return ( ret );
    }
std::string cmdidHdrSt::prt(bool all) const
{
    return (fmt::format("cmdid:0x{:03x}",
       (uint64_t) cmdid
    ));
}
void cmdidHdrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, cmdidHdrSt::_byteWidth);
    _ret = cmdid;
}
void cmdidHdrSt::unpack(_packedSt &_src)
{
    cmdid = (cmdidT)((_src) & ((1ULL << 10) - 1));
}
sc_bv<10> cmdidHdrSt::sc_pack(void) const
{
    sc_bv<10> packed_data;
    packed_data.range(9, 0) = cmdid;
    return packed_data;
}
void cmdidHdrSt::sc_unpack(sc_bv<10> packed_data)
{
    cmdid = (cmdidT) packed_data.range(9, 0).to_uint64();
}

// GENERATED_CODE_END



