#ifndef INANDOUTINCLUDES_H
#define INANDOUTINCLUDES_H
#include "systemc.h"
#include <cstdint>

// GENERATED_CODE_PARAM --block=inAndOut --context=inAndOut.yaml

// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
#define ASIZE                            1  // The size of A
#define ASIZE2                           2  // The size of A+1
#define BIGE33                  8589934591  // Test constant for numbers slightly bigger than 32 bits
#define BIGE53           18014398509481983  // Test constant for numbers slightly bigger than 32 bits

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types 
// types
typedef uint8_t twoBitT; // [2] this is a 2 bit type
typedef uint8_t threeBitT; // [3] this is a 3 bit type
typedef uint8_t fourBitT; // [4] this is a 4 bit type
typedef uint8_t aSizeT; // [1] type of width ASIZE
typedef uint8_t aBiggerT; // [2] yet another type
typedef uint8_t bSizeT; // [5] for addressing memory, temp, unused

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums 
// enums
enum  readyT {               //either ready or not ready
    READY_NO=0,              // Not ready
    READY_YES=1 };           // Ready
inline const char* readyT_prt( readyT val )
{
    switch( val )
    {
        case READY_NO: return( "READY_NO" );
        case READY_YES: return( "READY_YES" );
    }
    return("!!!BADENUM!!!");
}

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct aSt {
    aSizeT variablea[ASIZE2]; //One bit of A

    aSt() {}

    static constexpr uint16_t _bitWidth = 2;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const aSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const aSt & v, const std::string & NAME ) {
        for(int i=0; i<ASIZE2; i++) {
            sc_trace(tf,v.variablea[i], NAME + ".variablea[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  aSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<2> sc_pack(void) const;
    void sc_unpack(sc_bv<2> packed_data);
    explicit aSt(sc_bv<2> packed_data) { sc_unpack(packed_data); }
    explicit aSt(
        aSizeT variablea_[ASIZE2])
    {
        memcpy(&variablea, &variablea_, sizeof(variablea));
    }
    explicit aSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bSt {
    bSizeT variableb; //Variable of B

    bSt() {}

    static constexpr uint16_t _bitWidth = 5;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const bSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const bSt & v, const std::string & NAME ) {
        sc_trace(tf,v.variableb, NAME + ".variableb");
    }
    inline friend ostream& operator << ( ostream& os,  bSt const & v ) {
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
    explicit bSt(sc_bv<5> packed_data) { sc_unpack(packed_data); }
    explicit bSt(
        bSizeT variableb_) :
        variableb(variableb_)
    {}
    explicit bSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bBSt {
    readyT ready; //

    bBSt() {}

    static constexpr uint16_t _bitWidth = 1;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const bBSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const bBSt & v, const std::string & NAME ) {
        sc_trace(tf,v.ready, NAME + ".ready");
    }
    inline friend ostream& operator << ( ostream& os,  bBSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    bool sc_pack(void) const;
    void sc_unpack(bool packed_data);
    void sc_unpack(sc_bv<1> packed_data);
    explicit bBSt(bool packed_data) { sc_unpack(packed_data); }
    explicit bBSt(
        readyT ready_) :
        ready(ready_)
    {}
    explicit bBSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct seeSt {
    threeBitT variablec2; //Three bits of C
    twoBitT variablec; //Two bits of C

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
        threeBitT variablec2_,
        twoBitT variablec_) :
        variablec2(variablec2_),
        variablec(variablec_)
    {}
    explicit seeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct dSt {
    fourBitT variabled2; //Four bits of D
    threeBitT variabled; //Three bits of D

    dSt() {}

    static constexpr uint16_t _bitWidth = 7;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const dSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const dSt & v, const std::string & NAME ) {
        sc_trace(tf,v.variabled, NAME + ".variabled");
        sc_trace(tf,v.variabled2, NAME + ".variabled2");
    }
    inline friend ostream& operator << ( ostream& os,  dSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<7> sc_pack(void) const;
    void sc_unpack(sc_bv<7> packed_data);
    explicit dSt(sc_bv<7> packed_data) { sc_unpack(packed_data); }
    explicit dSt(
        fourBitT variabled2_,
        threeBitT variabled_) :
        variabled2(variabled2_),
        variabled(variabled_)
    {}
    explicit dSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct eNestedSt {
    seeSt joe[2]; //Need two of these
    dSt bob; //
    aSizeT variablea; //One bit of A

    eNestedSt() {}

    static constexpr uint16_t _bitWidth = 18;
    static constexpr uint16_t _byteWidth = 3;
    typedef uint32_t _packedSt;
    bool operator == (const eNestedSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const eNestedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.variablea, NAME + ".variablea");
        sc_trace(tf,v.bob, NAME + ".bob");
        for(int i=0; i<2; i++) {
            sc_trace(tf,v.joe[i], NAME + ".joe[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  eNestedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<18> sc_pack(void) const;
    void sc_unpack(sc_bv<18> packed_data);
    explicit eNestedSt(sc_bv<18> packed_data) { sc_unpack(packed_data); }
    explicit eNestedSt(
        seeSt joe_[2],
        dSt bob_,
        aSizeT variablea_) :
        bob(bob_),
        variablea(variablea_)
    {
        memcpy(&joe, &joe_, sizeof(joe));
    }
    explicit eNestedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bSizeSt {
    bSizeT index; //

    bSizeSt() {}

    static constexpr uint16_t _bitWidth = 5;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const bSizeSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const bSizeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.index, NAME + ".index");
    }
    inline friend ostream& operator << ( ostream& os,  bSizeSt const & v ) {
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
    explicit bSizeSt(sc_bv<5> packed_data) { sc_unpack(packed_data); }
    explicit bSizeSt(
        bSizeT index_) :
        index(index_)
    {}
    explicit bSizeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct eHeaderSt {
    aBiggerT hdr; //

    eHeaderSt() {}

    static constexpr uint16_t _bitWidth = 2;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const eHeaderSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const eHeaderSt & v, const std::string & NAME ) {
        sc_trace(tf,v.hdr, NAME + ".hdr");
    }
    inline friend ostream& operator << ( ostream& os,  eHeaderSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<2> sc_pack(void) const;
    void sc_unpack(sc_bv<2> packed_data);
    explicit eHeaderSt(sc_bv<2> packed_data) { sc_unpack(packed_data); }
    explicit eHeaderSt(
        aBiggerT hdr_) :
        hdr(hdr_)
    {}
    explicit eHeaderSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END
#endif