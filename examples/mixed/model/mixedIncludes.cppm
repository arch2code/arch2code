
// GENERATED_CODE_PARAM --context=mixed.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module mixed;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import mixedInclude;
import mixedNestedInclude;
import mixedBlockC;
using namespace mixedInclude_ns;
using namespace mixedNestedInclude_ns;
using namespace mixedBlockC_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace mixed_ns {
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
const double REAL_PI = 3.0;  // Test constant for floating point (real) type
const double REAL_HALF = 16.0;  // Test constant for real from eval expression
const uint32_t OPCODEABASE_READ = 0;  // base value for Read command
const uint32_t OPCODEABASE_WRITE = 64;  // base value for Write command
const uint32_t OPCODEABASE_WAIT = 128;  // base value for Wait command
const uint32_t OPCODEABASE_EVICT = 192;  // base value for Evict command
const uint32_t OPCODEABASE_TRIM = 256;  // base value for Trim command

} // namespace mixed_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace mixed_ns {
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
typedef uint32_t apbDataT; // [32] for the data sent or received via APB
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
typedef uint64_t bigT; // [64] 64-bit type for mixed testing
typedef uint64_t test37BitT; // [37] 37-bit type for testing non-power-of-2 memory address calculations (5 bytes, rounds to 8-byte stride)
typedef uint8_t bSizeCountT; // [4] Type wide enough to count 0..BSIZE (widthLog2 with constant)
typedef uint8_t bSizeIndexT; // [4] Type wide enough to index 0..BSIZE-1 (widthLog2minus1 with constant)
typedef uint8_t log2LiteralT; // [5] Type wide enough to count 0..16 using widthLog2 with literal (5 bits)
typedef uint8_t log2minus1LiteralT; // [3] Type wide enough to index 0..7 using widthLog2minus1 with literal (3 bits)
typedef int8_t signedLog2T; // [5] Signed type using widthLog2 — gets +1 bit for sign

} // namespace mixed_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace mixed_ns {
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

} // namespace mixed_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace mixed_ns {
// structures
struct aSt {
    twoBitT variablea2; //
    aSizeT variablea[ASIZE2]; //One bit of A

    aSt() {}

