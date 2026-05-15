
#ifndef PYSOCKET_TBINCLUDESFW_H_
#define PYSOCKET_TBINCLUDESFW_H_
// 

#include <cstdint>
#include <cstring>

// GENERATED_CODE_PARAM --context=pySocket_tb.yaml --mode=fw
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
namespace fw_ns {
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint32_t param_t; // [32] Parameter type
typedef uint16_t word16_t; // [16] Parameter type

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums
enum  p2s_message_ID_t {     //Message ID
    P2S_MESSAGE_TYPE_REQUEST=0,   // Request
    P2S_MESSAGE_TYPE_RESPONSE=1 }; // Response
inline const char* p2s_message_ID_t_prt( p2s_message_ID_t val )
{
    switch( val )
    {
        case P2S_MESSAGE_TYPE_REQUEST: return( "P2S_MESSAGE_TYPE_REQUEST" );
        case P2S_MESSAGE_TYPE_RESPONSE: return( "P2S_MESSAGE_TYPE_RESPONSE" );
    }
    return("!!!BADENUM!!!");
}

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct message_header_st {
    word16_t tag; //Tag
    word16_t ID; //Message ID
    word16_t length; //Message payload length

    message_header_st() { memset(this, 0, sizeof(message_header_st)); }

    static constexpr uint16_t _bitWidth = 16 + 16 + 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, message_header_st::_byteWidth);
        _ret = tag;
        _ret |= (uint64_t)ID << (16 & 63);
        _ret |= (uint64_t)length << (32 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        tag = (word16_t)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
        _pos += 16;
        ID = (word16_t)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
        _pos += 16;
        length = (word16_t)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
    }
    explicit message_header_st(
        word16_t tag_,
        word16_t ID_,
        word16_t length_) :
        tag(tag_),
        ID(ID_),
        length(length_)
    {}

};
struct p2s_message_st {
    param_t param1; //Parameter 1
    param_t param2; //Parameter 2

    p2s_message_st() { memset(this, 0, sizeof(p2s_message_st)); }

    static constexpr uint16_t _bitWidth = 32 + 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, p2s_message_st::_byteWidth);
        _ret = param1;
        _ret |= (uint64_t)param2 << (32 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        param1 = (param_t)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += 32;
        param2 = (param_t)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
    }
    explicit p2s_message_st(
        param_t param1_,
        param_t param2_) :
        param1(param1_),
        param2(param2_)
    {}

};
struct p2s_response_st {
    param_t response; //response

    p2s_response_st() { memset(this, 0, sizeof(p2s_response_st)); }

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, p2s_response_st::_byteWidth);
        _ret = response;
    }
    inline void unpack(const _packedSt &_src)
    {
        response = (param_t)((_src));
    }
    explicit p2s_response_st(
        param_t response_) :
        response(response_)
    {}

};

// GENERATED_CODE_END
} // end of namespace fw_ns
#endif //PYSOCKET_TBINCLUDESFW_H_
