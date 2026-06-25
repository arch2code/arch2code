
#ifndef PYSOCKET_TBINCLUDES_H_
#define PYSOCKET_TBINCLUDES_H_
// 

#include "systemc.h"

// GENERATED_CODE_PARAM --context=pySocket_tb.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
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

    message_header_st() {}

    static constexpr uint16_t _bitWidth = 16 + 16 + 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    bool operator == (const message_header_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const message_header_st & v, const std::string & NAME ) {
        sc_trace(tf,v.length, NAME + ".length");
        sc_trace(tf,v.ID, NAME + ".ID");
        sc_trace(tf,v.tag, NAME + ".tag");
    }
    inline friend ostream& operator << ( ostream& os,  message_header_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<message_header_st::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<message_header_st::_bitWidth> packed_data);
    explicit message_header_st(sc_bv<message_header_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit message_header_st(
        word16_t tag_,
        word16_t ID_,
        word16_t length_) :
        tag(tag_),
        ID(ID_),
        length(length_)
    {}
    explicit message_header_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct p2s_message_st {
    param_t param1; //Parameter 1
    param_t param2; //Parameter 2

    p2s_message_st() {}

    static constexpr uint16_t _bitWidth = 32 + 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    bool operator == (const p2s_message_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const p2s_message_st & v, const std::string & NAME ) {
        sc_trace(tf,v.param2, NAME + ".param2");
        sc_trace(tf,v.param1, NAME + ".param1");
    }
    inline friend ostream& operator << ( ostream& os,  p2s_message_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<p2s_message_st::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<p2s_message_st::_bitWidth> packed_data);
    explicit p2s_message_st(sc_bv<p2s_message_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit p2s_message_st(
        param_t param1_,
        param_t param2_) :
        param1(param1_),
        param2(param2_)
    {}
    explicit p2s_message_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct p2s_response_st {
    param_t response; //response

    p2s_response_st() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    bool operator == (const p2s_response_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const p2s_response_st & v, const std::string & NAME ) {
        sc_trace(tf,v.response, NAME + ".response");
    }
    inline friend ostream& operator << ( ostream& os,  p2s_response_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<p2s_response_st::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<p2s_response_st::_bitWidth> packed_data);
    explicit p2s_response_st(sc_bv<p2s_response_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit p2s_response_st(
        param_t response_) :
        response(response_)
    {}
    explicit p2s_response_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END
#endif //PYSOCKET_TBINCLUDES_H_
