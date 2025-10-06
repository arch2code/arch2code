#ifndef MIXEDBLOCKCINCLUDES_H
#define MIXEDBLOCKCINCLUDES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <cstdint>


// GENERATED_CODE_PARAM --context=mixedBlockC.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t CSIZE = 2;  // The size of C
const uint32_t CSIZE_PLUS = 3;  // The size of C plus 1

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types 
// types
typedef uint8_t cSizeT; // [2] size of c
typedef uint8_t cSizePlusT; // [3] size of c plus 1
typedef uint16_t cBiggerT; // [13] yet another type

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums 
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct seeSt {
    cSizePlusT variablec2; //
    cSizeT variablec; //

    seeSt() {}

    static constexpr uint16_t _bitWidth = 5;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const seeSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const seeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.variablec, NAME + ".variablec");
        sc_trace(tf,v.variablec2, NAME + ".variablec2");
    }
    inline friend ostream& operator << ( ostream& os,  seeSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<5> sc_pack(void) const;
    void sc_unpack(sc_bv<5> packed_data);
    explicit seeSt(sc_bv<5> packed_data) { sc_unpack(packed_data); }
    explicit seeSt(
        cSizePlusT variablec2_,
        cSizeT variablec_) :
        variablec2(variablec2_),
        variablec(variablec_)
    {}
    explicit seeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cHeaderSt {
    cBiggerT hdr; //

    cHeaderSt() {}

    static constexpr uint16_t _bitWidth = 13;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const cHeaderSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const cHeaderSt & v, const std::string & NAME ) {
        sc_trace(tf,v.hdr, NAME + ".hdr");
    }
    inline friend ostream& operator << ( ostream& os,  cHeaderSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<13> sc_pack(void) const;
    void sc_unpack(sc_bv<13> packed_data);
    explicit cHeaderSt(sc_bv<13> packed_data) { sc_unpack(packed_data); }
    explicit cHeaderSt(
        cBiggerT hdr_) :
        hdr(hdr_)
    {}
    explicit cHeaderSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END

#endif //MIXEDBLOCKCINCLUDES_H
