// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "helloWorldTopIncludes.h"

// GENERATED_CODE_PARAM --context=helloWorldTop.yaml
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
    return (std::format("a:0x{:02x}",
       (uint64_t) a
    ));
}
void test_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test_st::_byteWidth);
    _ret = a;
}
void test_st::unpack(const _packedSt &_src)
{
    a = (byteT)((_src));
}
sc_bv<test_st::_bitWidth> test_st::sc_pack(void) const
{
    sc_bv<test_st::_bitWidth> packed_data;
    packed_data.range(7, 0) = a;
    return packed_data;
}
void test_st::sc_unpack(sc_bv<test_st::_bitWidth> packed_data)
{
    a = (byteT) packed_data.range(7, 0).to_uint64();
}
bool test_no_tracker_st::operator == (const test_no_tracker_st & rhs) const {
    bool ret = true;
    ret = ret && (a == rhs.a);
    return ( ret );
    }
std::string test_no_tracker_st::prt(bool all) const
{
    return (std::format("a:0x{:02x}",
       (uint64_t) a
    ));
}
void test_no_tracker_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, test_no_tracker_st::_byteWidth);
    _ret = a;
}
void test_no_tracker_st::unpack(const _packedSt &_src)
{
    a = (byteT)((_src));
}
sc_bv<test_no_tracker_st::_bitWidth> test_no_tracker_st::sc_pack(void) const
{
    sc_bv<test_no_tracker_st::_bitWidth> packed_data;
    packed_data.range(7, 0) = a;
    return packed_data;
}
void test_no_tracker_st::sc_unpack(sc_bv<test_no_tracker_st::_bitWidth> packed_data)
{
    a = (byteT) packed_data.range(7, 0).to_uint64();
}
bool data_st::operator == (const data_st & rhs) const {
    bool ret = true;
    ret = ret && (b == rhs.b);
    return ( ret );
    }
std::string data_st::prt(bool all) const
{
    return (std::format("b:0x{:016x}",
       (uint64_t) b
    ));
}
void data_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, data_st::_byteWidth);
    _ret = b;
}
void data_st::unpack(const _packedSt &_src)
{
    b = (qwordT)((_src));
}
sc_bv<data_st::_bitWidth> data_st::sc_pack(void) const
{
    sc_bv<data_st::_bitWidth> packed_data;
    packed_data.range(63, 0) = b;
    return packed_data;
}
void data_st::sc_unpack(sc_bv<data_st::_bitWidth> packed_data)
{
    b = (qwordT) packed_data.range(63, 0).to_uint64();
}

// GENERATED_CODE_END


