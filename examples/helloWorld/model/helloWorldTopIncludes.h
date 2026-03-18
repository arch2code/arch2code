#ifndef HELLOWORLDTOPINCLUDES_H
#define HELLOWORLDTOPINCLUDES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <cstdint>


// GENERATED_CODE_PARAM --context=helloWorldTop.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t BUFFER_SIZE = 64;  // Buffer size

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types 
// types
typedef uint8_t byteT; // [8] Byte
typedef uint64_t qwordT; // [64] 64 bits

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums 
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct test_st {
    byteT a; //

    test_st() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    bool operator == (const test_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test_st & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  test_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "tracker:cmd" );}
    inline uint64_t getStructValue(void) const { return( a );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<test_st::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<test_st::_bitWidth> packed_data);
    explicit test_st(sc_bv<test_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit test_st(
        byteT a_) :
        a(a_)
    {}
    explicit test_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test_no_tracker_st {
    byteT a; //

    test_no_tracker_st() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    bool operator == (const test_no_tracker_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test_no_tracker_st & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  test_no_tracker_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<test_no_tracker_st::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<test_no_tracker_st::_bitWidth> packed_data);
    explicit test_no_tracker_st(sc_bv<test_no_tracker_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit test_no_tracker_st(
        byteT a_) :
        a(a_)
    {}
    explicit test_no_tracker_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct data_st {
    qwordT b; //

    data_st() {}

    static constexpr uint16_t _bitWidth = 64;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    bool operator == (const data_st & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const data_st & v, const std::string & NAME ) {
        sc_trace(tf,v.b, NAME + ".b");
    }
    inline friend ostream& operator << ( ostream& os,  data_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<data_st::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<data_st::_bitWidth> packed_data);
    explicit data_st(sc_bv<data_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit data_st(
        qwordT b_) :
        b(b_)
    {}
    explicit data_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END

#endif //HELLOWORLDTOPINCLUDES_H