    static constexpr uint16_t _bitWidth = 2 + ASIZE*ASIZE2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const aSt & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<ASIZE2; i++) {
            ret = ret && (variablea[i] == rhs.variablea[i]);
        }
        ret = ret && (variablea2 == rhs.variablea2);
        return ( ret );
        }
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
    std::string prt(bool all=false) const
    {
        return (std::format("variablea[0:1]: {} variablea2:0x{:01x}",
           staticArrayPrt<aSizeT, ASIZE2>(variablea, all),
           (uint64_t) variablea2
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aSt::_byteWidth);
        _ret = variablea2;
        uint16_t _pos{2};
        for(unsigned int i=0; i<ASIZE2; i++) {
            pack_bits((uint64_t *)&_ret, _pos, variablea[i], ASIZE);
            _pos += ASIZE;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        variablea2 = (twoBitT)((_src >> (_pos & 7)) & ((1ULL << 2) - 1));
        _pos += 2;
        for(unsigned int i=0; i<ASIZE2; i++) {
            uint16_t _bits = ASIZE;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(8-(_pos & 7)));
            variablea[i] = (aSizeT)((_src >> (_pos & 7)) & 1);
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 8)) {
                variablea[i] = (aSizeT)(variablea[i] | ((_src << _consume) & 1));
                _pos += _bits;
            }
        }
    }
    inline sc_bv<aSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<aSt::_bitWidth> packed_data;
        packed_data.range(1, 0) = variablea2;
        for(unsigned int i=0; i<ASIZE2; i++) {
            packed_data.range(2+(i+1)*ASIZE-1, 2+i*ASIZE) = variablea[i];
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<aSt::_bitWidth> packed_data)
    {
        variablea2 = (twoBitT) packed_data.range(1, 0).to_uint64();
        for(unsigned int i=0; i<ASIZE2; i++) {
            variablea[i] = (aSizeT) packed_data.range(2+(i+1)*ASIZE-1, 2+i*ASIZE).to_uint64();
        }
    }
    explicit aSt(sc_bv<aSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = ASIZE;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const aASt & rhs) const {
        bool ret = true;
        ret = ret && (variablea == rhs.variablea);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const aASt & v, const std::string & NAME ) {
        sc_trace(tf,v.variablea, NAME + ".variablea");
    }
    inline friend ostream& operator << ( ostream& os,  aASt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("variablea:0x{:01x}",
           (uint64_t) variablea
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aASt::_byteWidth);
        _ret = variablea;
    }
    inline void unpack(const _packedSt &_src)
    {
        variablea = (aSizeT)((_src) & 1);
    }
    inline bool sc_pack(void) const
    {
        bool packed_data;
        packed_data = (bool) variablea;
        return packed_data;
    }
    inline void sc_unpack(bool packed_data)
    {
        variablea = (aSizeT) packed_data;
    }
    inline void sc_unpack(sc_bv<aASt::_bitWidth> packed_data)
    {
        variablea = (aSizeT) packed_data.range(0, 0).to_uint64();
    }
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
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const aRegSt & rhs) const {
        bool ret = true;
        ret = ret && (a == rhs.a);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const aRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  aRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("a:0x{:02x}",
           (uint64_t) a
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aRegSt::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (sevenBitT)((_src) & ((1ULL << 7) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
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
    inline sc_bv<aRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<aRegSt::_bitWidth> packed_data;
        packed_data.range(6, 0) = a;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<aRegSt::_bitWidth> packed_data)
    {
        a = (sevenBitT) packed_data.range(6, 0).to_uint64();
    }
    explicit aRegSt(sc_bv<aRegSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const dRegSt & rhs) const {
        bool ret = true;
        ret = ret && (d == rhs.d);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const dRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.d, NAME + ".d");
    }
    inline friend ostream& operator << ( ostream& os,  dRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("d:0x{:02x}",
           (uint64_t) d
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, dRegSt::_byteWidth);
        _ret = d;
    }
    inline void unpack(const _packedSt &_src)
    {
        d = (sevenBitT)((_src) & ((1ULL << 7) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
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
    inline sc_bv<dRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<dRegSt::_bitWidth> packed_data;
        packed_data.range(6, 0) = d;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<dRegSt::_bitWidth> packed_data)
    {
        d = (sevenBitT) packed_data.range(6, 0).to_uint64();
    }
    explicit dRegSt(sc_bv<dRegSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 4 + 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const dSt & rhs) const {
        bool ret = true;
        ret = ret && (variabled == rhs.variabled);
        ret = ret && (variabled2 == rhs.variabled2);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const dSt & v, const std::string & NAME ) {
        sc_trace(tf,v.variabled, NAME + ".variabled");
        sc_trace(tf,v.variabled2, NAME + ".variabled2");
    }
    inline friend ostream& operator << ( ostream& os,  dSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("variabled:0x{:01x} variabled2:0x{:01x}",
           (uint64_t) variabled,
           (uint64_t) variabled2
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, dSt::_byteWidth);
        _ret = variabled2;
        _ret |= (uint8_t)variabled << (4 & 7);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        variabled2 = (fourBitT)((_src >> (_pos & 7)) & ((1ULL << 4) - 1));
        _pos += 4;
        variabled = (threeBitT)((_src >> (_pos & 7)) & ((1ULL << 3) - 1));
    }
    inline sc_bv<dSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<dSt::_bitWidth> packed_data;
        packed_data.range(3, 0) = variabled2;
        packed_data.range(6, 4) = variabled;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<dSt::_bitWidth> packed_data)
    {
        variabled2 = (fourBitT) packed_data.range(3, 0).to_uint64();
        variabled = (threeBitT) packed_data.range(6, 4).to_uint64();
    }
    explicit dSt(sc_bv<dSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit dSt(
        fourBitT variabled2_,
        threeBitT variabled_) :
        variabled2(variabled2_),
        variabled(variabled_)
    {}
    explicit dSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bigSt {
    bigT big; //

    bigSt() {}

    static constexpr uint16_t _bitWidth = 64;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const bigSt & rhs) const {
        bool ret = true;
        ret = ret && (big == rhs.big);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bigSt & v, const std::string & NAME ) {
        sc_trace(tf,v.big, NAME + ".big");
    }
    inline friend ostream& operator << ( ostream& os,  bigSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("big:0x{:016x}",
           (uint64_t) big
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, bigSt::_byteWidth);
        _ret = big;
    }
    inline void unpack(const _packedSt &_src)
    {
        big = (bigT)((_src));
    }
    inline sc_bv<bigSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bigSt::_bitWidth> packed_data;
        packed_data.range(63, 0) = big;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bigSt::_bitWidth> packed_data)
    {
        big = (bigT) packed_data.range(63, 0).to_uint64();
    }
    explicit bigSt(sc_bv<bigSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bigSt(
        bigT big_) :
        big(big_)
    {}
    explicit bigSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct nestedSt {
    seeSt joe[2]; //Need two of these
    dSt bob; //
    aSizeT variablea; //One bit of A

    nestedSt() {}

    static constexpr uint16_t _bitWidth = seeSt::_bitWidth*2 + dSt::_bitWidth + ASIZE;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const nestedSt & rhs) const {
        bool ret = true;
        ret = ret && (variablea == rhs.variablea);
        ret = ret && (bob == rhs.bob);
        for(unsigned int i=0; i<2; i++) {
            ret = ret && (joe[i] == rhs.joe[i]);
        }
        return ( ret );
        }
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
    std::string prt(bool all=false) const
    {
        return (std::format("variablea:0x{:01x} bob:<{}>{}",
           (uint64_t) variablea,
           bob.prt(all),
           structArrayPrt<seeSt, 2>(joe, "joe", all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, nestedSt::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<2; i++) {
            seeSt::_packedSt _tmp{0};
            joe[i].pack(_tmp);
            _ret |= (uint32_t)_tmp << (_pos & 31);
            _pos += seeSt::_bitWidth;
        }
        {
            dSt::_packedSt _tmp{0};
            bob.pack(_tmp);
            _ret |= (uint32_t)_tmp << (10 & 31);
        }
        _ret |= (uint32_t)variablea << (17 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<2; i++) {
            uint16_t _bits = seeSt::_bitWidth;
            uint16_t _consume;
            {
                uint64_t _tmp{0};
                _tmp = (_src >> _pos) & ((1ULL << seeSt::_bitWidth) - 1);
                joe[i].unpack(*((seeSt::_packedSt*)&_tmp));
            }
            _pos += seeSt::_bitWidth;
        }
        {
            uint64_t _tmp{0};
            _tmp = (_src >> _pos) & ((1ULL << dSt::_bitWidth) - 1);
            bob.unpack(*((dSt::_packedSt*)&_tmp));
        }
        _pos += dSt::_bitWidth;
        variablea = (aSizeT)((_src >> (_pos & 31)) & 1);
    }
    inline sc_bv<nestedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<nestedSt::_bitWidth> packed_data;
        for(unsigned int i=0; i<2; i++) {
            packed_data.range(0+(i+1)*seeSt::_bitWidth-1, 0+i*seeSt::_bitWidth) = joe[i].sc_pack();
        }
        packed_data.range(16, 10) = bob.sc_pack();
        packed_data.range(17, 17) = variablea;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<nestedSt::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<2; i++) {
            joe[i].sc_unpack(packed_data.range(0+(i+1)*seeSt::_bitWidth-1, 0+i*seeSt::_bitWidth));
        }
        bob.sc_unpack(packed_data.range(16, 10));
        variablea = (aSizeT) packed_data.range(17, 17).to_uint64();
    }
    explicit nestedSt(sc_bv<nestedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = BSIZE_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const bSizeRegSt & rhs) const {
        bool ret = true;
        ret = ret && (index == rhs.index);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bSizeRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.index, NAME + ".index");
    }
    inline friend ostream& operator << ( ostream& os,  bSizeRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("index:0x{:01x}",
           (uint64_t) index
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, bSizeRegSt::_byteWidth);
        _ret = index;
    }
    inline void unpack(const _packedSt &_src)
    {
        index = (bSizeT)((_src) & ((1ULL << 4) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
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
    inline sc_bv<bSizeRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bSizeRegSt::_bitWidth> packed_data;
        packed_data.range(3, 0) = index;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bSizeRegSt::_bitWidth> packed_data)
    {
        index = (bSizeT) packed_data.range(3, 0).to_uint64();
    }
    explicit bSizeRegSt(sc_bv<bSizeRegSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bSizeRegSt(
        bSizeT index_) :
        index(index_)
    {}
    explicit bSizeRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bSizeSt {
    bSizeT index; //

    bSizeSt() {}

    static constexpr uint16_t _bitWidth = BSIZE_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const bSizeSt & rhs) const {
        bool ret = true;
        ret = ret && (index == rhs.index);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bSizeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.index, NAME + ".index");
    }
    inline friend ostream& operator << ( ostream& os,  bSizeSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("index:0x{:01x}",
           (uint64_t) index
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline bSizeT _getAddress(void) { return( index); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, bSizeSt::_byteWidth);
        _ret = index;
    }
    inline void unpack(const _packedSt &_src)
    {
        index = (bSizeT)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<bSizeSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bSizeSt::_bitWidth> packed_data;
        packed_data.range(3, 0) = index;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bSizeSt::_bitWidth> packed_data)
    {
        index = (bSizeT) packed_data.range(3, 0).to_uint64();
    }
    explicit bSizeSt(sc_bv<bSizeSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bSizeSt(
        bSizeT index_) :
        index(index_)
    {}
    explicit bSizeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct apbAddrSt {
    apbAddrT address; //

    apbAddrSt() {}

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const apbAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const apbAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  apbAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("address:0x{:08x}",
           (uint64_t) address
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline apbAddrT _getAddress(void) { return( address); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, apbAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (apbAddrT)((_src));
    }
    inline sc_bv<apbAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<apbAddrSt::_bitWidth> packed_data;
        packed_data.range(31, 0) = address;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<apbAddrSt::_bitWidth> packed_data)
    {
        address = (apbAddrT) packed_data.range(31, 0).to_uint64();
    }
    explicit apbAddrSt(sc_bv<apbAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit apbAddrSt(
        apbAddrT address_) :
        address(address_)
    {}
    explicit apbAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct apbDataSt {
    apbDataT data; //

    apbDataSt() {}

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const apbDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const apbDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  apbDataSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:08x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline apbDataT _getData(void) { return( data); }
    inline void _setData(apbDataT value) { data = value; }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, apbDataSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (apbDataT)((_src));
    }
    inline sc_bv<apbDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<apbDataSt::_bitWidth> packed_data;
        packed_data.range(31, 0) = data;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<apbDataSt::_bitWidth> packed_data)
    {
        data = (apbDataT) packed_data.range(31, 0).to_uint64();
    }
    explicit apbDataSt(sc_bv<apbDataSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit apbDataSt(
        apbDataT data_) :
        data(data_)
    {}
    explicit apbDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cSt {
    sevenBitT sevenBitArray[5]; //An array of total size > 32 bit and < 64 bits

    cSt() {}

    static constexpr uint16_t _bitWidth = 7*5;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const cSt & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<5; i++) {
            ret = ret && (sevenBitArray[i] == rhs.sevenBitArray[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cSt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.sevenBitArray[i], NAME + ".sevenBitArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  cSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("sevenBitArray[0:4]: {}",
           staticArrayPrt<sevenBitT, 5>(sevenBitArray, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, cSt::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            pack_bits((uint64_t *)&_ret, _pos, sevenBitArray[i], 7);
            _pos += 7;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            uint16_t _bits = 7;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            sevenBitArray[i] = (sevenBitT)((_src >> (_pos & 63)) & ((1ULL << 7) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                sevenBitArray[i] = (sevenBitT)(sevenBitArray[i] | ((_src << _consume) & ((1ULL << 7) - 1)));
                _pos += _bits;
            }
        }
    }
    inline sc_bv<cSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<cSt::_bitWidth> packed_data;
        for(unsigned int i=0; i<5; i++) {
            packed_data.range(0+(i+1)*7-1, 0+i*7) = sevenBitArray[i];
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<cSt::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<5; i++) {
            sevenBitArray[i] = (sevenBitT) packed_data.range(0+(i+1)*7-1, 0+i*7).to_uint64();
        }
    }
    explicit cSt(sc_bv<cSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 7*5 + 7*5;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const test1St & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<5; i++) {
            ret = ret && (sevenBitArray[i] == rhs.sevenBitArray[i]);
        }
        for(unsigned int i=0; i<5; i++) {
            ret = ret && (sevenBitArray2[i] == rhs.sevenBitArray2[i]);
        }
        return ( ret );
        }
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
    std::string prt(bool all=false) const
    {
        return (std::format("sevenBitArray[0:4]: {} sevenBitArray2[0:4]: {}",
           staticArrayPrt<sevenBitT, 5>(sevenBitArray, all),
           staticArrayPrt<sevenBitT, 5>(sevenBitArray2, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test1St::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            pack_bits((uint64_t *)&_ret, _pos, sevenBitArray2[i], 7);
            _pos += 7;
        }
        for(unsigned int i=0; i<5; i++) {
            pack_bits((uint64_t *)&_ret, _pos, sevenBitArray[i], 7);
            _pos += 7;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            uint16_t _bits = 7;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            sevenBitArray2[i] = (sevenBitT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 7) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                sevenBitArray2[i] = (sevenBitT)(sevenBitArray2[i] | ((_src[ _pos >> 6 ] << _consume) & ((1ULL << 7) - 1)));
                _pos += _bits;
            }
        }
        for(unsigned int i=0; i<5; i++) {
            uint16_t _bits = 7;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            sevenBitArray[i] = (sevenBitT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 7) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                sevenBitArray[i] = (sevenBitT)(sevenBitArray[i] | ((_src[ _pos >> 6 ] << _consume) & ((1ULL << 7) - 1)));
                _pos += _bits;
            }
        }
    }
    inline sc_bv<test1St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test1St::_bitWidth> packed_data;
        for(unsigned int i=0; i<5; i++) {
            packed_data.range(0+(i+1)*7-1, 0+i*7) = sevenBitArray2[i];
        }
        for(unsigned int i=0; i<5; i++) {
            packed_data.range(35+(i+1)*7-1, 35+i*7) = sevenBitArray[i];
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test1St::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<5; i++) {
            sevenBitArray2[i] = (sevenBitT) packed_data.range(0+(i+1)*7-1, 0+i*7).to_uint64();
        }
        for(unsigned int i=0; i<5; i++) {
            sevenBitArray[i] = (sevenBitT) packed_data.range(35+(i+1)*7-1, 35+i*7).to_uint64();
        }
    }
    explicit test1St(sc_bv<test1St::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = cSt::_bitWidth*5;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline bool operator == (const test2St & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<5; i++) {
            ret = ret && (thirtyFiveBitArray[i] == rhs.thirtyFiveBitArray[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test2St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.thirtyFiveBitArray[i], NAME + ".thirtyFiveBitArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test2St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("{}",
           structArrayPrt<cSt, 5>(thirtyFiveBitArray, "thirtyFiveBitArray", all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test2St::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            cSt::_packedSt _tmp{0};
            thirtyFiveBitArray[i].pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, _tmp, cSt::_bitWidth);
            _pos += cSt::_bitWidth;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            uint16_t _bits = cSt::_bitWidth;
            uint16_t _consume;
            {
                cSt::_packedSt _tmp{0};
                unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, cSt::_bitWidth);
                thirtyFiveBitArray[i].unpack(_tmp);
            }
            _pos += cSt::_bitWidth;
        }
    }
    inline sc_bv<test2St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test2St::_bitWidth> packed_data;
        for(unsigned int i=0; i<5; i++) {
            packed_data.range(0+(i+1)*cSt::_bitWidth-1, 0+i*cSt::_bitWidth) = thirtyFiveBitArray[i].sc_pack();
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test2St::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<5; i++) {
            thirtyFiveBitArray[i].sc_unpack(packed_data.range(0+(i+1)*cSt::_bitWidth-1, 0+i*cSt::_bitWidth));
        }
    }
    explicit test2St(sc_bv<test2St::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = aRegSt::_bitWidth*5;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const test3St & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<5; i++) {
            ret = ret && (sevenBitArray[i] == rhs.sevenBitArray[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test3St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.sevenBitArray[i], NAME + ".sevenBitArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test3St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("{}",
           structArrayPrt<aRegSt, 5>(sevenBitArray, "sevenBitArray", all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test3St::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            aRegSt::_packedSt _tmp{0};
            sevenBitArray[i].pack(_tmp);
            _ret |= (uint64_t)_tmp << (_pos & 63);
            _pos += aRegSt::_bitWidth;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            uint16_t _bits = aRegSt::_bitWidth;
            uint16_t _consume;
            {
                uint64_t _tmp{0};
                _tmp = (_src >> _pos) & ((1ULL << aRegSt::_bitWidth) - 1);
                sevenBitArray[i].unpack(*((aRegSt::_packedSt*)&_tmp));
            }
            _pos += aRegSt::_bitWidth;
        }
    }
    inline sc_bv<test3St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test3St::_bitWidth> packed_data;
        for(unsigned int i=0; i<5; i++) {
            packed_data.range(0+(i+1)*aRegSt::_bitWidth-1, 0+i*aRegSt::_bitWidth) = sevenBitArray[i].sc_pack();
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test3St::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<5; i++) {
            sevenBitArray[i].sc_unpack(packed_data.range(0+(i+1)*aRegSt::_bitWidth-1, 0+i*aRegSt::_bitWidth));
        }
    }
    explicit test3St(sc_bv<test3St::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = aRegSt::_bitWidth;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const test4St & rhs) const {
        bool ret = true;
        ret = ret && (sevenBitArray == rhs.sevenBitArray);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test4St & v, const std::string & NAME ) {
        sc_trace(tf,v.sevenBitArray, NAME + ".sevenBitArray");
    }
    inline friend ostream& operator << ( ostream& os,  test4St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("sevenBitArray:<{}>",
           sevenBitArray.prt(all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test4St::_byteWidth);
        {
            sevenBitArray.pack(*(aRegSt::_packedSt*)&_ret);
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        {
            sevenBitArray.unpack(*(aRegSt::_packedSt*)&_src);
        }
    }
    inline sc_bv<test4St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test4St::_bitWidth> packed_data;
        packed_data.range(6, 0) = sevenBitArray.sc_pack();
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test4St::_bitWidth> packed_data)
    {
        sevenBitArray.sc_unpack(packed_data.range(6, 0));
    }
    explicit test4St(sc_bv<test4St::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit test4St(
        aRegSt sevenBitArray_) :
        sevenBitArray(sevenBitArray_)
    {}
    explicit test4St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test5St {
    aRegSt sevenBitArray[10]; //An array of 7 bit * 10

    test5St() {}

    static constexpr uint16_t _bitWidth = aRegSt::_bitWidth*10;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const test5St & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<10; i++) {
            ret = ret && (sevenBitArray[i] == rhs.sevenBitArray[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test5St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<10; i++) {
            sc_trace(tf,v.sevenBitArray[i], NAME + ".sevenBitArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test5St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("{}",
           structArrayPrt<aRegSt, 10>(sevenBitArray, "sevenBitArray", all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test5St::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<10; i++) {
            aRegSt::_packedSt _tmp{0};
            sevenBitArray[i].pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, _tmp, aRegSt::_bitWidth);
            _pos += aRegSt::_bitWidth;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<10; i++) {
            uint16_t _bits = aRegSt::_bitWidth;
            uint16_t _consume;
            {
                uint64_t _tmp{0};
                unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, aRegSt::_bitWidth);
                sevenBitArray[i].unpack(*((aRegSt::_packedSt*)&_tmp));
            }
            _pos += aRegSt::_bitWidth;
        }
    }
    inline sc_bv<test5St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test5St::_bitWidth> packed_data;
        for(unsigned int i=0; i<10; i++) {
            packed_data.range(0+(i+1)*aRegSt::_bitWidth-1, 0+i*aRegSt::_bitWidth) = sevenBitArray[i].sc_pack();
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test5St::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<10; i++) {
            sevenBitArray[i].sc_unpack(packed_data.range(0+(i+1)*aRegSt::_bitWidth-1, 0+i*aRegSt::_bitWidth));
        }
    }
    explicit test5St(sc_bv<test5St::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = test1St::_bitWidth;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const test6St & rhs) const {
        bool ret = true;
        ret = ret && (largeStruct == rhs.largeStruct);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test6St & v, const std::string & NAME ) {
        sc_trace(tf,v.largeStruct, NAME + ".largeStruct");
    }
    inline friend ostream& operator << ( ostream& os,  test6St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("largeStruct:<{}>",
           largeStruct.prt(all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test6St::_byteWidth);
        {
            largeStruct.pack(*(test1St::_packedSt*)&_ret[ 0 ]);
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        {
            largeStruct.unpack(*(test1St::_packedSt*)&_src[ _pos >> 6 ]);
        }
    }
    inline sc_bv<test6St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test6St::_bitWidth> packed_data;
        packed_data.range(69, 0) = largeStruct.sc_pack();
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test6St::_bitWidth> packed_data)
    {
        largeStruct.sc_unpack(packed_data.range(69, 0));
    }
    explicit test6St(sc_bv<test6St::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit test6St(
        test1St largeStruct_) :
        largeStruct(largeStruct_)
    {}
    explicit test6St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test7St {
    test1St largeStruct[5]; //An array of 70 bit * 5

    test7St() {}

    static constexpr uint16_t _bitWidth = test1St::_bitWidth*5;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[6];
    inline bool operator == (const test7St & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<5; i++) {
            ret = ret && (largeStruct[i] == rhs.largeStruct[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test7St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<5; i++) {
            sc_trace(tf,v.largeStruct[i], NAME + ".largeStruct[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test7St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("{}",
           structArrayPrt<test1St, 5>(largeStruct, "largeStruct", all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test7St::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            test1St::_packedSt _tmp{0};
            largeStruct[i].pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&_tmp, test1St::_bitWidth);
            _pos += test1St::_bitWidth;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<5; i++) {
            uint16_t _bits = test1St::_bitWidth;
            uint16_t _consume;
            {
                test1St::_packedSt _tmp{0};
                unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, test1St::_bitWidth);
                largeStruct[i].unpack(_tmp);
            }
            _pos += test1St::_bitWidth;
        }
    }
    inline sc_bv<test7St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test7St::_bitWidth> packed_data;
        for(unsigned int i=0; i<5; i++) {
            packed_data.range(0+(i+1)*test1St::_bitWidth-1, 0+i*test1St::_bitWidth) = largeStruct[i].sc_pack();
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test7St::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<5; i++) {
            largeStruct[i].sc_unpack(packed_data.range(0+(i+1)*test1St::_bitWidth-1, 0+i*test1St::_bitWidth));
        }
    }
    explicit test7St(sc_bv<test7St::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 16*3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const test8St & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<3; i++) {
            ret = ret && (words[i] == rhs.words[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test8St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<3; i++) {
            sc_trace(tf,v.words[i], NAME + ".words[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test8St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("words[0:2]: {}",
           staticArrayPrt<wordT, 3>(words, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test8St::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            pack_bits((uint64_t *)&_ret, _pos, words[i], 16);
            _pos += 16;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            uint16_t _bits = 16;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            words[i] = (wordT)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                words[i] = (wordT)(words[i] | ((_src << _consume) & ((1ULL << 16) - 1)));
                _pos += _bits;
            }
        }
    }
    inline sc_bv<test8St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test8St::_bitWidth> packed_data;
        for(unsigned int i=0; i<3; i++) {
            packed_data.range(0+(i+1)*16-1, 0+i*16) = words[i];
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test8St::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<3; i++) {
            words[i] = (wordT) packed_data.range(0+(i+1)*16-1, 0+i*16).to_uint64();
        }
    }
    explicit test8St(sc_bv<test8St::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = test8St::_bitWidth*4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline bool operator == (const test9St & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<4; i++) {
            ret = ret && (wordArray[i] == rhs.wordArray[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test9St & v, const std::string & NAME ) {
        for(unsigned int i=0; i<4; i++) {
            sc_trace(tf,v.wordArray[i], NAME + ".wordArray[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  test9St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("{}",
           structArrayPrt<test8St, 4>(wordArray, "wordArray", all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test9St::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<4; i++) {
            test8St::_packedSt _tmp{0};
            wordArray[i].pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, _tmp, test8St::_bitWidth);
            _pos += test8St::_bitWidth;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<4; i++) {
            uint16_t _bits = test8St::_bitWidth;
            uint16_t _consume;
            {
                test8St::_packedSt _tmp{0};
                unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, test8St::_bitWidth);
                wordArray[i].unpack(_tmp);
            }
            _pos += test8St::_bitWidth;
        }
    }
    inline sc_bv<test9St::_bitWidth> sc_pack(void) const
    {
        sc_bv<test9St::_bitWidth> packed_data;
        for(unsigned int i=0; i<4; i++) {
            packed_data.range(0+(i+1)*test8St::_bitWidth-1, 0+i*test8St::_bitWidth) = wordArray[i].sc_pack();
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test9St::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<4; i++) {
            wordArray[i].sc_unpack(packed_data.range(0+(i+1)*test8St::_bitWidth-1, 0+i*test8St::_bitWidth));
        }
    }
    explicit test9St(sc_bv<test9St::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 2 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const signedTestSt & rhs) const {
        bool ret = true;
        ret = ret && (signedValue == rhs.signedValue);
        ret = ret && (unsignedValue == rhs.unsignedValue);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const signedTestSt & v, const std::string & NAME ) {
        sc_trace(tf,v.signedValue, NAME + ".signedValue");
        sc_trace(tf,v.unsignedValue, NAME + ".unsignedValue");
    }
    inline friend ostream& operator << ( ostream& os,  signedTestSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("signedValue:0x{:02x} unsignedValue:0x{:01x}",
           (uint64_t) signedValue,
           (uint64_t) unsignedValue
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, signedTestSt::_byteWidth);
        _ret = unsignedValue;
        _ret |= ((uint16_t)(signedValue & ((1ULL << 8) - 1))) << (2 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        unsignedValue = (twoBitT)((_src >> (_pos & 15)) & ((1ULL << 2) - 1));
        _pos += 2;
        signedValue = (signedByte_t)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
        _pos += 8;
        // Sign extension for signed type
        if (signedValue & (1ULL << (8 - 1))) {
            signedValue = (signedByte_t)(signedValue | ~((1ULL << 8) - 1));
        }
    }
    inline sc_bv<signedTestSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<signedTestSt::_bitWidth> packed_data;
        packed_data.range(1, 0) = unsignedValue;
        packed_data.range(9, 2) = signedValue;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<signedTestSt::_bitWidth> packed_data)
    {
        unsignedValue = (twoBitT) packed_data.range(1, 0).to_uint64();
        signedValue = (signedByte_t) packed_data.range(9, 2).to_uint64();
        // Sign extension for signed type
        if (signedValue & (1ULL << (8 - 1))) {
            signedValue = (signedByte_t)(signedValue | ~((1ULL << 8) - 1));
        }
    }
    explicit signedTestSt(sc_bv<signedTestSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 4 + 8 + 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const mixedSignedSt & rhs) const {
        bool ret = true;
        ret = ret && (temp == rhs.temp);
        ret = ret && (offset == rhs.offset);
        ret = ret && (flags == rhs.flags);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const mixedSignedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.temp, NAME + ".temp");
        sc_trace(tf,v.offset, NAME + ".offset");
        sc_trace(tf,v.flags, NAME + ".flags");
    }
    inline friend ostream& operator << ( ostream& os,  mixedSignedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("temp:0x{:04x} offset:0x{:02x} flags:0x{:01x}",
           (uint64_t) temp,
           (uint64_t) offset,
           (uint64_t) flags
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, mixedSignedSt::_byteWidth);
        _ret = flags;
        _ret |= ((uint32_t)(offset & ((1ULL << 8) - 1))) << (4 & 31);
        _ret |= ((uint32_t)(temp & ((1ULL << 16) - 1))) << (12 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        flags = (fourBitT)((_src >> (_pos & 31)) & ((1ULL << 4) - 1));
        _pos += 4;
        offset = (signedByte_t)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
        _pos += 8;
        // Sign extension for signed type
        if (offset & (1ULL << (8 - 1))) {
            offset = (signedByte_t)(offset | ~((1ULL << 8) - 1));
        }
        temp = (signedWord_t)((_src >> (_pos & 31)) & ((1ULL << 16) - 1));
        _pos += 16;
        // Sign extension for signed type
        if (temp & (1ULL << (16 - 1))) {
            temp = (signedWord_t)(temp | ~((1ULL << 16) - 1));
        }
    }
    inline sc_bv<mixedSignedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<mixedSignedSt::_bitWidth> packed_data;
        packed_data.range(3, 0) = flags;
        packed_data.range(11, 4) = offset;
        packed_data.range(27, 12) = temp;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<mixedSignedSt::_bitWidth> packed_data)
    {
        flags = (fourBitT) packed_data.range(3, 0).to_uint64();
        offset = (signedByte_t) packed_data.range(11, 4).to_uint64();
        // Sign extension for signed type
        if (offset & (1ULL << (8 - 1))) {
            offset = (signedByte_t)(offset | ~((1ULL << 8) - 1));
        }
        temp = (signedWord_t) packed_data.range(27, 12).to_uint64();
        // Sign extension for signed type
        if (temp & (1ULL << (16 - 1))) {
            temp = (signedWord_t)(temp | ~((1ULL << 16) - 1));
        }
    }
    explicit mixedSignedSt(sc_bv<mixedSignedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 4*3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const signedArraySt & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<3; i++) {
            ret = ret && (values[i] == rhs.values[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const signedArraySt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<3; i++) {
            sc_trace(tf,v.values[i], NAME + ".values[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  signedArraySt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("values[0:2]: {}",
           staticArrayPrt<signedNibble_t, 3>(values, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, signedArraySt::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            pack_bits((uint64_t *)&_ret, _pos, values[i] & ((1ULL << 4) - 1), 4);
            _pos += 4;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            uint16_t _bits = 4;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(16-(_pos & 15)));
            values[i] = (signedNibble_t)((_src >> (_pos & 15)) & ((1ULL << 4) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 16)) {
                values[i] = (signedNibble_t)(values[i] | ((_src << _consume) & ((1ULL << 4) - 1)));
                _pos += _bits;
            }
            // Sign extension for signed type
            if (values[i] & (1ULL << (4 - 1))) {
                values[i] = (signedNibble_t)(values[i] | ~((1ULL << 4) - 1));
            }
        }
    }
    inline sc_bv<signedArraySt::_bitWidth> sc_pack(void) const
    {
        sc_bv<signedArraySt::_bitWidth> packed_data;
        for(unsigned int i=0; i<3; i++) {
            packed_data.range(0+(i+1)*4-1, 0+i*4) = values[i];
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<signedArraySt::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<3; i++) {
            values[i] = (signedNibble_t) packed_data.range(0+(i+1)*4-1, 0+i*4).to_uint64();
            // Sign extension for signed type
            if (values[i] & (1ULL << (4 - 1))) {
                values[i] = (signedNibble_t)(values[i] | ~((1ULL << 4) - 1));
            }
        }
    }
    explicit signedArraySt(sc_bv<signedArraySt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 3 + 5 + 5 + 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const nonByteAlignedSignedSt & rhs) const {
        bool ret = true;
        ret = ret && (field1 == rhs.field1);
        ret = ret && (field2 == rhs.field2);
        ret = ret && (field3 == rhs.field3);
        ret = ret && (field4 == rhs.field4);
        return ( ret );
        }
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
    std::string prt(bool all=false) const
    {
        return (std::format("field1:0x{:01x} field2:0x{:02x} field3:0x{:02x} field4:0x{:01x}",
           (uint64_t) field1,
           (uint64_t) field2,
           (uint64_t) field3,
           (uint64_t) field4
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, nonByteAlignedSignedSt::_byteWidth);
        _ret = field4;
        _ret |= ((uint16_t)(field3 & ((1ULL << 5) - 1))) << (3 & 15);
        _ret |= (uint16_t)field2 << (8 & 15);
        _ret |= ((uint16_t)(field1 & ((1ULL << 3) - 1))) << (13 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        field4 = (threeBitT)((_src >> (_pos & 15)) & ((1ULL << 3) - 1));
        _pos += 3;
        field3 = (signed5bit_t)((_src >> (_pos & 15)) & ((1ULL << 5) - 1));
        _pos += 5;
        // Sign extension for signed type
        if (field3 & (1ULL << (5 - 1))) {
            field3 = (signed5bit_t)(field3 | ~((1ULL << 5) - 1));
        }
        field2 = (unsigned5bit_t)((_src >> (_pos & 15)) & ((1ULL << 5) - 1));
        _pos += 5;
        field1 = (signed3bit_t)((_src >> (_pos & 15)) & ((1ULL << 3) - 1));
        _pos += 3;
        // Sign extension for signed type
        if (field1 & (1ULL << (3 - 1))) {
            field1 = (signed3bit_t)(field1 | ~((1ULL << 3) - 1));
        }
    }
    inline sc_bv<nonByteAlignedSignedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<nonByteAlignedSignedSt::_bitWidth> packed_data;
        packed_data.range(2, 0) = field4;
        packed_data.range(7, 3) = field3;
        packed_data.range(12, 8) = field2;
        packed_data.range(15, 13) = field1;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<nonByteAlignedSignedSt::_bitWidth> packed_data)
    {
        field4 = (threeBitT) packed_data.range(2, 0).to_uint64();
        field3 = (signed5bit_t) packed_data.range(7, 3).to_uint64();
        // Sign extension for signed type
        if (field3 & (1ULL << (5 - 1))) {
            field3 = (signed5bit_t)(field3 | ~((1ULL << 5) - 1));
        }
        field2 = (unsigned5bit_t) packed_data.range(12, 8).to_uint64();
        field1 = (signed3bit_t) packed_data.range(15, 13).to_uint64();
        // Sign extension for signed type
        if (field1 & (1ULL << (3 - 1))) {
            field1 = (signed3bit_t)(field1 | ~((1ULL << 3) - 1));
        }
    }
    explicit nonByteAlignedSignedSt(sc_bv<nonByteAlignedSignedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 8 + 4 + 11 + 9 + 7;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const complexMixedSt & rhs) const {
        bool ret = true;
        ret = ret && (signedA == rhs.signedA);
        ret = ret && (unsignedB == rhs.unsignedB);
        ret = ret && (signedC == rhs.signedC);
        ret = ret && (unsignedD == rhs.unsignedD);
        ret = ret && (signedE == rhs.signedE);
        return ( ret );
        }
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
    std::string prt(bool all=false) const
    {
        return (std::format("signedA:0x{:02x} unsignedB:0x{:03x} signedC:0x{:03x} unsignedD:0x{:01x} signedE:0x{:02x}",
           (uint64_t) signedA,
           (uint64_t) unsignedB,
           (uint64_t) signedC,
           (uint64_t) unsignedD,
           (uint64_t) signedE
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, complexMixedSt::_byteWidth);
        _ret = signedE & ((1ULL << 8) - 1);
        _ret |= (uint64_t)unsignedD << (8 & 63);
        _ret |= ((uint64_t)(signedC & ((1ULL << 11) - 1))) << (12 & 63);
        _ret |= (uint64_t)unsignedB << (23 & 63);
        _ret |= ((uint64_t)(signedA & ((1ULL << 7) - 1))) << (32 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        signedE = (signedByte_t)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
        _pos += 8;
        // Sign extension for signed type
        if (signedE & (1ULL << (8 - 1))) {
            signedE = (signedByte_t)(signedE | ~((1ULL << 8) - 1));
        }
        unsignedD = (fourBitT)((_src >> (_pos & 63)) & ((1ULL << 4) - 1));
        _pos += 4;
        signedC = (signed11bit_t)((_src >> (_pos & 63)) & ((1ULL << 11) - 1));
        _pos += 11;
        // Sign extension for signed type
        if (signedC & (1ULL << (11 - 1))) {
            signedC = (signed11bit_t)(signedC | ~((1ULL << 11) - 1));
        }
        unsignedB = (unsigned9bit_t)((_src >> (_pos & 63)) & ((1ULL << 9) - 1));
        _pos += 9;
        signedA = (signed7bit_t)((_src >> (_pos & 63)) & ((1ULL << 7) - 1));
        _pos += 7;
        // Sign extension for signed type
        if (signedA & (1ULL << (7 - 1))) {
            signedA = (signed7bit_t)(signedA | ~((1ULL << 7) - 1));
        }
    }
    inline sc_bv<complexMixedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<complexMixedSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = signedE;
        packed_data.range(11, 8) = unsignedD;
        packed_data.range(22, 12) = signedC;
        packed_data.range(31, 23) = unsignedB;
        packed_data.range(38, 32) = signedA;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<complexMixedSt::_bitWidth> packed_data)
    {
        signedE = (signedByte_t) packed_data.range(7, 0).to_uint64();
        // Sign extension for signed type
        if (signedE & (1ULL << (8 - 1))) {
            signedE = (signedByte_t)(signedE | ~((1ULL << 8) - 1));
        }
        unsignedD = (fourBitT) packed_data.range(11, 8).to_uint64();
        signedC = (signed11bit_t) packed_data.range(22, 12).to_uint64();
        // Sign extension for signed type
        if (signedC & (1ULL << (11 - 1))) {
            signedC = (signed11bit_t)(signedC | ~((1ULL << 11) - 1));
        }
        unsignedB = (unsigned9bit_t) packed_data.range(31, 23).to_uint64();
        signedA = (signed7bit_t) packed_data.range(38, 32).to_uint64();
        // Sign extension for signed type
        if (signedA & (1ULL << (7 - 1))) {
            signedA = (signed7bit_t)(signedA | ~((1ULL << 7) - 1));
        }
    }
    explicit complexMixedSt(sc_bv<complexMixedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 16 + 11 + 4 + 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const edgeCaseSignedSt & rhs) const {
        bool ret = true;
        ret = ret && (tiny == rhs.tiny);
        ret = ret && (smallVal == rhs.smallVal);
        ret = ret && (mediumVal == rhs.mediumVal);
        ret = ret && (largeVal == rhs.largeVal);
        return ( ret );
        }
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
    std::string prt(bool all=false) const
    {
        return (std::format("tiny:0x{:01x} smallVal:0x{:01x} mediumVal:0x{:03x} largeVal:0x{:04x}",
           (uint64_t) tiny,
           (uint64_t) smallVal,
           (uint64_t) mediumVal,
           (uint64_t) largeVal
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, edgeCaseSignedSt::_byteWidth);
        _ret = largeVal & ((1ULL << 16) - 1);
        _ret |= ((uint64_t)(mediumVal & ((1ULL << 11) - 1))) << (16 & 63);
        _ret |= ((uint64_t)(smallVal & ((1ULL << 4) - 1))) << (27 & 63);
        _ret |= ((uint64_t)(tiny & ((1ULL << 3) - 1))) << (31 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        largeVal = (signedWord_t)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
        _pos += 16;
        // Sign extension for signed type
        if (largeVal & (1ULL << (16 - 1))) {
            largeVal = (signedWord_t)(largeVal | ~((1ULL << 16) - 1));
        }
        mediumVal = (signed11bit_t)((_src >> (_pos & 63)) & ((1ULL << 11) - 1));
        _pos += 11;
        // Sign extension for signed type
        if (mediumVal & (1ULL << (11 - 1))) {
            mediumVal = (signed11bit_t)(mediumVal | ~((1ULL << 11) - 1));
        }
        smallVal = (signedNibble_t)((_src >> (_pos & 63)) & ((1ULL << 4) - 1));
        _pos += 4;
        // Sign extension for signed type
        if (smallVal & (1ULL << (4 - 1))) {
            smallVal = (signedNibble_t)(smallVal | ~((1ULL << 4) - 1));
        }
        tiny = (signed3bit_t)((_src >> (_pos & 63)) & ((1ULL << 3) - 1));
        _pos += 3;
        // Sign extension for signed type
        if (tiny & (1ULL << (3 - 1))) {
            tiny = (signed3bit_t)(tiny | ~((1ULL << 3) - 1));
        }
    }
    inline sc_bv<edgeCaseSignedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<edgeCaseSignedSt::_bitWidth> packed_data;
        packed_data.range(15, 0) = largeVal;
        packed_data.range(26, 16) = mediumVal;
        packed_data.range(30, 27) = smallVal;
        packed_data.range(33, 31) = tiny;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<edgeCaseSignedSt::_bitWidth> packed_data)
    {
        largeVal = (signedWord_t) packed_data.range(15, 0).to_uint64();
        // Sign extension for signed type
        if (largeVal & (1ULL << (16 - 1))) {
            largeVal = (signedWord_t)(largeVal | ~((1ULL << 16) - 1));
        }
        mediumVal = (signed11bit_t) packed_data.range(26, 16).to_uint64();
        // Sign extension for signed type
        if (mediumVal & (1ULL << (11 - 1))) {
            mediumVal = (signed11bit_t)(mediumVal | ~((1ULL << 11) - 1));
        }
        smallVal = (signedNibble_t) packed_data.range(30, 27).to_uint64();
        // Sign extension for signed type
        if (smallVal & (1ULL << (4 - 1))) {
            smallVal = (signedNibble_t)(smallVal | ~((1ULL << 4) - 1));
        }
        tiny = (signed3bit_t) packed_data.range(33, 31).to_uint64();
        // Sign extension for signed type
        if (tiny & (1ULL << (3 - 1))) {
            tiny = (signed3bit_t)(tiny | ~((1ULL << 3) - 1));
        }
    }
    explicit edgeCaseSignedSt(sc_bv<edgeCaseSignedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 5*3 + 5*4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const mixedArraySignedSt & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<4; i++) {
            ret = ret && (signedVals[i] == rhs.signedVals[i]);
        }
        for(unsigned int i=0; i<3; i++) {
            ret = ret && (unsignedVals[i] == rhs.unsignedVals[i]);
        }
        return ( ret );
        }
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
    std::string prt(bool all=false) const
    {
        return (std::format("signedVals[0:3]: {} unsignedVals[0:2]: {}",
           staticArrayPrt<signed5bit_t, 4>(signedVals, all),
           staticArrayPrt<unsigned5bit_t, 3>(unsignedVals, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, mixedArraySignedSt::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            pack_bits((uint64_t *)&_ret, _pos, unsignedVals[i], 5);
            _pos += 5;
        }
        for(unsigned int i=0; i<4; i++) {
            pack_bits((uint64_t *)&_ret, _pos, signedVals[i] & ((1ULL << 5) - 1), 5);
            _pos += 5;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            uint16_t _bits = 5;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            unsignedVals[i] = (unsigned5bit_t)((_src >> (_pos & 63)) & ((1ULL << 5) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                unsignedVals[i] = (unsigned5bit_t)(unsignedVals[i] | ((_src << _consume) & ((1ULL << 5) - 1)));
                _pos += _bits;
            }
        }
        for(unsigned int i=0; i<4; i++) {
            uint16_t _bits = 5;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            signedVals[i] = (signed5bit_t)((_src >> (_pos & 63)) & ((1ULL << 5) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                signedVals[i] = (signed5bit_t)(signedVals[i] | ((_src << _consume) & ((1ULL << 5) - 1)));
                _pos += _bits;
            }
            // Sign extension for signed type
            if (signedVals[i] & (1ULL << (5 - 1))) {
                signedVals[i] = (signed5bit_t)(signedVals[i] | ~((1ULL << 5) - 1));
            }
        }
    }
    inline sc_bv<mixedArraySignedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<mixedArraySignedSt::_bitWidth> packed_data;
        for(unsigned int i=0; i<3; i++) {
            packed_data.range(0+(i+1)*5-1, 0+i*5) = unsignedVals[i];
        }
        for(unsigned int i=0; i<4; i++) {
            packed_data.range(15+(i+1)*5-1, 15+i*5) = signedVals[i];
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<mixedArraySignedSt::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<3; i++) {
            unsignedVals[i] = (unsigned5bit_t) packed_data.range(0+(i+1)*5-1, 0+i*5).to_uint64();
        }
        for(unsigned int i=0; i<4; i++) {
            signedVals[i] = (signed5bit_t) packed_data.range(15+(i+1)*5-1, 15+i*5).to_uint64();
            // Sign extension for signed type
            if (signedVals[i] & (1ULL << (5 - 1))) {
                signedVals[i] = (signed5bit_t)(signedVals[i] | ~((1ULL << 5) - 1));
            }
        }
    }
    explicit mixedArraySignedSt(sc_bv<mixedArraySignedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit mixedArraySignedSt(
        unsigned5bit_t unsignedVals_[3],
        signed5bit_t signedVals_[4])
    {
        memcpy(&unsignedVals, &unsignedVals_, sizeof(unsignedVals));
        memcpy(&signedVals, &signedVals_, sizeof(signedVals));
    }
    explicit mixedArraySignedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct test37BitRegSt {
    test37BitT value37; //

    test37BitRegSt() {}

    static constexpr uint16_t _bitWidth = 37;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const test37BitRegSt & rhs) const {
        bool ret = true;
        ret = ret && (value37 == rhs.value37);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const test37BitRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.value37, NAME + ".value37");
    }
    inline friend ostream& operator << ( ostream& os,  test37BitRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("value37:0x{:010x}",
           (uint64_t) value37
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, test37BitRegSt::_byteWidth);
        _ret = value37;
    }
    inline void unpack(const _packedSt &_src)
    {
        value37 = (test37BitT)((_src) & ((1ULL << 37) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( value37 & ((1ULL<<37 )-1) << 0);
        return( ret );
    }
    void _setValue(uint64_t value)
    {
        value37 = ( test37BitT ) (( value >> 0 ) & (( (uint64_t)1 << 37 ) - 1)) ;
        }
    inline sc_bv<test37BitRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<test37BitRegSt::_bitWidth> packed_data;
        packed_data.range(36, 0) = value37;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<test37BitRegSt::_bitWidth> packed_data)
    {
        value37 = (test37BitT) packed_data.range(36, 0).to_uint64();
    }
    explicit test37BitRegSt(sc_bv<test37BitRegSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit test37BitRegSt(
        test37BitT value37_) :
        value37(value37_)
    {}
    explicit test37BitRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct log2TestSt {
    signedLog2T signedCount; //Signed count field using widthLog2+isSigned
    bSizeIndexT index; //Index field using widthLog2minus1 type
    bSizeCountT count; //Count field using widthLog2 type

    log2TestSt() {}

    static constexpr uint16_t _bitWidth = clog2(BSIZE+1)+1 + clog2(BSIZE) + clog2(BSIZE+1);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const log2TestSt & rhs) const {
        bool ret = true;
        ret = ret && (count == rhs.count);
        ret = ret && (index == rhs.index);
        ret = ret && (signedCount == rhs.signedCount);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const log2TestSt & v, const std::string & NAME ) {
        sc_trace(tf,v.count, NAME + ".count");
        sc_trace(tf,v.index, NAME + ".index");
        sc_trace(tf,v.signedCount, NAME + ".signedCount");
    }
    inline friend ostream& operator << ( ostream& os,  log2TestSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("count:0x{:01x} index:0x{:01x} signedCount:0x{:02x}",
           (uint64_t) count,
           (uint64_t) index,
           (uint64_t) signedCount
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, log2TestSt::_byteWidth);
        _ret = signedCount & ((1ULL << clog2(BSIZE+1)+1) - 1);
        _ret |= (uint16_t)index << (5 & 15);
        _ret |= (uint16_t)count << (9 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        signedCount = (signedLog2T)((_src >> (_pos & 15)) & ((1ULL << 5) - 1));
        _pos += 5;
        // Sign extension for signed type
        if (signedCount & (1ULL << (clog2(BSIZE+1)+1 - 1))) {
            signedCount = (signedLog2T)(signedCount | ~((1ULL << clog2(BSIZE+1)+1) - 1));
        }
        index = (bSizeIndexT)((_src >> (_pos & 15)) & ((1ULL << 4) - 1));
        _pos += 4;
        count = (bSizeCountT)((_src >> (_pos & 15)) & ((1ULL << 4) - 1));
    }
    inline sc_bv<log2TestSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<log2TestSt::_bitWidth> packed_data;
        packed_data.range(4, 0) = signedCount;
        packed_data.range(8, 5) = index;
        packed_data.range(12, 9) = count;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<log2TestSt::_bitWidth> packed_data)
    {
        signedCount = (signedLog2T) packed_data.range(4, 0).to_uint64();
        // Sign extension for signed type
        if (signedCount & (1ULL << (clog2(BSIZE+1)+1 - 1))) {
            signedCount = (signedLog2T)(signedCount | ~((1ULL << clog2(BSIZE+1)+1) - 1));
        }
        index = (bSizeIndexT) packed_data.range(8, 5).to_uint64();
        count = (bSizeCountT) packed_data.range(12, 9).to_uint64();
    }
    explicit log2TestSt(sc_bv<log2TestSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit log2TestSt(
        signedLog2T signedCount_,
        bSizeIndexT index_,
        bSizeCountT count_) :
        signedCount(signedCount_),
        index(index_),
        count(count_)
    {}
    explicit log2TestSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct nestedLog2St {
    log2TestSt log2Data; //Nested struct with widthLog2 fields
    threeBitT tag; //A plain 3-bit tag

    nestedLog2St() {}

    static constexpr uint16_t _bitWidth = log2TestSt::_bitWidth + 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const nestedLog2St & rhs) const {
        bool ret = true;
        ret = ret && (tag == rhs.tag);
        ret = ret && (log2Data == rhs.log2Data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const nestedLog2St & v, const std::string & NAME ) {
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.log2Data, NAME + ".log2Data");
    }
    inline friend ostream& operator << ( ostream& os,  nestedLog2St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tag:0x{:01x} log2Data:<{}>",
           (uint64_t) tag,
           log2Data.prt(all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, nestedLog2St::_byteWidth);
        {
            log2Data.pack(*(log2TestSt::_packedSt*)&_ret);
        }
        _ret |= (uint16_t)tag << (13 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        {
            log2Data.unpack(*(log2TestSt::_packedSt*)&_src);
        }
        _pos += log2TestSt::_bitWidth;
        tag = (threeBitT)((_src >> (_pos & 15)) & ((1ULL << 3) - 1));
    }
    inline sc_bv<nestedLog2St::_bitWidth> sc_pack(void) const
    {
        sc_bv<nestedLog2St::_bitWidth> packed_data;
        packed_data.range(12, 0) = log2Data.sc_pack();
        packed_data.range(15, 13) = tag;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<nestedLog2St::_bitWidth> packed_data)
    {
        log2Data.sc_unpack(packed_data.range(12, 0));
        tag = (threeBitT) packed_data.range(15, 13).to_uint64();
    }
    explicit nestedLog2St(sc_bv<nestedLog2St::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit nestedLog2St(
        log2TestSt log2Data_,
        threeBitT tag_) :
        log2Data(log2Data_),
        tag(tag_)
    {}
    explicit nestedLog2St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct wideLog2St {
    log2TestSt nested; //Nested log2 struct
    apbAddrT addr; //Address
    fourBitT flags; //Flags
    threeBitT tag; //Tag
    signedLog2T signedB; //Signed count B
    signedLog2T signedA; //Signed count A
    bSizeIndexT indexB; //Index field B
    bSizeIndexT indexA[ASIZE2]; //Index field A
    bSizeCountT countB; //Count field B
    bSizeCountT countA; //Count field A

    wideLog2St() {}

    static constexpr uint16_t _bitWidth = log2TestSt::_bitWidth + DWORD + 4 + 3 + clog2(BSIZE+1)+1 + clog2(BSIZE+1)+1
                                          + clog2(BSIZE) + clog2(BSIZE)*ASIZE2 + clog2(BSIZE+1) + clog2(BSIZE+1);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const wideLog2St & rhs) const {
        bool ret = true;
        ret = ret && (countA == rhs.countA);
        ret = ret && (countB == rhs.countB);
        for(unsigned int i=0; i<ASIZE2; i++) {
            ret = ret && (indexA[i] == rhs.indexA[i]);
        }
        ret = ret && (indexB == rhs.indexB);
        ret = ret && (signedA == rhs.signedA);
        ret = ret && (signedB == rhs.signedB);
        ret = ret && (tag == rhs.tag);
        ret = ret && (flags == rhs.flags);
        ret = ret && (addr == rhs.addr);
        ret = ret && (nested == rhs.nested);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const wideLog2St & v, const std::string & NAME ) {
        sc_trace(tf,v.countA, NAME + ".countA");
        sc_trace(tf,v.countB, NAME + ".countB");
        for(unsigned int i=0; i<ASIZE2; i++) {
            sc_trace(tf,v.indexA[i], NAME + ".indexA[i]");
        }
        sc_trace(tf,v.indexB, NAME + ".indexB");
        sc_trace(tf,v.signedA, NAME + ".signedA");
        sc_trace(tf,v.signedB, NAME + ".signedB");
        sc_trace(tf,v.tag, NAME + ".tag");
        sc_trace(tf,v.flags, NAME + ".flags");
        sc_trace(tf,v.addr, NAME + ".addr");
        sc_trace(tf,v.nested, NAME + ".nested");
    }
    inline friend ostream& operator << ( ostream& os,  wideLog2St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("countA:0x{:01x} countB:0x{:01x} indexA[0:1]: {} indexB:0x{:01x} signedA:0x{:02x} signedB:0x{:02x} tag:0x{:01x} flags:0x{:01x} addr:0x{:08x} nested:<{}>",
           (uint64_t) countA,
           (uint64_t) countB,
           staticArrayPrt<bSizeIndexT, ASIZE2>(indexA, all),
           (uint64_t) indexB,
           (uint64_t) signedA,
           (uint64_t) signedB,
           (uint64_t) tag,
           (uint64_t) flags,
           (uint64_t) addr,
           nested.prt(all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, wideLog2St::_byteWidth);
        {
            nested.pack(*(log2TestSt::_packedSt*)&_ret);
        }
        _ret[ 0 ] |= (uint64_t)addr << (13 & 63);
        _ret[ 0 ] |= (uint64_t)flags << (45 & 63);
        _ret[ 0 ] |= (uint64_t)tag << (49 & 63);
        _ret[ 0 ] |= ((uint64_t)(signedB & ((1ULL << clog2(BSIZE+1)+1) - 1))) << (52 & 63);
        _ret[ 0 ] |= ((uint64_t)(signedA & ((1ULL << clog2(BSIZE+1)+1) - 1))) << (57 & 63);
        pack_bits((uint64_t *)&_ret, 62, indexB, clog2(BSIZE));
        uint16_t _pos{66};
        for(unsigned int i=0; i<ASIZE2; i++) {
            pack_bits((uint64_t *)&_ret, _pos, indexA[i], clog2(BSIZE));
            _pos += clog2(BSIZE);
        }
        pack_bits((uint64_t *)&_ret, 74, countB, clog2(BSIZE+1));
        pack_bits((uint64_t *)&_ret, 78, countA, clog2(BSIZE+1));
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        {
            nested.unpack(*(log2TestSt::_packedSt*)&_src[ _pos >> 6 ]);
        }
        _pos += log2TestSt::_bitWidth;
        addr = (apbAddrT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += 32;
        flags = (fourBitT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 4) - 1));
        _pos += 4;
        tag = (threeBitT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 3) - 1));
        _pos += 3;
        signedB = (signedLog2T)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 5) - 1));
        _pos += 5;
        // Sign extension for signed type
        if (signedB & (1ULL << (clog2(BSIZE+1)+1 - 1))) {
            signedB = (signedLog2T)(signedB | ~((1ULL << clog2(BSIZE+1)+1) - 1));
        }
        signedA = (signedLog2T)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 5) - 1));
        _pos += 5;
        // Sign extension for signed type
        if (signedA & (1ULL << (clog2(BSIZE+1)+1 - 1))) {
            signedA = (signedLog2T)(signedA | ~((1ULL << clog2(BSIZE+1)+1) - 1));
        }
        indexB = (bSizeIndexT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 4) - 1));
        _pos += 2;
        indexB = (bSizeIndexT)(indexB | ((_src[ _pos >> 6 ] << 2) & ((1ULL << 4) - 1)));
        _pos += 2;
        for(unsigned int i=0; i<ASIZE2; i++) {
            uint16_t _bits = clog2(BSIZE);
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            indexA[i] = (bSizeIndexT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 4) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                indexA[i] = (bSizeIndexT)(indexA[i] | ((_src[ _pos >> 6 ] << _consume) & ((1ULL << 4) - 1)));
                _pos += _bits;
            }
        }
        countB = (bSizeCountT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 4) - 1));
        _pos += 4;
        countA = (bSizeCountT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 4) - 1));
    }
    inline sc_bv<wideLog2St::_bitWidth> sc_pack(void) const
    {
        sc_bv<wideLog2St::_bitWidth> packed_data;
        packed_data.range(12, 0) = nested.sc_pack();
        packed_data.range(44, 13) = addr;
        packed_data.range(48, 45) = flags;
        packed_data.range(51, 49) = tag;
        packed_data.range(56, 52) = signedB;
        packed_data.range(61, 57) = signedA;
        packed_data.range(65, 62) = indexB;
        for(unsigned int i=0; i<ASIZE2; i++) {
            packed_data.range(66+(i+1)*clog2(BSIZE)-1, 66+i*clog2(BSIZE)) = indexA[i];
        }
        packed_data.range(77, 74) = countB;
        packed_data.range(81, 78) = countA;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<wideLog2St::_bitWidth> packed_data)
    {
        nested.sc_unpack(packed_data.range(12, 0));
        addr = (apbAddrT) packed_data.range(44, 13).to_uint64();
        flags = (fourBitT) packed_data.range(48, 45).to_uint64();
        tag = (threeBitT) packed_data.range(51, 49).to_uint64();
        signedB = (signedLog2T) packed_data.range(56, 52).to_uint64();
        // Sign extension for signed type
        if (signedB & (1ULL << (clog2(BSIZE+1)+1 - 1))) {
            signedB = (signedLog2T)(signedB | ~((1ULL << clog2(BSIZE+1)+1) - 1));
        }
        signedA = (signedLog2T) packed_data.range(61, 57).to_uint64();
        // Sign extension for signed type
        if (signedA & (1ULL << (clog2(BSIZE+1)+1 - 1))) {
            signedA = (signedLog2T)(signedA | ~((1ULL << clog2(BSIZE+1)+1) - 1));
        }
        indexB = (bSizeIndexT) packed_data.range(65, 62).to_uint64();
        for(unsigned int i=0; i<ASIZE2; i++) {
            indexA[i] = (bSizeIndexT) packed_data.range(66+(i+1)*clog2(BSIZE)-1, 66+i*clog2(BSIZE)).to_uint64();
        }
        countB = (bSizeCountT) packed_data.range(77, 74).to_uint64();
        countA = (bSizeCountT) packed_data.range(81, 78).to_uint64();
    }
    explicit wideLog2St(sc_bv<wideLog2St::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit wideLog2St(
        log2TestSt nested_,
        apbAddrT addr_,
        fourBitT flags_,
        threeBitT tag_,
        signedLog2T signedB_,
        signedLog2T signedA_,
        bSizeIndexT indexB_,
        bSizeIndexT indexA_[ASIZE2],
        bSizeCountT countB_,
        bSizeCountT countA_) :
        nested(nested_),
        addr(addr_),
        flags(flags_),
        tag(tag_),
        signedB(signedB_),
        signedA(signedA_),
        indexB(indexB_),
        countB(countB_),
        countA(countA_)
    {
        memcpy(&indexA, &indexA_, sizeof(indexA));
    }
    explicit wideLog2St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace mixed_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace mixed_ns {
template<typename Config>
class test_mixed_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace mixed_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace mixed_ns {
template<typename Config>
std::string test_mixed_structs<Config>::name(void) { return "test_mixed_structs"; }
template<typename Config>
void test_mixed_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        aSt::_packedSt packed;
        memset(&packed, pattern, aSt::_byteWidth);
        sc_bv<aSt::_bitWidth> aInit;
        sc_bv<aSt::_bitWidth> aTest;
        for (int i = 0; i < aSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, aSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        aSt a;
        a.sc_unpack(aInit);
        aSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"aSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"aSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = aSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"aSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        aASt::_packedSt packed;
        memset(&packed, pattern, aASt::_byteWidth);
        sc_bv<aASt::_bitWidth> aInit;
        sc_bv<aASt::_bitWidth> aTest;
        for (int i = 0; i < aASt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, aASt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        aASt a;
        a.sc_unpack(aInit);
        aASt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"aASt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"aASt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = aASt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"aASt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        aRegSt::_packedSt packed;
        memset(&packed, pattern, aRegSt::_byteWidth);
        sc_bv<aRegSt::_bitWidth> aInit;
        sc_bv<aRegSt::_bitWidth> aTest;
        for (int i = 0; i < aRegSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, aRegSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        aRegSt a;
        a.sc_unpack(aInit);
        aRegSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"aRegSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"aRegSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = aRegSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"aRegSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        dRegSt::_packedSt packed;
        memset(&packed, pattern, dRegSt::_byteWidth);
        sc_bv<dRegSt::_bitWidth> aInit;
        sc_bv<dRegSt::_bitWidth> aTest;
        for (int i = 0; i < dRegSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, dRegSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        dRegSt a;
        a.sc_unpack(aInit);
        dRegSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"dRegSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"dRegSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = dRegSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"dRegSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        dSt::_packedSt packed;
        memset(&packed, pattern, dSt::_byteWidth);
        sc_bv<dSt::_bitWidth> aInit;
        sc_bv<dSt::_bitWidth> aTest;
        for (int i = 0; i < dSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, dSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        dSt a;
        a.sc_unpack(aInit);
        dSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"dSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"dSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = dSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"dSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        bigSt::_packedSt packed;
        memset(&packed, pattern, bigSt::_byteWidth);
        sc_bv<bigSt::_bitWidth> aInit;
        sc_bv<bigSt::_bitWidth> aTest;
        for (int i = 0; i < bigSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, bigSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        bigSt a;
        a.sc_unpack(aInit);
        bigSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"bigSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"bigSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = bigSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"bigSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        nestedSt::_packedSt packed;
        memset(&packed, pattern, nestedSt::_byteWidth);
        sc_bv<nestedSt::_bitWidth> aInit;
        sc_bv<nestedSt::_bitWidth> aTest;
        for (int i = 0; i < nestedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, nestedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        nestedSt a;
        a.sc_unpack(aInit);
        nestedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"nestedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"nestedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = nestedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"nestedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        bSizeRegSt::_packedSt packed;
        memset(&packed, pattern, bSizeRegSt::_byteWidth);
        sc_bv<bSizeRegSt::_bitWidth> aInit;
        sc_bv<bSizeRegSt::_bitWidth> aTest;
        for (int i = 0; i < bSizeRegSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, bSizeRegSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        bSizeRegSt a;
        a.sc_unpack(aInit);
        bSizeRegSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"bSizeRegSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"bSizeRegSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = bSizeRegSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"bSizeRegSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        bSizeSt::_packedSt packed;
        memset(&packed, pattern, bSizeSt::_byteWidth);
        sc_bv<bSizeSt::_bitWidth> aInit;
        sc_bv<bSizeSt::_bitWidth> aTest;
        for (int i = 0; i < bSizeSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, bSizeSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        bSizeSt a;
        a.sc_unpack(aInit);
        bSizeSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"bSizeSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"bSizeSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = bSizeSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"bSizeSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        apbAddrSt::_packedSt packed;
        memset(&packed, pattern, apbAddrSt::_byteWidth);
        sc_bv<apbAddrSt::_bitWidth> aInit;
        sc_bv<apbAddrSt::_bitWidth> aTest;
        for (int i = 0; i < apbAddrSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, apbAddrSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        apbAddrSt a;
        a.sc_unpack(aInit);
        apbAddrSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"apbAddrSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"apbAddrSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = apbAddrSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"apbAddrSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        apbDataSt::_packedSt packed;
        memset(&packed, pattern, apbDataSt::_byteWidth);
        sc_bv<apbDataSt::_bitWidth> aInit;
        sc_bv<apbDataSt::_bitWidth> aTest;
        for (int i = 0; i < apbDataSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, apbDataSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        apbDataSt a;
        a.sc_unpack(aInit);
        apbDataSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"apbDataSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"apbDataSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = apbDataSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"apbDataSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        cSt::_packedSt packed;
        memset(&packed, pattern, cSt::_byteWidth);
        sc_bv<cSt::_bitWidth> aInit;
        sc_bv<cSt::_bitWidth> aTest;
        for (int i = 0; i < cSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, cSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        cSt a;
        a.sc_unpack(aInit);
        cSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"cSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"cSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = cSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"cSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test1St::_packedSt packed;
        memset(&packed, pattern, test1St::_byteWidth);
        sc_bv<test1St::_bitWidth> aInit;
        sc_bv<test1St::_bitWidth> aTest;
        for (int i = 0; i < test1St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test1St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test1St a;
        a.sc_unpack(aInit);
        test1St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test1St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test1St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test1St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test1St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test2St::_packedSt packed;
        memset(&packed, pattern, test2St::_byteWidth);
        sc_bv<test2St::_bitWidth> aInit;
        sc_bv<test2St::_bitWidth> aTest;
        for (int i = 0; i < test2St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test2St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test2St a;
        a.sc_unpack(aInit);
        test2St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test2St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test2St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test2St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test2St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test3St::_packedSt packed;
        memset(&packed, pattern, test3St::_byteWidth);
        sc_bv<test3St::_bitWidth> aInit;
        sc_bv<test3St::_bitWidth> aTest;
        for (int i = 0; i < test3St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test3St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test3St a;
        a.sc_unpack(aInit);
        test3St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test3St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test3St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test3St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test3St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test4St::_packedSt packed;
        memset(&packed, pattern, test4St::_byteWidth);
        sc_bv<test4St::_bitWidth> aInit;
        sc_bv<test4St::_bitWidth> aTest;
        for (int i = 0; i < test4St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test4St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test4St a;
        a.sc_unpack(aInit);
        test4St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test4St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test4St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test4St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test4St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test5St::_packedSt packed;
        memset(&packed, pattern, test5St::_byteWidth);
        sc_bv<test5St::_bitWidth> aInit;
        sc_bv<test5St::_bitWidth> aTest;
        for (int i = 0; i < test5St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test5St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test5St a;
        a.sc_unpack(aInit);
        test5St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test5St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test5St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test5St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test5St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test6St::_packedSt packed;
        memset(&packed, pattern, test6St::_byteWidth);
        sc_bv<test6St::_bitWidth> aInit;
        sc_bv<test6St::_bitWidth> aTest;
        for (int i = 0; i < test6St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test6St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test6St a;
        a.sc_unpack(aInit);
        test6St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test6St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test6St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test6St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test6St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test7St::_packedSt packed;
        memset(&packed, pattern, test7St::_byteWidth);
        sc_bv<test7St::_bitWidth> aInit;
        sc_bv<test7St::_bitWidth> aTest;
        for (int i = 0; i < test7St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test7St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test7St a;
        a.sc_unpack(aInit);
        test7St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test7St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test7St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test7St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test7St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test8St::_packedSt packed;
        memset(&packed, pattern, test8St::_byteWidth);
        sc_bv<test8St::_bitWidth> aInit;
        sc_bv<test8St::_bitWidth> aTest;
        for (int i = 0; i < test8St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test8St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test8St a;
        a.sc_unpack(aInit);
        test8St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test8St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test8St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test8St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test8St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test9St::_packedSt packed;
        memset(&packed, pattern, test9St::_byteWidth);
        sc_bv<test9St::_bitWidth> aInit;
        sc_bv<test9St::_bitWidth> aTest;
        for (int i = 0; i < test9St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test9St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test9St a;
        a.sc_unpack(aInit);
        test9St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test9St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test9St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test9St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test9St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        signedTestSt::_packedSt packed;
        memset(&packed, pattern, signedTestSt::_byteWidth);
        sc_bv<signedTestSt::_bitWidth> aInit;
        sc_bv<signedTestSt::_bitWidth> aTest;
        for (int i = 0; i < signedTestSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, signedTestSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        signedTestSt a;
        a.sc_unpack(aInit);
        signedTestSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"signedTestSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"signedTestSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = signedTestSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"signedTestSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        mixedSignedSt::_packedSt packed;
        memset(&packed, pattern, mixedSignedSt::_byteWidth);
        sc_bv<mixedSignedSt::_bitWidth> aInit;
        sc_bv<mixedSignedSt::_bitWidth> aTest;
        for (int i = 0; i < mixedSignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, mixedSignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        mixedSignedSt a;
        a.sc_unpack(aInit);
        mixedSignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"mixedSignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"mixedSignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = mixedSignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"mixedSignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        signedArraySt::_packedSt packed;
        memset(&packed, pattern, signedArraySt::_byteWidth);
        sc_bv<signedArraySt::_bitWidth> aInit;
        sc_bv<signedArraySt::_bitWidth> aTest;
        for (int i = 0; i < signedArraySt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, signedArraySt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        signedArraySt a;
        a.sc_unpack(aInit);
        signedArraySt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"signedArraySt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"signedArraySt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = signedArraySt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"signedArraySt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        nonByteAlignedSignedSt::_packedSt packed;
        memset(&packed, pattern, nonByteAlignedSignedSt::_byteWidth);
        sc_bv<nonByteAlignedSignedSt::_bitWidth> aInit;
        sc_bv<nonByteAlignedSignedSt::_bitWidth> aTest;
        for (int i = 0; i < nonByteAlignedSignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, nonByteAlignedSignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        nonByteAlignedSignedSt a;
        a.sc_unpack(aInit);
        nonByteAlignedSignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"nonByteAlignedSignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"nonByteAlignedSignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = nonByteAlignedSignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"nonByteAlignedSignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        complexMixedSt::_packedSt packed;
        memset(&packed, pattern, complexMixedSt::_byteWidth);
        sc_bv<complexMixedSt::_bitWidth> aInit;
        sc_bv<complexMixedSt::_bitWidth> aTest;
        for (int i = 0; i < complexMixedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, complexMixedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        complexMixedSt a;
        a.sc_unpack(aInit);
        complexMixedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"complexMixedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"complexMixedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = complexMixedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"complexMixedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        edgeCaseSignedSt::_packedSt packed;
        memset(&packed, pattern, edgeCaseSignedSt::_byteWidth);
        sc_bv<edgeCaseSignedSt::_bitWidth> aInit;
        sc_bv<edgeCaseSignedSt::_bitWidth> aTest;
        for (int i = 0; i < edgeCaseSignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, edgeCaseSignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        edgeCaseSignedSt a;
        a.sc_unpack(aInit);
        edgeCaseSignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"edgeCaseSignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"edgeCaseSignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = edgeCaseSignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"edgeCaseSignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        mixedArraySignedSt::_packedSt packed;
        memset(&packed, pattern, mixedArraySignedSt::_byteWidth);
        sc_bv<mixedArraySignedSt::_bitWidth> aInit;
        sc_bv<mixedArraySignedSt::_bitWidth> aTest;
        for (int i = 0; i < mixedArraySignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, mixedArraySignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        mixedArraySignedSt a;
        a.sc_unpack(aInit);
        mixedArraySignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"mixedArraySignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"mixedArraySignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = mixedArraySignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"mixedArraySignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        test37BitRegSt::_packedSt packed;
        memset(&packed, pattern, test37BitRegSt::_byteWidth);
        sc_bv<test37BitRegSt::_bitWidth> aInit;
        sc_bv<test37BitRegSt::_bitWidth> aTest;
        for (int i = 0; i < test37BitRegSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, test37BitRegSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        test37BitRegSt a;
        a.sc_unpack(aInit);
        test37BitRegSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"test37BitRegSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"test37BitRegSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = test37BitRegSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"test37BitRegSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        log2TestSt::_packedSt packed;
        memset(&packed, pattern, log2TestSt::_byteWidth);
        sc_bv<log2TestSt::_bitWidth> aInit;
        sc_bv<log2TestSt::_bitWidth> aTest;
        for (int i = 0; i < log2TestSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, log2TestSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        log2TestSt a;
        a.sc_unpack(aInit);
        log2TestSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"log2TestSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"log2TestSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = log2TestSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"log2TestSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        nestedLog2St::_packedSt packed;
        memset(&packed, pattern, nestedLog2St::_byteWidth);
        sc_bv<nestedLog2St::_bitWidth> aInit;
        sc_bv<nestedLog2St::_bitWidth> aTest;
        for (int i = 0; i < nestedLog2St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, nestedLog2St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        nestedLog2St a;
        a.sc_unpack(aInit);
        nestedLog2St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"nestedLog2St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"nestedLog2St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = nestedLog2St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"nestedLog2St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        wideLog2St::_packedSt packed;
        memset(&packed, pattern, wideLog2St::_byteWidth);
        sc_bv<wideLog2St::_bitWidth> aInit;
        sc_bv<wideLog2St::_bitWidth> aTest;
        for (int i = 0; i < wideLog2St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, wideLog2St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        wideLog2St a;
        a.sc_unpack(aInit);
        wideLog2St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"wideLog2St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"wideLog2St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = wideLog2St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"wideLog2St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace mixed_ns

// GENERATED_CODE_END
