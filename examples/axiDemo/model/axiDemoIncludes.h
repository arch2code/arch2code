#ifndef AXIDEMOINCLUDES_H
#define AXIDEMOINCLUDES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <cstdint>

// GENERATED_CODE_PARAM --context=axiDemo.yaml
// GENERATED_DISABLE_CODE_BEGIN --template=headers

// GENERATED_DISABLE_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t AXI_ADDRESS_WIDTH = 32;  // The width of the AXI address busses
const uint32_t AXI_DATA_WIDTH = 32;  // The width of the AXI data busses
const uint32_t AXI_STROBE_WIDTH = 4;  // The width of the AXI strobe signals

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types 
// types
typedef uint32_t axiAddrT; // [32] Address Width
typedef uint32_t axiDataT; // [32] Width of the data bus.
typedef uint8_t axiStrobeT; // [4] Width of the strobe bus.

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums 
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct axiAddrSt {
    axiAddrT addr; //

    axiAddrSt() {}

    static constexpr uint16_t _bitWidth = AXI_ADDRESS_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    bool operator == (const axiAddrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const axiAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.addr, NAME + ".addr");
    }
    inline friend ostream& operator << ( ostream& os,  axiAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<axiAddrSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<axiAddrSt::_bitWidth> packed_data);
    explicit axiAddrSt(sc_bv<axiAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit axiAddrSt(
        axiAddrT addr_) :
        addr(addr_)
    {}
    explicit axiAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct axiDataSt {
    axiDataT data; //

    axiDataSt() {}

    static constexpr uint16_t _bitWidth = AXI_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    bool operator == (const axiDataSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const axiDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  axiDataSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<axiDataSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<axiDataSt::_bitWidth> packed_data);
    explicit axiDataSt(sc_bv<axiDataSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit axiDataSt(
        axiDataT data_) :
        data(data_)
    {}
    explicit axiDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct axiStrobeSt {
    axiStrobeT strobe; //

    axiStrobeSt() {}

    static constexpr uint16_t _bitWidth = AXI_STROBE_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    bool operator == (const axiStrobeSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const axiStrobeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.strobe, NAME + ".strobe");
    }
    inline friend ostream& operator << ( ostream& os,  axiStrobeSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<axiStrobeSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<axiStrobeSt::_bitWidth> packed_data);
    explicit axiStrobeSt(sc_bv<axiStrobeSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit axiStrobeSt(
        axiStrobeT strobe_) :
        strobe(strobe_)
    {}
    explicit axiStrobeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END

#endif //AXIDEMOINCLUDES_H

