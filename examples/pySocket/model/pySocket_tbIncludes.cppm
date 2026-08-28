
// GENERATED_CODE_PARAM --project=pySocket --context=pySocket_tb.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module pySocket_tb;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace pySocket_tb_ns {
//constants

} // namespace pySocket_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace pySocket_tb_ns {
// types
typedef uint32_t param_t; // [32] Parameter type
typedef uint16_t word16_t; // [16] Parameter type
typedef uint8_t axis_id_t; // [8] AXI4-Stream TID/TDEST width

} // namespace pySocket_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace pySocket_tb_ns {
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

} // namespace pySocket_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace pySocket_tb_ns {
// structures
struct message_header_st {
    word16_t tag; //Tag
    word16_t ID; //Message ID
    word16_t length; //Message payload length

    message_header_st() {}

    static constexpr uint16_t _bitWidth = 16 + 16 + 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const message_header_st & rhs) const {
        bool ret = true;
        ret = ret && (length == rhs.length);
        ret = ret && (ID == rhs.ID);
        ret = ret && (tag == rhs.tag);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const message_header_st & v, const std::string & NAME ) {
        sc_trace(tf,v.length, NAME + ".length");
        sc_trace(tf,v.ID, NAME + ".ID");
        sc_trace(tf,v.tag, NAME + ".tag");
    }
    inline friend ostream& operator << ( ostream& os,  message_header_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("length:0x{:04x} ID:0x{:04x} tag:0x{:04x}",
           (uint64_t) length,
           (uint64_t) ID,
           (uint64_t) tag
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
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
    inline sc_bv<message_header_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<message_header_st::_bitWidth> packed_data;
        packed_data.range(15, 0) = tag;
        packed_data.range(31, 16) = ID;
        packed_data.range(47, 32) = length;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<message_header_st::_bitWidth> packed_data)
    {
        tag = (word16_t) packed_data.range(15, 0).to_uint64();
        ID = (word16_t) packed_data.range(31, 16).to_uint64();
        length = (word16_t) packed_data.range(47, 32).to_uint64();
    }
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
    inline bool operator == (const p2s_message_st & rhs) const {
        bool ret = true;
        ret = ret && (param2 == rhs.param2);
        ret = ret && (param1 == rhs.param1);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const p2s_message_st & v, const std::string & NAME ) {
        sc_trace(tf,v.param2, NAME + ".param2");
        sc_trace(tf,v.param1, NAME + ".param1");
    }
    inline friend ostream& operator << ( ostream& os,  p2s_message_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("param2:0x{:08x} param1:0x{:08x}",
           (uint64_t) param2,
           (uint64_t) param1
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
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
    inline sc_bv<p2s_message_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<p2s_message_st::_bitWidth> packed_data;
        packed_data.range(31, 0) = param1;
        packed_data.range(63, 32) = param2;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<p2s_message_st::_bitWidth> packed_data)
    {
        param1 = (param_t) packed_data.range(31, 0).to_uint64();
        param2 = (param_t) packed_data.range(63, 32).to_uint64();
    }
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
    inline bool operator == (const p2s_response_st & rhs) const {
        bool ret = true;
        ret = ret && (response == rhs.response);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const p2s_response_st & v, const std::string & NAME ) {
        sc_trace(tf,v.response, NAME + ".response");
    }
    inline friend ostream& operator << ( ostream& os,  p2s_response_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("response:0x{:08x}",
           (uint64_t) response
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, p2s_response_st::_byteWidth);
        _ret = response;
    }
    inline void unpack(const _packedSt &_src)
    {
        response = (param_t)((_src));
    }
    inline sc_bv<p2s_response_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<p2s_response_st::_bitWidth> packed_data;
        packed_data.range(31, 0) = response;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<p2s_response_st::_bitWidth> packed_data)
    {
        response = (param_t) packed_data.range(31, 0).to_uint64();
    }
    explicit p2s_response_st(sc_bv<p2s_response_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit p2s_response_st(
        param_t response_) :
        response(response_)
    {}
    explicit p2s_response_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct axis_tid_st {
    axis_id_t id; //Stream TID

    axis_tid_st() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const axis_tid_st & rhs) const {
        bool ret = true;
        ret = ret && (id == rhs.id);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const axis_tid_st & v, const std::string & NAME ) {
        sc_trace(tf,v.id, NAME + ".id");
    }
    inline friend ostream& operator << ( ostream& os,  axis_tid_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("id:0x{:02x}",
           (uint64_t) id
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, axis_tid_st::_byteWidth);
        _ret = id;
    }
    inline void unpack(const _packedSt &_src)
    {
        id = (axis_id_t)((_src));
    }
    inline sc_bv<axis_tid_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<axis_tid_st::_bitWidth> packed_data;
        packed_data.range(7, 0) = id;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<axis_tid_st::_bitWidth> packed_data)
    {
        id = (axis_id_t) packed_data.range(7, 0).to_uint64();
    }
    explicit axis_tid_st(sc_bv<axis_tid_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit axis_tid_st(
        axis_id_t id_) :
        id(id_)
    {}
    explicit axis_tid_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct axis_tdest_st {
    axis_id_t id; //Stream TDEST

    axis_tdest_st() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const axis_tdest_st & rhs) const {
        bool ret = true;
        ret = ret && (id == rhs.id);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const axis_tdest_st & v, const std::string & NAME ) {
        sc_trace(tf,v.id, NAME + ".id");
    }
    inline friend ostream& operator << ( ostream& os,  axis_tdest_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("id:0x{:02x}",
           (uint64_t) id
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, axis_tdest_st::_byteWidth);
        _ret = id;
    }
    inline void unpack(const _packedSt &_src)
    {
        id = (axis_id_t)((_src));
    }
    inline sc_bv<axis_tdest_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<axis_tdest_st::_bitWidth> packed_data;
        packed_data.range(7, 0) = id;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<axis_tdest_st::_bitWidth> packed_data)
    {
        id = (axis_id_t) packed_data.range(7, 0).to_uint64();
    }
    explicit axis_tdest_st(sc_bv<axis_tdest_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit axis_tdest_st(
        axis_id_t id_) :
        id(id_)
    {}
    explicit axis_tdest_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace pySocket_tb_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace pySocket_tb_test_ns {
class test_pySocket_tb_structs {
public:
    static std::string name(void);
    static void test(void);
private:
    template<typename T>
    static void roundTrip(const char* sName, const std::vector<uint8_t>& patterns) {
        for(auto pattern : patterns) {
            typename T::_packedSt packed;
            memset(&packed, pattern, T::_byteWidth);
            sc_bv<T::_bitWidth> aInit;
            sc_bv<T::_bitWidth> aTest;
            for (int i = 0; i < T::_byteWidth; i++) {
                int end = std::min((i+1)*8-1, T::_bitWidth-1);
                aInit.range(end, i*8) = pattern;
            }
            T a;
            a.sc_unpack(aInit);
            T b;
            b.unpack(packed);
            if (!(b == a)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false, sName);
            }
            uint64_t test;
            memset(&test, pattern, 8);
            b.pack(packed);
            aTest = a.sc_pack();
            if (!(aTest == aInit)) {;
                cout << a.prt();
                cout << aTest;
                Q_ASSERT(false, sName);
            }
            uint64_t *ptr = (uint64_t *)&packed;
            uint16_t bitsLeft = T::_bitWidth;
            do {
                int bits = std::min((uint16_t)64, bitsLeft);
                uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
                if ((*ptr & mask) != (test & mask)) {;
                    cout << a.prt();
                    cout << b.prt();
                    Q_ASSERT(false, sName);
                }
                bitsLeft -= bits;
                ptr++;
            } while(bitsLeft > 0);
        }
    }
};
} // namespace pySocket_tb_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace pySocket_tb_test_ns {
using namespace pySocket_tb_ns;
std::string test_pySocket_tb_structs::name(void) { return "test_pySocket_tb_structs"; }
void test_pySocket_tb_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<message_header_st>("message_header_st", patterns);
    roundTrip<p2s_message_st>("p2s_message_st", patterns);
    roundTrip<p2s_response_st>("p2s_response_st", patterns);
    roundTrip<axis_tid_st>("axis_tid_st", patterns);
    roundTrip<axis_tdest_st>("axis_tdest_st", patterns);
}
} // namespace pySocket_tb_test_ns

// GENERATED_CODE_END
