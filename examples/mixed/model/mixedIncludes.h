#ifndef MIXEDINCLUDES_H
#define MIXEDINCLUDES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <cstdint>


// GENERATED_CODE_PARAM --context=mixed.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr
#include "mixedIncludeIncludes.h"
#include "mixedNestedIncludeIncludes.h"
#include "mixedBlockCIncludes.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t ASIZE = 1;  // The size of A
const uint32_t ASIZE2 = 2;  // The size of A+1
const uint32_t INTP = 4294966272;  // Test constant for numbers of unsigned integer type 
const int32_t INTN = -2147482624;  // Test constant for numbers of signed integer type (two's complement negative)
const uint64_t LONGP = 0X1FFFFFFFFFFFFC00UL;  // Test constant for numbers unsigned long type 
const int64_t LONGN = -0XFFFFFC00L;  // Test constant for numbers signed long type (two's complement negative)
const uint64_t BIGE33 = 0X1FFFFFFFFUL;  // Test constant for numbers slightly bigger than 32 bits
const uint64_t BIGE53 = 0X3FFFFFFFFFFFFFUL;  // Test constant for numbers slightly bigger than 32 bits
const uint64_t YUGE = 0X7FFFFFFFFFFFFFFFUL;  // Test constant for numbers of 63 bits
const uint32_t DWORD = 32;  // size of a double word
const uint32_t DWORD_LOG2 = 6;  // size of a double word log2
const uint32_t BOB0 = 16;  // Memory size for instance 0
const uint32_t BOB1 = 15;  // Memory size for instance 1
const uint32_t TESTCONST1 = 1;  // A test constant
const uint32_t TESTCONST2 = 6;  // A test constant using an enum value
const uint32_t OPCODEABASE_READ = 0;  // base value for Read command
const uint32_t OPCODEABASE_WRITE = 64;  // base value for Write command
const uint32_t OPCODEABASE_WAIT = 128;  // base value for Wait command
const uint32_t OPCODEABASE_EVICT = 192;  // base value for Evict command
const uint32_t OPCODEABASE_TRIM = 256;  // base value for Trim command

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types 
// types
typedef uint16_t opcodeTagT; // [9] opcode tag
typedef uint8_t twoBitT; // [2] this is a 2 bit type
typedef uint8_t threeBitT; // [3] this is a 3 bit type
typedef uint8_t fourBitT; // [4] this is a 4 bit type
typedef uint8_t sevenBitT; // [7] Used as a threeBitT plus a fourBitT for the register structure dRegSt
typedef uint8_t aSizeT; // [1] type of width ASIZE
typedef uint8_t aBiggerT; // [2] yet another type
typedef uint8_t bSizeT; // [4] for addressing memory
typedef uint16_t wordT; // [16] a word type, used for test
typedef uint32_t apbAddrT; // [32] for addressing register via APB
typedef uint32_t apbDataT; // [32] for the data sent or recieved via APB
typedef int8_t signedByte_t; // [8] Signed 8-bit type (-128 to 127)
typedef int16_t signedWord_t; // [16] Signed 16-bit type (-32768 to 32767)
typedef int32_t signedDword_t; // [32] Signed 32-bit type
typedef int8_t signedNibble_t; // [4] Signed 4-bit type (-8 to 7) for testing small signed values
typedef int8_t signed3bit_t; // [3] Signed 3-bit type (-4 to 3) non-byte-aligned
typedef int8_t signed5bit_t; // [5] Signed 5-bit type (-16 to 15) non-byte-aligned
typedef int8_t signed7bit_t; // [7] Signed 7-bit type (-64 to 63) non-byte-aligned
typedef int16_t signed11bit_t; // [11] Signed 11-bit type (-1024 to 1023) non-byte-aligned
typedef uint8_t unsigned5bit_t; // [5] Unsigned 5-bit type for mixed testing
typedef uint16_t unsigned9bit_t; // [9] Unsigned 9-bit type for mixed testing

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums 
// enums
enum  test1EnumT {           //a test enum
    TEST1_A=0,               // Test A
    TEST1_B=1,               // Test B
    TEST1_C=2 };             // Test C
