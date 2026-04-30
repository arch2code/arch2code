
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "ipIncludes.h"
// GENERATED_CODE_PARAM --context=ip.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool ipDataSt::operator == (const ipDataSt & rhs) const {
    bool ret = true;
    ret = ret && (data == rhs.data);
    return ( ret );
    }
std::string ipDataSt::prt(bool all) const
{
    return (std::format("data:0x{:02x}",
       (uint64_t) data
    ));
}
void ipDataSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, ipDataSt::_byteWidth);
    _ret = data;
}
void ipDataSt::unpack(const _packedSt &_src)
{
    data = (ipDataT)((_src));
}
sc_bv<ipDataSt::_bitWidth> ipDataSt::sc_pack(void) const
{
    sc_bv<ipDataSt::_bitWidth> packed_data;
    packed_data.range(7, 0) = data;
    return packed_data;
}
void ipDataSt::sc_unpack(sc_bv<ipDataSt::_bitWidth> packed_data)
{
    data = (ipDataT) packed_data.range(7, 0).to_uint64();
}
bool ipCfgSt::operator == (const ipCfgSt & rhs) const {
    bool ret = true;
    ret = ret && (enable == rhs.enable);
    ret = ret && (mode == rhs.mode);
    ret = ret && (threshold == rhs.threshold);
    return ( ret );
    }
std::string ipCfgSt::prt(bool all) const
{
    return (std::format("enable:0x{:01x} mode:{} threshold:0x{:02x}",
       (uint64_t) enable,
       ipModeT_prt( mode ),
       (uint64_t) threshold
    ));
}
void ipCfgSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, ipCfgSt::_byteWidth);
    _ret = threshold;
    _ret |= (uint16_t)mode << (8 & 15);
    _ret |= (uint16_t)enable << (10 & 15);
}
void ipCfgSt::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    threshold = (ipDataT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
    _pos += 8;
    mode = (ipModeT)((_src >> (_pos & 15)) & ((1ULL << 2) - 1));
    _pos += 2;
    enable = (enableT)((_src >> (_pos & 15)) & 1);
}
sc_bv<ipCfgSt::_bitWidth> ipCfgSt::sc_pack(void) const
{
    sc_bv<ipCfgSt::_bitWidth> packed_data;
    packed_data.range(7, 0) = threshold;
    packed_data.range(9, 8) = mode;
    packed_data.range(10, 10) = enable;
    return packed_data;
}
void ipCfgSt::sc_unpack(sc_bv<ipCfgSt::_bitWidth> packed_data)
{
    threshold = (ipDataT) packed_data.range(7, 0).to_uint64();
    mode = (ipModeT) packed_data.range(9, 8).to_uint64();
    enable = (enableT) packed_data.range(10, 10).to_uint64();
}
bool ipMemSt::operator == (const ipMemSt & rhs) const {
    bool ret = true;
    ret = ret && (data == rhs.data);
    return ( ret );
    }
std::string ipMemSt::prt(bool all) const
{
    return (std::format("data:0x{:02x}",
       (uint64_t) data
    ));
}
void ipMemSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, ipMemSt::_byteWidth);
    _ret = data;
}
void ipMemSt::unpack(const _packedSt &_src)
{
    data = (ipDataT)((_src));
}
sc_bv<ipMemSt::_bitWidth> ipMemSt::sc_pack(void) const
{
    sc_bv<ipMemSt::_bitWidth> packed_data;
    packed_data.range(7, 0) = data;
    return packed_data;
}
void ipMemSt::sc_unpack(sc_bv<ipMemSt::_bitWidth> packed_data)
{
    data = (ipDataT) packed_data.range(7, 0).to_uint64();
}
bool ipMemAddrSt::operator == (const ipMemAddrSt & rhs) const {
    bool ret = true;
    ret = ret && (address == rhs.address);
    return ( ret );
    }
std::string ipMemAddrSt::prt(bool all) const
{
    return (std::format("address:0x{:01x}",
       (uint64_t) address
    ));
}
void ipMemAddrSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, ipMemAddrSt::_byteWidth);
    _ret = address;
}
void ipMemAddrSt::unpack(const _packedSt &_src)
{
    address = (ipMemAddrT)((_src) & ((1ULL << 4) - 1));
}
sc_bv<ipMemAddrSt::_bitWidth> ipMemAddrSt::sc_pack(void) const
{
    sc_bv<ipMemAddrSt::_bitWidth> packed_data;
    packed_data.range(3, 0) = address;
    return packed_data;
}
void ipMemAddrSt::sc_unpack(sc_bv<ipMemAddrSt::_bitWidth> packed_data)
{
    address = (ipMemAddrT) packed_data.range(3, 0).to_uint64();
}

// GENERATED_CODE_END
