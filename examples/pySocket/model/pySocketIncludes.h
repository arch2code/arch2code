
#ifndef PYSOCKETINCLUDES_H_
#define PYSOCKETINCLUDES_H_
// 

#include "systemc.h"

// GENERATED_CODE_PARAM --context=pySocket.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t P2S_MESSAGE_LIST_SIZE = 16;  // Size of the p2s message list
const uint32_t P2S_MESSAGE_LIST_LOG2 = 4;  // Log2 of the p2s message list size

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint8_t p2s_message_tag_t; // [4] Tag type
typedef uint32_t param_t; // [32] Parameter type

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct p2s_message_st {
    param_t param2; //Parameter 2
    param_t param1; //Parameter 1

    p2s_message_st() {}

    static constexpr uint16_t _bitWidth = 32 + 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    bool operator == (const p2s_message_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const p2s_message_st & v, const std::string & NAME ) {
        sc_trace(tf,v.param1, NAME + ".param1");
        sc_trace(tf,v.param2, NAME + ".param2");
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
        param_t param2_,
        param_t param1_) :
        param2(param2_),
        param1(param1_)
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
struct p2s_message_tag_st {
    p2s_message_tag_t tag; //Tag

    p2s_message_tag_st() {}

    static constexpr uint16_t _bitWidth = P2S_MESSAGE_LIST_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    bool operator == (const p2s_message_tag_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const p2s_message_tag_st & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
    }
    inline friend ostream& operator << ( ostream& os,  p2s_message_tag_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<p2s_message_tag_st::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<p2s_message_tag_st::_bitWidth> packed_data);
    explicit p2s_message_tag_st(sc_bv<p2s_message_tag_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit p2s_message_tag_st(
        p2s_message_tag_t tag_) :
        tag(tag_)
    {}
    explicit p2s_message_tag_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END
#endif //PYSOCKETINCLUDES_H_
