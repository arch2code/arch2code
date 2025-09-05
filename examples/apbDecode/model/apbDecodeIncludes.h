#ifndef HELLOWORLDTOPINCLUDES_H
#define HELLOWORLDTOPINCLUDES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <cstdint>
#include "logging.h"

// GENERATED_CODE_PARAM --context=apbDecode.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const int ASIZE = 29;  // The size of A
const int DWORD = 32;  // size of a double word
const int MEMORYA_WORDS = 19;  // Address wordlines for memory A
const int MEMORYA_WORDS_LOG2 = 5;  // Address wordlines for memory A log2
const int MEMORYA_WIDTH = 63;  // Bit width of content for memory A, more than 32, less than 64
const int MEMORYB_WORDS = 21;  // Address wordlines for memory B
const int MEMORYB_WORDS_LOG2 = 5;  // Address wordlines for memory B log2

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types 
// types
typedef uint64_t thirtySevenBitT; // [37] Used as a thirty seven bit register structure
typedef uint32_t aSizeT; // [29] type of width ASIZE
typedef uint32_t apbAddrT; // [32] for addressing register via APB
typedef uint32_t apbDataT; // [32] for the data sent or recieved via APB
typedef uint8_t aAddrBitsT; // [5] size of memory A address in bits
typedef uint64_t aDataBitsT; // [63] size of memory A data in bits
typedef uint8_t bAddrBitsT; // [5] size of memory B address in bits
typedef uint8_t u8T; // [8] Byte integral type
typedef uint16_t u16T; // [16] sixteen bit integral type
typedef uint32_t u32T; // [32] thirty two bit integral type
typedef uint64_t u64T; // [64] sixty four bit integral type

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums 
// enums
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

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct aRegSt {
    thirtySevenBitT a; //

    aRegSt() {}

    static constexpr uint16_t _bitWidth = 37;
    static constexpr uint16_t _byteWidth = 5;
    typedef uint64_t _packedSt;
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
    void unpack(_packedSt &_src);
    // register functions
    inline int _size(void) {return( (37 + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( a & ((1ULL<<37 )-1) << 0);
        return( ret );
    }
    void _setValue(uint64_t value)
    {
        a = ( thirtySevenBitT ) (( value >> 0 ) & (( (uint64_t)1 << 37 ) - 1)) ;
        }
    sc_bv<37> sc_pack(void) const;
    void sc_unpack(sc_bv<37> packed_data);
    explicit aRegSt(sc_bv<37> packed_data) { sc_unpack(packed_data); }
    explicit aRegSt(
        thirtySevenBitT a_) :
        a(a_)
    {}
    explicit aRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct un0BRegSt {
    u16T fb; //[23:8] - byte 3-4
    u8T fa; //[7:0] - byte 0-2

    un0BRegSt() {}

    static constexpr uint16_t _bitWidth = 24;
    static constexpr uint16_t _byteWidth = 3;
    typedef uint32_t _packedSt;
    bool operator == (const un0BRegSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const un0BRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.fa, NAME + ".fa");
        sc_trace(tf,v.fb, NAME + ".fb");
    }
    inline friend ostream& operator << ( ostream& os,  un0BRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    // register functions
    inline int _size(void) {return( (24 + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( fb & ((1ULL<<16 )-1) << 8);
        return( ret );
    }
    void _setValue(uint64_t value)
    {
        fa = ( u8T ) (( value >> 0 ) & (( (uint64_t)1 << 8 ) - 1)) ;
        fb = ( u16T ) (( value >> 8 ) & (( (uint64_t)1 << 16 ) - 1)) ;
        }
    sc_bv<24> sc_pack(void) const;
    void sc_unpack(sc_bv<24> packed_data);
    explicit un0BRegSt(sc_bv<24> packed_data) { sc_unpack(packed_data); }
    explicit un0BRegSt(
        u16T fb_,
        u8T fa_) :
        fb(fb_),
        fa(fa_)
    {}
    explicit un0BRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct un0ARegSt {
    u8T fc; //[47:40] - byte 8-11
    u32T fb; //[39:8] - byte 4-7
    u8T fa; //[7:0] - byte 0-3

    un0ARegSt() {}

    static constexpr uint16_t _bitWidth = 48;
    static constexpr uint16_t _byteWidth = 6;
    typedef uint64_t _packedSt;
    bool operator == (const un0ARegSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const un0ARegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.fa, NAME + ".fa");
        sc_trace(tf,v.fb, NAME + ".fb");
        sc_trace(tf,v.fc, NAME + ".fc");
    }
    inline friend ostream& operator << ( ostream& os,  un0ARegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    // register functions
    inline int _size(void) {return( (48 + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( fc & ((1ULL<<8 )-1) << 40);
        return( ret );
    }
    void _setValue(uint64_t value)
    {
        fa = ( u8T ) (( value >> 0 ) & (( (uint64_t)1 << 8 ) - 1)) ;
        fb = ( u32T ) (( value >> 8 ) & (( (uint64_t)1 << 32 ) - 1)) ;
        fc = ( u8T ) (( value >> 40 ) & (( (uint64_t)1 << 8 ) - 1)) ;
        }
    sc_bv<48> sc_pack(void) const;
    void sc_unpack(sc_bv<48> packed_data);
    explicit un0ARegSt(sc_bv<48> packed_data) { sc_unpack(packed_data); }
    explicit un0ARegSt(
        u8T fc_,
        u32T fb_,
        u8T fa_) :
        fc(fc_),
        fb(fb_),
        fa(fa_)
    {}
    explicit un0ARegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct aSizeRegSt {
    aSizeT index; //

    aSizeRegSt() {}

    static constexpr uint16_t _bitWidth = 29;
    static constexpr uint16_t _byteWidth = 4;
    typedef uint32_t _packedSt;
    bool operator == (const aSizeRegSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const aSizeRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.index, NAME + ".index");
    }
    inline friend ostream& operator << ( ostream& os,  aSizeRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    // register functions
    inline int _size(void) {return( (29 + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        ( index & ((1ULL<<29 )-1) << 0);
        return( ret );
    }
    void _setValue(uint64_t value)
    {
        index = ( aSizeT ) (( value >> 0 ) & (( (uint64_t)1 << 29 ) - 1)) ;
        }
    sc_bv<29> sc_pack(void) const;
    void sc_unpack(sc_bv<29> packed_data);
    explicit aSizeRegSt(sc_bv<29> packed_data) { sc_unpack(packed_data); }
    explicit aSizeRegSt(
        aSizeT index_) :
        index(index_)
    {}
    explicit aSizeRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

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
    void unpack(_packedSt &_src);
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
    void unpack(_packedSt &_src);
    sc_bv<32> sc_pack(void) const;
    void sc_unpack(sc_bv<32> packed_data);
    explicit apbDataSt(sc_bv<32> packed_data) { sc_unpack(packed_data); }
    explicit apbDataSt(
        apbDataT data_) :
        data(data_)
    {}
    explicit apbDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct aMemAddrSt {
    aAddrBitsT address; //

    aMemAddrSt() {}

    static constexpr uint16_t _bitWidth = 5;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const aMemAddrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const aMemAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  aMemAddrSt const & v ) {
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
    explicit aMemAddrSt(sc_bv<5> packed_data) { sc_unpack(packed_data); }
    explicit aMemAddrSt(
        aAddrBitsT address_) :
        address(address_)
    {}
    explicit aMemAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct aMemSt {
    aDataBitsT data; //

    aMemSt() {}

    static constexpr uint16_t _bitWidth = 63;
    static constexpr uint16_t _byteWidth = 8;
    typedef uint64_t _packedSt;
    bool operator == (const aMemSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const aMemSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  aMemSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<63> sc_pack(void) const;
    void sc_unpack(sc_bv<63> packed_data);
    explicit aMemSt(sc_bv<63> packed_data) { sc_unpack(packed_data); }
    explicit aMemSt(
        aDataBitsT data_) :
        data(data_)
    {}
    explicit aMemSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bMemAddrSt {
    bAddrBitsT address; //

    bMemAddrSt() {}

    static constexpr uint16_t _bitWidth = 5;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const bMemAddrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const bMemAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  bMemAddrSt const & v ) {
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
    explicit bMemAddrSt(sc_bv<5> packed_data) { sc_unpack(packed_data); }
    explicit bMemAddrSt(
        bAddrBitsT address_) :
        address(address_)
    {}
    explicit bMemAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bMemSt {
    u32T data[3]; //

    bMemSt() {}

    static constexpr uint16_t _bitWidth = 96;
    static constexpr uint16_t _byteWidth = 12;
    typedef uint64_t _packedSt[2];
    bool operator == (const bMemSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const bMemSt & v, const std::string & NAME ) {
        for(int i=0; i<3; i++) {
            sc_trace(tf,v.data[i], NAME + ".data[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  bMemSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<96> sc_pack(void) const;
    void sc_unpack(sc_bv<96> packed_data);
    explicit bMemSt(sc_bv<96> packed_data) { sc_unpack(packed_data); }
    explicit bMemSt(
        u32T data_[3])
    {
        memcpy(&data, &data_, sizeof(data));
    }
    explicit bMemSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END

#endif //HELLOWORLDTOPINCLUDES_H