inline const char* test1EnumT_prt( test1EnumT val )
{
    switch( val )
    {
        case TEST1_A: return( "TEST1_A" );
        case TEST1_B: return( "TEST1_B" );
        case TEST1_C: return( "TEST1_C" );
    }
    return("!!!BADENUM!!!");
}
enum  opcodeEnumT {          //Type of opcodeEnA (auto generated from encoder section)
    OPCODEATYPE_READ=0,      // Read command
    OPCODEATYPE_WRITE=1,     // Write command
    OPCODEATYPE_WAIT=2,      // Wait command
    OPCODEATYPE_EVICT=3,     // Evict command
    OPCODEATYPE_TRIM=4 };    // Trim command
inline const char* opcodeEnumT_prt( opcodeEnumT val )
{
    switch( val )
    {
        case OPCODEATYPE_READ: return( "OPCODEATYPE_READ" );
        case OPCODEATYPE_WRITE: return( "OPCODEATYPE_WRITE" );
        case OPCODEATYPE_WAIT: return( "OPCODEATYPE_WAIT" );
        case OPCODEATYPE_EVICT: return( "OPCODEATYPE_EVICT" );
        case OPCODEATYPE_TRIM: return( "OPCODEATYPE_TRIM" );
    }
    return("!!!BADENUM!!!");
}
enum  testEnumT {            //a test enum
    TEST_A=0,                // Test A
    TEST_B=5,                // Test B
    TEST_C=2 };              // Test C
inline const char* testEnumT_prt( testEnumT val )
{
    switch( val )
    {
        case TEST_A: return( "TEST_A" );
        case TEST_B: return( "TEST_B" );
        case TEST_C: return( "TEST_C" );
    }
    return("!!!BADENUM!!!");
}
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
enum  opcodeT {              //opcode with fixed width
    ADD=0,                   // Add
    SUB=5 };                 // Subtract
inline const char* opcodeT_prt( opcodeT val )
{
    switch( val )
    {
        case ADD: return( "ADD" );
        case SUB: return( "SUB" );
    }
    return("!!!BADENUM!!!");
}
enum  addr_id_top {          //Generated type for addressing top instances
    ADDR_ID_TOP_UBLOCKA=0,   // uBlockA instance address
    ADDR_ID_TOP_UBLOCKB=1 }; // uBlockB instance address
inline const char* addr_id_top_prt( addr_id_top val )
{
    switch( val )
    {
        case ADDR_ID_TOP_UBLOCKA: return( "ADDR_ID_TOP_UBLOCKA" );
        case ADDR_ID_TOP_UBLOCKB: return( "ADDR_ID_TOP_UBLOCKB" );
    }
    return("!!!BADENUM!!!");
}
enum  addr_id_ip1 {          //Generated type for addressing ip1 instances
    ADDR_ID_IP1_UBLOCKD=0,   // uBlockD instance address
    ADDR_ID_IP1_UBLOCKF0=2 }; // uBlockF0 instance address
