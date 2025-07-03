// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "axiDemoIncludes.h"

// GENERATED_CODE_PARAM --context=axiDemo.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool axiAddrSt::operator == (const axiAddrSt & rhs) const {
    bool ret = true; 
    ret = ret && (addr == rhs.addr);
    return ( ret );
    }
std::string axiAddrSt::prt(bool all) const
{
    return (fmt::format("addr:0x{:08x}",
       (uint64_t) addr
    ));
}
void axiAddrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, axiAddrSt::_byteWidth);
    _ret = addr;
}
void axiAddrSt::unpack(_packedSt &_src)
{
    addr = (axiAddrT)((_src));
}
sc_bv<32> axiAddrSt::sc_pack(void) const
{
    sc_bv<32> packed_data;
    packed_data.range(31, 0) = addr;
    return packed_data;
}
void axiAddrSt::sc_unpack(sc_bv<32> packed_data)
{
    addr = (axiAddrT) packed_data.range(31, 0).to_uint64();
}
bool axiDataSt::operator == (const axiDataSt & rhs) const {
    bool ret = true; 
    ret = ret && (data == rhs.data);
    return ( ret );
    }
std::string axiDataSt::prt(bool all) const
{
    return (fmt::format("data:0x{:08x}",
       (uint64_t) data
    ));
}
void axiDataSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, axiDataSt::_byteWidth);
    _ret = data;
}
void axiDataSt::unpack(_packedSt &_src)
{
    data = (axiDataT)((_src));
}
sc_bv<32> axiDataSt::sc_pack(void) const
{
    sc_bv<32> packed_data;
    packed_data.range(31, 0) = data;
    return packed_data;
}
void axiDataSt::sc_unpack(sc_bv<32> packed_data)
{
    data = (axiDataT) packed_data.range(31, 0).to_uint64();
}
bool axiStrobeSt::operator == (const axiStrobeSt & rhs) const {
    bool ret = true; 
    ret = ret && (strobe == rhs.strobe);
    return ( ret );
    }
std::string axiStrobeSt::prt(bool all) const
{
    return (fmt::format("strobe:0x{:01x}",
       (uint64_t) strobe
    ));
}
void axiStrobeSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, axiStrobeSt::_byteWidth);
    _ret = strobe;
}
void axiStrobeSt::unpack(_packedSt &_src)
{
    strobe = (axiStrobeT)((_src) & ((1ULL << 4) - 1));
}
sc_bv<4> axiStrobeSt::sc_pack(void) const
{
    sc_bv<4> packed_data;
    packed_data.range(3, 0) = strobe;
    return packed_data;
}
void axiStrobeSt::sc_unpack(sc_bv<4> packed_data)
{
    strobe = (axiStrobeT) packed_data.range(3, 0).to_uint64();
}

// GENERATED_CODE_END

