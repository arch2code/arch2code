
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "ip_topIncludes.h"
// GENERATED_CODE_PARAM --context=ip_top.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
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
sc_bv<apbAddrSt::_bitWidth> apbAddrSt::sc_pack(void) const
{
    sc_bv<apbAddrSt::_bitWidth> packed_data;
    packed_data.range(31, 0) = address;
    return packed_data;
}
void apbAddrSt::sc_unpack(sc_bv<apbAddrSt::_bitWidth> packed_data)
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
sc_bv<apbDataSt::_bitWidth> apbDataSt::sc_pack(void) const
{
    sc_bv<apbDataSt::_bitWidth> packed_data;
    packed_data.range(31, 0) = data;
    return packed_data;
}
void apbDataSt::sc_unpack(sc_bv<apbDataSt::_bitWidth> packed_data)
{
    data = (apbDataT) packed_data.range(31, 0).to_uint64();
}

// GENERATED_CODE_END