inline const char* addr_id_ip1_prt( addr_id_ip1 val )
{
    switch( val )
    {
        case ADDR_ID_IP1_UBLOCKD: return( "ADDR_ID_IP1_UBLOCKD" );
        case ADDR_ID_IP1_UBLOCKF0: return( "ADDR_ID_IP1_UBLOCKF0" );
    }
    return("!!!BADENUM!!!");
}

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct aSt {
    twoBitT variablea2; //
    aSizeT variablea[ASIZE2]; //One bit of A

    aSt() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const aSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const aSt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<ASIZE2; i++) {
            sc_trace(tf,v.variablea[i], NAME + ".variablea[i]");
        }
        sc_trace(tf,v.variablea2, NAME + ".variablea2");
    }
    inline friend ostream& operator << ( ostream& os,  aSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<4> sc_pack(void) const;
    void sc_unpack(sc_bv<4> packed_data);
    explicit aSt(sc_bv<4> packed_data) { sc_unpack(packed_data); }
    explicit aSt(
        twoBitT variablea2_,
        aSizeT variablea_[ASIZE2]) :
        variablea2(variablea2_)
    {
        memcpy(&variablea, &variablea_, sizeof(variablea));
    }
    explicit aSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct aASt {
    aSizeT variablea; //One bit of A

    aASt() {}

    static constexpr uint16_t _bitWidth = 1;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const aASt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const aASt & v, const std::string & NAME ) {
        sc_trace(tf,v.variablea, NAME + ".variablea");
    }
    inline friend ostream& operator << ( ostream& os,  aASt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    bool sc_pack(void) const;
    void sc_unpack(bool packed_data);
    void sc_unpack(sc_bv<1> packed_data);
    explicit aASt(bool packed_data) { sc_unpack(packed_data); }
    explicit aASt(
        aSizeT variablea_) :
        variablea(variablea_)
    {}
    explicit aASt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct aRegSt {
    sevenBitT a; //

    aRegSt() {}

    static constexpr uint16_t _bitWidth = 7;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const aRegSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const aRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  aRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    // register functions
    inline int _size(void) {return( (7 + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( a & ((1ULL<<7 )-1) << 0);
        return( ret );
    }
    void _setValue(uint64_t value)
    {
        a = ( sevenBitT ) (( value >> 0 ) & (( (uint64_t)1 << 7 ) - 1)) ;
        }
    sc_bv<7> sc_pack(void) const;
    void sc_unpack(sc_bv<7> packed_data);
    explicit aRegSt(sc_bv<7> packed_data) { sc_unpack(packed_data); }
    explicit aRegSt(
        sevenBitT a_) :
        a(a_)
    {}
    explicit aRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct dRegSt {
    sevenBitT d; //

    dRegSt() {}

    static constexpr uint16_t _bitWidth = 7;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const dRegSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const dRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.d, NAME + ".d");
    }
    inline friend ostream& operator << ( ostream& os,  dRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    // register functions
    inline int _size(void) {return( (7 + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( d & ((1ULL<<7 )-1) << 0);
        return( ret );
    }
    void _setValue(uint64_t value)
    {
        d = ( sevenBitT ) (( value >> 0 ) & (( (uint64_t)1 << 7 ) - 1)) ;
        }
    sc_bv<7> sc_pack(void) const;
    void sc_unpack(sc_bv<7> packed_data);
    explicit dRegSt(sc_bv<7> packed_data) { sc_unpack(packed_data); }
    explicit dRegSt(
        sevenBitT d_) :
        d(d_)
    {}
    explicit dRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

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
    void unpack(const _packedSt &_src);
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
struct nestedSt {
    seeSt joe[2]; //Need two of these
    dSt bob; //
    aSizeT variablea; //One bit of A

    nestedSt() {}

    static constexpr uint16_t _bitWidth = 18;
    static constexpr uint16_t _byteWidth = 3;
    typedef uint32_t _packedSt;
    bool operator == (const nestedSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const nestedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.variablea, NAME + ".variablea");
        sc_trace(tf,v.bob, NAME + ".bob");
        for(unsigned int i=0; i<2; i++) {
            sc_trace(tf,v.joe[i], NAME + ".joe[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  nestedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<18> sc_pack(void) const;
    void sc_unpack(sc_bv<18> packed_data);
    explicit nestedSt(sc_bv<18> packed_data) { sc_unpack(packed_data); }
    explicit nestedSt(
        seeSt joe_[2],
        dSt bob_,
        aSizeT variablea_) :
        bob(bob_),
        variablea(variablea_)
    {
        memcpy(&joe, &joe_, sizeof(joe));
    }
    explicit nestedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bSizeRegSt {
    bSizeT index; //

    bSizeRegSt() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const bSizeRegSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const bSizeRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.index, NAME + ".index");
    }
    inline friend ostream& operator << ( ostream& os,  bSizeRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    // register functions
    inline int _size(void) {return( (4 + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( index & ((1ULL<<4 )-1) << 0);
        return( ret );
    }
    void _setValue(uint64_t value)
    {
        index = ( bSizeT ) (( value >> 0 ) & (( (uint64_t)1 << 4 ) - 1)) ;
        }
    sc_bv<4> sc_pack(void) const;
    void sc_unpack(sc_bv<4> packed_data);
    explicit bSizeRegSt(sc_bv<4> packed_data) { sc_unpack(packed_data); }
    explicit bSizeRegSt(
        bSizeT index_) :
        index(index_)
    {}
    explicit bSizeRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bSizeSt {
    bSizeT index; //

    bSizeSt() {}

    static constexpr uint16_t _bitWidth = 4;
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
    void unpack(const _packedSt &_src);
    sc_bv<4> sc_pack(void) const;
    void sc_unpack(sc_bv<4> packed_data);
    explicit bSizeSt(sc_bv<4> packed_data) { sc_unpack(packed_data); }
    explicit bSizeSt(
        bSizeT index_) :
        index(index_)
    {}
    explicit bSizeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct apbAddrSt {
    apbAddrT address; //

    apbAddrSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = 4;
    typedef uint32_t _packedSt;
    bool operator == (const apbAddrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const apbAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  apbAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline apbAddrT _getAddress(void) { return( address); }
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<32> sc_pack(void) const;
    void sc_unpack(sc_bv<32> packed_data);
    explicit apbAddrSt(sc_bv<32> packed_data) { sc_unpack(packed_data); }
    explicit apbAddrSt(
        apbAddrT address_) :
        address(address_)
    {}
    explicit apbAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct apbDataSt {
    apbDataT data; //

    apbDataSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = 4;
    typedef uint32_t _packedSt;
    bool operator == (const apbDataSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const apbDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  apbDataSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline apbDataT _getData(void) { return( data); }
    inline void _setData(apbDataT value) { data = value; }
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<32> sc_pack(void) const;
    void sc_unpack(sc_bv<32> packed_data);
    explicit apbDataSt(sc_bv<32> packed_data) { sc_unpack(packed_data); }
    explicit apbDataSt(
        apbDataT data_) :
        data(data_)
    {}
    explicit apbDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cSt {
    sevenBitT sevenBitArray[5]; //An array of total size > 32 bit and < 64 bits

    cSt() {}

    static constexpr uint16_t _bitWidth = 35;
    static constexpr uint16_t _byteWidth = 5;
    typedef uint64_t _packedSt;
    bool operator == (const cSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const cSt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.sevenBitArray[i], NAME + ".sevenBitArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  cSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<35> sc_pack(void) const;
    void sc_unpack(sc_bv<35> packed_data);
    explicit cSt(sc_bv<35> packed_data) { sc_unpack(packed_data); }
    explicit cSt(
        sevenBitT sevenBitArray_[5])
    {
        memcpy(&sevenBitArray, &sevenBitArray_, sizeof(sevenBitArray));
    }
    explicit cSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test1St {
    sevenBitT sevenBitArray2[5]; //An array of total size > 32 bit and < 64 bits
    sevenBitT sevenBitArray[5]; //An array of total size > 32 bit and < 64 bits

    test1St() {}

    static constexpr uint16_t _bitWidth = 70;
    static constexpr uint16_t _byteWidth = 9;
    typedef uint64_t _packedSt[2];
    bool operator == (const test1St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test1St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.sevenBitArray[i], NAME + ".sevenBitArray[i]");
        }
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.sevenBitArray2[i], NAME + ".sevenBitArray2[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test1St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<70> sc_pack(void) const;
    void sc_unpack(sc_bv<70> packed_data);
    explicit test1St(sc_bv<70> packed_data) { sc_unpack(packed_data); }
    explicit test1St(
        sevenBitT sevenBitArray2_[5],
        sevenBitT sevenBitArray_[5])
    {
        memcpy(&sevenBitArray2, &sevenBitArray2_, sizeof(sevenBitArray2));
        memcpy(&sevenBitArray, &sevenBitArray_, sizeof(sevenBitArray));
    }
    explicit test1St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test2St {
    cSt thirtyFiveBitArray[5]; //An array of 35 bit * 5

    test2St() {}

    static constexpr uint16_t _bitWidth = 175;
    static constexpr uint16_t _byteWidth = 22;
    typedef uint64_t _packedSt[3];
    bool operator == (const test2St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test2St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.thirtyFiveBitArray[i], NAME + ".thirtyFiveBitArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test2St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<175> sc_pack(void) const;
    void sc_unpack(sc_bv<175> packed_data);
    explicit test2St(sc_bv<175> packed_data) { sc_unpack(packed_data); }
    explicit test2St(
        cSt thirtyFiveBitArray_[5])
    {
        memcpy(&thirtyFiveBitArray, &thirtyFiveBitArray_, sizeof(thirtyFiveBitArray));
    }
    explicit test2St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test3St {
    aRegSt sevenBitArray[5]; //An array of 7 bit * 5

    test3St() {}

    static constexpr uint16_t _bitWidth = 35;
    static constexpr uint16_t _byteWidth = 5;
    typedef uint64_t _packedSt;
    bool operator == (const test3St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test3St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.sevenBitArray[i], NAME + ".sevenBitArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test3St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<35> sc_pack(void) const;
    void sc_unpack(sc_bv<35> packed_data);
    explicit test3St(sc_bv<35> packed_data) { sc_unpack(packed_data); }
    explicit test3St(
        aRegSt sevenBitArray_[5])
    {
        memcpy(&sevenBitArray, &sevenBitArray_, sizeof(sevenBitArray));
    }
    explicit test3St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test4St {
    aRegSt sevenBitArray; //An array of 7 bit

    test4St() {}

    static constexpr uint16_t _bitWidth = 7;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const test4St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test4St & v, const std::string & NAME ) {
        sc_trace(tf,v.sevenBitArray, NAME + ".sevenBitArray");
    }
    inline friend ostream& operator << ( ostream& os,  test4St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<7> sc_pack(void) const;
    void sc_unpack(sc_bv<7> packed_data);
    explicit test4St(sc_bv<7> packed_data) { sc_unpack(packed_data); }
    explicit test4St(
        aRegSt sevenBitArray_) :
        sevenBitArray(sevenBitArray_)
    {}
    explicit test4St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test5St {
    aRegSt sevenBitArray[10]; //An array of 7 bit * 10

    test5St() {}

    static constexpr uint16_t _bitWidth = 70;
    static constexpr uint16_t _byteWidth = 9;
    typedef uint64_t _packedSt[2];
    bool operator == (const test5St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test5St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<10; i++) {
            sc_trace(tf,v.sevenBitArray[i], NAME + ".sevenBitArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test5St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<70> sc_pack(void) const;
    void sc_unpack(sc_bv<70> packed_data);
    explicit test5St(sc_bv<70> packed_data) { sc_unpack(packed_data); }
    explicit test5St(
        aRegSt sevenBitArray_[10])
    {
        memcpy(&sevenBitArray, &sevenBitArray_, sizeof(sevenBitArray));
    }
    explicit test5St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test6St {
    test1St largeStruct; //An array of 70 bit

    test6St() {}

    static constexpr uint16_t _bitWidth = 70;
    static constexpr uint16_t _byteWidth = 9;
    typedef uint64_t _packedSt[2];
    bool operator == (const test6St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test6St & v, const std::string & NAME ) {
        sc_trace(tf,v.largeStruct, NAME + ".largeStruct");
    }
    inline friend ostream& operator << ( ostream& os,  test6St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<70> sc_pack(void) const;
    void sc_unpack(sc_bv<70> packed_data);
    explicit test6St(sc_bv<70> packed_data) { sc_unpack(packed_data); }
    explicit test6St(
        test1St largeStruct_) :
        largeStruct(largeStruct_)
    {}
    explicit test6St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test7St {
    test1St largeStruct[5]; //An array of 70 bit * 5

    test7St() {}

    static constexpr uint16_t _bitWidth = 350;
    static constexpr uint16_t _byteWidth = 44;
    typedef uint64_t _packedSt[6];
    bool operator == (const test7St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test7St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.largeStruct[i], NAME + ".largeStruct[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test7St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<350> sc_pack(void) const;
    void sc_unpack(sc_bv<350> packed_data);
    explicit test7St(sc_bv<350> packed_data) { sc_unpack(packed_data); }
    explicit test7St(
        test1St largeStruct_[5])
    {
        memcpy(&largeStruct, &largeStruct_, sizeof(largeStruct));
    }
    explicit test7St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test8St {
    wordT words[3]; //Aligned array of 3 words, each word is 16 bits

    test8St() {}

    static constexpr uint16_t _bitWidth = 48;
    static constexpr uint16_t _byteWidth = 6;
    typedef uint64_t _packedSt;
    bool operator == (const test8St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test8St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<3; i++) {
            sc_trace(tf,v.words[i], NAME + ".words[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test8St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<48> sc_pack(void) const;
    void sc_unpack(sc_bv<48> packed_data);
    explicit test8St(sc_bv<48> packed_data) { sc_unpack(packed_data); }
    explicit test8St(
        wordT words_[3])
    {
        memcpy(&words, &words_, sizeof(words));
    }
    explicit test8St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test9St {
    test8St wordArray[4]; //Array of 4 * 48 bits

    test9St() {}

    static constexpr uint16_t _bitWidth = 192;
    static constexpr uint16_t _byteWidth = 24;
    typedef uint64_t _packedSt[3];
    bool operator == (const test9St & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const test9St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<4; i++) {
            sc_trace(tf,v.wordArray[i], NAME + ".wordArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test9St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<192> sc_pack(void) const;
    void sc_unpack(sc_bv<192> packed_data);
    explicit test9St(sc_bv<192> packed_data) { sc_unpack(packed_data); }
    explicit test9St(
        test8St wordArray_[4])
    {
        memcpy(&wordArray, &wordArray_, sizeof(wordArray));
    }
    explicit test9St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct signedTestSt {
    twoBitT unsignedValue; //An unsigned two-bit value
    signedByte_t signedValue; //A signed byte value for testing

    signedTestSt() {}

    static constexpr uint16_t _bitWidth = 10;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const signedTestSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const signedTestSt & v, const std::string & NAME ) {
        sc_trace(tf,v.signedValue, NAME + ".signedValue");
        sc_trace(tf,v.unsignedValue, NAME + ".unsignedValue");
    }
    inline friend ostream& operator << ( ostream& os,  signedTestSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<10> sc_pack(void) const;
    void sc_unpack(sc_bv<10> packed_data);
    explicit signedTestSt(sc_bv<10> packed_data) { sc_unpack(packed_data); }
    explicit signedTestSt(
        twoBitT unsignedValue_,
        signedByte_t signedValue_) :
        unsignedValue(unsignedValue_),
        signedValue(signedValue_)
    {}
    explicit signedTestSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct mixedSignedSt {
    fourBitT flags; //Status flags
    signedByte_t offset; //Calibration offset
    signedWord_t temp; //Temperature sensor value

    mixedSignedSt() {}

    static constexpr uint16_t _bitWidth = 28;
    static constexpr uint16_t _byteWidth = 4;
    typedef uint32_t _packedSt;
    bool operator == (const mixedSignedSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const mixedSignedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.temp, NAME + ".temp");
        sc_trace(tf,v.offset, NAME + ".offset");
        sc_trace(tf,v.flags, NAME + ".flags");
    }
    inline friend ostream& operator << ( ostream& os,  mixedSignedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<28> sc_pack(void) const;
    void sc_unpack(sc_bv<28> packed_data);
    explicit mixedSignedSt(sc_bv<28> packed_data) { sc_unpack(packed_data); }
    explicit mixedSignedSt(
        fourBitT flags_,
        signedByte_t offset_,
        signedWord_t temp_) :
        flags(flags_),
        offset(offset_),
        temp(temp_)
    {}
    explicit mixedSignedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct signedArraySt {
    signedNibble_t values[3]; //Array of three signed nibbles

    signedArraySt() {}

    static constexpr uint16_t _bitWidth = 12;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const signedArraySt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const signedArraySt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<3; i++) {
            sc_trace(tf,v.values[i], NAME + ".values[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  signedArraySt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<12> sc_pack(void) const;
    void sc_unpack(sc_bv<12> packed_data);
    explicit signedArraySt(sc_bv<12> packed_data) { sc_unpack(packed_data); }
    explicit signedArraySt(
        signedNibble_t values_[3])
    {
        memcpy(&values, &values_, sizeof(values));
    }
    explicit signedArraySt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct nonByteAlignedSignedSt {
    threeBitT field4; //3-bit unsigned at bit 13-15
    signed5bit_t field3; //5-bit signed at bit 8-12
    unsigned5bit_t field2; //5-bit unsigned at bit 3-7
    signed3bit_t field1; //3-bit signed at bit 0-2

    nonByteAlignedSignedSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const nonByteAlignedSignedSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const nonByteAlignedSignedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.field1, NAME + ".field1");
        sc_trace(tf,v.field2, NAME + ".field2");
        sc_trace(tf,v.field3, NAME + ".field3");
        sc_trace(tf,v.field4, NAME + ".field4");
    }
    inline friend ostream& operator << ( ostream& os,  nonByteAlignedSignedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<16> sc_pack(void) const;
    void sc_unpack(sc_bv<16> packed_data);
    explicit nonByteAlignedSignedSt(sc_bv<16> packed_data) { sc_unpack(packed_data); }
    explicit nonByteAlignedSignedSt(
        threeBitT field4_,
        signed5bit_t field3_,
        unsigned5bit_t field2_,
        signed3bit_t field1_) :
        field4(field4_),
        field3(field3_),
        field2(field2_),
        field1(field1_)
    {}
    explicit nonByteAlignedSignedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct complexMixedSt {
    signedByte_t signedE; //8-bit signed field to cross 32-bit boundary
    fourBitT unsignedD; //4-bit unsigned field
    signed11bit_t signedC; //11-bit signed field
    unsigned9bit_t unsignedB; //9-bit unsigned field
    signed7bit_t signedA; //7-bit signed field

    complexMixedSt() {}

    static constexpr uint16_t _bitWidth = 39;
    static constexpr uint16_t _byteWidth = 5;
    typedef uint64_t _packedSt;
    bool operator == (const complexMixedSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const complexMixedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.signedA, NAME + ".signedA");
        sc_trace(tf,v.unsignedB, NAME + ".unsignedB");
        sc_trace(tf,v.signedC, NAME + ".signedC");
        sc_trace(tf,v.unsignedD, NAME + ".unsignedD");
        sc_trace(tf,v.signedE, NAME + ".signedE");
    }
    inline friend ostream& operator << ( ostream& os,  complexMixedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<39> sc_pack(void) const;
    void sc_unpack(sc_bv<39> packed_data);
    explicit complexMixedSt(sc_bv<39> packed_data) { sc_unpack(packed_data); }
    explicit complexMixedSt(
        signedByte_t signedE_,
        fourBitT unsignedD_,
        signed11bit_t signedC_,
        unsigned9bit_t unsignedB_,
        signed7bit_t signedA_) :
        signedE(signedE_),
        unsignedD(unsignedD_),
        signedC(signedC_),
        unsignedB(unsignedB_),
        signedA(signedA_)
    {}
    explicit complexMixedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct edgeCaseSignedSt {
    signedWord_t largeVal; //Large signed value
    signed11bit_t mediumVal; //Medium signed value
    signedNibble_t smallVal; //Small signed value
    signed3bit_t tiny; //Very small signed value

    edgeCaseSignedSt() {}

    static constexpr uint16_t _bitWidth = 34;
    static constexpr uint16_t _byteWidth = 5;
    typedef uint64_t _packedSt;
    bool operator == (const edgeCaseSignedSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const edgeCaseSignedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.tiny, NAME + ".tiny");
        sc_trace(tf,v.smallVal, NAME + ".smallVal");
        sc_trace(tf,v.mediumVal, NAME + ".mediumVal");
        sc_trace(tf,v.largeVal, NAME + ".largeVal");
    }
    inline friend ostream& operator << ( ostream& os,  edgeCaseSignedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<34> sc_pack(void) const;
    void sc_unpack(sc_bv<34> packed_data);
    explicit edgeCaseSignedSt(sc_bv<34> packed_data) { sc_unpack(packed_data); }
    explicit edgeCaseSignedSt(
        signedWord_t largeVal_,
        signed11bit_t mediumVal_,
        signedNibble_t smallVal_,
        signed3bit_t tiny_) :
        largeVal(largeVal_),
        mediumVal(mediumVal_),
        smallVal(smallVal_),
        tiny(tiny_)
    {}
    explicit edgeCaseSignedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct mixedArraySignedSt {
    unsigned5bit_t unsignedVals[3]; //Array of 3 non-byte-aligned unsigned values
    signed5bit_t signedVals[4]; //Array of 4 non-byte-aligned signed values

    mixedArraySignedSt() {}

    static constexpr uint16_t _bitWidth = 35;
    static constexpr uint16_t _byteWidth = 5;
    typedef uint64_t _packedSt;
    bool operator == (const mixedArraySignedSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const mixedArraySignedSt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<4; i++) {
            sc_trace(tf,v.signedVals[i], NAME + ".signedVals[i]");
        }
        for(unsigned int i=0; i<3; i++) {
            sc_trace(tf,v.unsignedVals[i], NAME + ".unsignedVals[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  mixedArraySignedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<35> sc_pack(void) const;
    void sc_unpack(sc_bv<35> packed_data);
    explicit mixedArraySignedSt(sc_bv<35> packed_data) { sc_unpack(packed_data); }
    explicit mixedArraySignedSt(
        unsigned5bit_t unsignedVals_[3],
        signed5bit_t signedVals_[4])
    {
        memcpy(&unsignedVals, &unsignedVals_, sizeof(unsignedVals));
        memcpy(&signedVals, &signedVals_, sizeof(signedVals));
    }
    explicit mixedArraySignedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
class test_mixed_structs {
public:
    static std::string name(void);
    static void test(void);
};

// GENERATED_CODE_END

#endif //MIXEDINCLUDES_H
