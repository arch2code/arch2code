#ifndef MIXEDNESTEDINCLUDEINCLUDES_H
#define MIXEDNESTEDINCLUDEINCLUDES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <cstdint>

// GENERATED_CODE_PARAM --context=mixedNestedInclude.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t DSIZE = 1;  // The size of D
const uint32_t DSIZE2 = 2;  // The size of D2

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types 
// types
typedef uint16_t dupTestT; // [13] yet another type

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums 
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct dupTestSt {
    dupTestT bob; //A test structure

    dupTestSt() {}

    static constexpr uint16_t _bitWidth = 13;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    bool operator == (const dupTestSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const dupTestSt & v, const std::string & NAME ) {
        sc_trace(tf,v.bob, NAME + ".bob");
    }
    inline friend ostream& operator << ( ostream& os,  dupTestSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<dupTestSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<dupTestSt::_bitWidth> packed_data);
    explicit dupTestSt(sc_bv<dupTestSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit dupTestSt(
        dupTestT bob_) :
        bob(bob_)
    {}
    explicit dupTestSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END
#endif //MIXEDNESTEDINCLUDEINCLUDES_H
