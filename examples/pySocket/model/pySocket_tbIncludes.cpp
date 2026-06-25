
// 
#include "pySocket_tbIncludes.h"
// GENERATED_CODE_PARAM --context=pySocket_tb.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool message_header_st::operator == (const message_header_st & rhs) const {
    bool ret = true;
    ret = ret && (length == rhs.length);
    ret = ret && (ID == rhs.ID);
    ret = ret && (tag == rhs.tag);
    return ( ret );
    }
std::string message_header_st::prt(bool all) const
{
    return (std::format("length:0x{:04x} ID:0x{:04x} tag:0x{:04x}",
       (uint64_t) length,
       (uint64_t) ID,
       (uint64_t) tag
    ));
}
void message_header_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, message_header_st::_byteWidth);
    _ret = tag;
    _ret |= (uint64_t)ID << (16 & 63);
    _ret |= (uint64_t)length << (32 & 63);
}
void message_header_st::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    tag = (word16_t)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
    _pos += 16;
    ID = (word16_t)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
    _pos += 16;
    length = (word16_t)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
}
sc_bv<message_header_st::_bitWidth> message_header_st::sc_pack(void) const
{
    sc_bv<message_header_st::_bitWidth> packed_data;
    packed_data.range(15, 0) = tag;
    packed_data.range(31, 16) = ID;
    packed_data.range(47, 32) = length;
    return packed_data;
}
void message_header_st::sc_unpack(sc_bv<message_header_st::_bitWidth> packed_data)
{
    tag = (word16_t) packed_data.range(15, 0).to_uint64();
    ID = (word16_t) packed_data.range(31, 16).to_uint64();
    length = (word16_t) packed_data.range(47, 32).to_uint64();
}
bool p2s_message_st::operator == (const p2s_message_st & rhs) const {
    bool ret = true;
    ret = ret && (param2 == rhs.param2);
    ret = ret && (param1 == rhs.param1);
    return ( ret );
    }
std::string p2s_message_st::prt(bool all) const
{
    return (std::format("param2:0x{:08x} param1:0x{:08x}",
       (uint64_t) param2,
       (uint64_t) param1
    ));
}
void p2s_message_st::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, p2s_message_st::_byteWidth);
    _ret = param1;
    _ret |= (uint64_t)param2 << (32 & 63);
}
void p2s_message_st::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    param1 = (param_t)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
    _pos += 32;
    param2 = (param_t)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
}
sc_bv<p2s_message_st::_bitWidth> p2s_message_st::sc_pack(void) const
{
    sc_bv<p2s_message_st::_bitWidth> packed_data;
    packed_data.range(31, 0) = param1;
    packed_data.range(63, 32) = param2;
    return packed_data;
}
void p2s_message_st::sc_unpack(sc_bv<p2s_message_st::_bitWidth> packed_data)
{
    param1 = (param_t) packed_data.range(31, 0).to_uint64();
    param2 = (param_t) packed_data.range(63, 32).to_uint64();
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

// GENERATED_CODE_END
