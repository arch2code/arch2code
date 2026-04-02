
// 
#include "pySocketIncludes.h"
// GENERATED_CODE_PARAM --context=pySocket.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool p2s_message_st::operator == (const p2s_message_st & rhs) const {
    bool ret = true;
    ret = ret && (param1 == rhs.param1);
    ret = ret && (param2 == rhs.param2);
    return ( ret );
    }
std::string p2s_message_st::prt(bool all) const
{
    return (std::format("param1:0x{:08x} param2:0x{:08x}",
       (uint64_t) param1,
       (uint64_t) param2
    ));
}
void p2s_message_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, p2s_message_st::_byteWidth);
    _ret = param2;
    _ret |= (uint64_t)param1 << (32 & 63);
}
void p2s_message_st::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    param2 = (param_t)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
    _pos += 32;
    param1 = (param_t)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
}
sc_bv<p2s_message_st::_bitWidth> p2s_message_st::sc_pack(void) const
{
    sc_bv<p2s_message_st::_bitWidth> packed_data;
    packed_data.range(31, 0) = param2;
    packed_data.range(63, 32) = param1;
    return packed_data;
}
void p2s_message_st::sc_unpack(sc_bv<p2s_message_st::_bitWidth> packed_data)
{
    param2 = (param_t) packed_data.range(31, 0).to_uint64();
    param1 = (param_t) packed_data.range(63, 32).to_uint64();
}
bool p2s_response_st::operator == (const p2s_response_st & rhs) const {
    bool ret = true;
    ret = ret && (response == rhs.response);
    return ( ret );
    }
std::string p2s_response_st::prt(bool all) const
{
    return (std::format("response:0x{:08x}",
       (uint64_t) response
    ));
}
void p2s_response_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, p2s_response_st::_byteWidth);
    _ret = response;
}
void p2s_response_st::unpack(const _packedSt &_src)
{
    response = (param_t)((_src));
}
sc_bv<p2s_response_st::_bitWidth> p2s_response_st::sc_pack(void) const
{
    sc_bv<p2s_response_st::_bitWidth> packed_data;
    packed_data.range(31, 0) = response;
    return packed_data;
}
void p2s_response_st::sc_unpack(sc_bv<p2s_response_st::_bitWidth> packed_data)
{
    response = (param_t) packed_data.range(31, 0).to_uint64();
}
bool p2s_message_tag_st::operator == (const p2s_message_tag_st & rhs) const {
    bool ret = true;
    ret = ret && (tag == rhs.tag);
    return ( ret );
    }
std::string p2s_message_tag_st::prt(bool all) const
{
    return (std::format("tag:0x{:01x}",
       (uint64_t) tag
    ));
}
void p2s_message_tag_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, p2s_message_tag_st::_byteWidth);
    _ret = tag;
}
void p2s_message_tag_st::unpack(const _packedSt &_src)
{
    tag = (p2s_message_tag_t)((_src) & ((1ULL << 4) - 1));
}
sc_bv<p2s_message_tag_st::_bitWidth> p2s_message_tag_st::sc_pack(void) const
{
    sc_bv<p2s_message_tag_st::_bitWidth> packed_data;
    packed_data.range(3, 0) = tag;
    return packed_data;
}
void p2s_message_tag_st::sc_unpack(sc_bv<p2s_message_tag_st::_bitWidth> packed_data)
{
    tag = (p2s_message_tag_t) packed_data.range(3, 0).to_uint64();
}

// GENERATED_CODE_END
