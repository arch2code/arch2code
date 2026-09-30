
// GENERATED_CODE_PARAM --project=apbDecode --context=apbDecode.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module apbDecode;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace apbDecode_ns {
//constants
inline constexpr uint32_t ASIZE = 29;  // The size of A
inline constexpr uint32_t DWORD = 32;  // size of a double word
inline constexpr uint32_t MEMORYA_WORDS = 19;  // Address wordlines for memory A
inline constexpr uint32_t MEMORYA_WORDS_LOG2 = 5;  // Address wordlines for memory A log2
inline constexpr uint32_t MEMORYA_WIDTH = 63;  // Bit width of content for memory A, more than 32, less than 64
inline constexpr uint32_t MEMORYB_WORDS = 21;  // Address wordlines for memory B
inline constexpr uint32_t MEMORYB_WORDS_LOG2 = 5;  // Address wordlines for memory B log2

} // namespace apbDecode_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace apbDecode_ns {
// types
typedef uint64_t thirtySevenBitT; // [37] Used as a thirty seven bit register structure
typedef uint32_t aSizeT; // [29] type of width ASIZE
typedef uint32_t apbAddrT; // [32] for addressing register via APB
typedef uint32_t apbDataT; // [32] for the data sent or received via APB
typedef uint8_t aAddrBitsT; // [5] size of memory A address in bits
typedef uint64_t aDataBitsT; // [63] size of memory A data in bits
typedef uint8_t bAddrBitsT; // [5] size of memory B address in bits
typedef uint8_t u8T; // [8] Byte integral type
typedef uint16_t u16T; // [16] sixteen bit integral type
typedef uint32_t u32T; // [32] thirty two bit integral type
typedef uint64_t u64T; // [64] sixty four bit integral type

} // namespace apbDecode_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace apbDecode_ns {
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

} // namespace apbDecode_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace apbDecode_ns {
// structures
struct aRegSt {
    thirtySevenBitT a; //

    aRegSt() {}

    static constexpr uint16_t _bitWidth = 37;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
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
        return (std::format("a:0x{:010x}",
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
        a = (thirtySevenBitT)((_src) & ((1ULL << 37) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        (( a & ((1ULL<<37)-1) ) << 0);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        a = ( thirtySevenBitT ) (( packedValue >> 0 ) & (( (uint64_t)1 << 37 ) - 1)) ;
        }
    inline sc_bv<aRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<aRegSt::_bitWidth> packed_data;
        packed_data.range(36, 0) = a;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<aRegSt::_bitWidth> packed_data)
    {
        a = (thirtySevenBitT) packed_data.range(36, 0).to_uint64();
    }
    explicit aRegSt(sc_bv<aRegSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 16 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const un0BRegSt & rhs) const {
        bool ret = true;
        ret = ret && (fa == rhs.fa);
        ret = ret && (fb == rhs.fb);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const un0BRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.fa, NAME + ".fa");
        sc_trace(tf,v.fb, NAME + ".fb");
    }
    inline friend ostream& operator << ( ostream& os,  un0BRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("fa:0x{:02x} fb:0x{:04x}",
           (uint64_t) fa,
           (uint64_t) fb
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, un0BRegSt::_byteWidth);
        _ret = fb;
        _ret |= (uint32_t)fa << (16 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        fb = (u16T)((_src >> (_pos & 31)) & ((1ULL << 16) - 1));
        _pos += 16;
        fa = (u8T)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        (( fa & ((1ULL<<8)-1) ) << 0)
 +
        (( fb & ((1ULL<<16)-1) ) << 8);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        fa = ( u8T ) (( packedValue >> 0 ) & (( (uint64_t)1 << 8 ) - 1)) ;
        fb = ( u16T ) (( packedValue >> 8 ) & (( (uint64_t)1 << 16 ) - 1)) ;
        }
    inline sc_bv<un0BRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<un0BRegSt::_bitWidth> packed_data;
        packed_data.range(15, 0) = fb;
        packed_data.range(23, 16) = fa;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<un0BRegSt::_bitWidth> packed_data)
    {
        fb = (u16T) packed_data.range(15, 0).to_uint64();
        fa = (u8T) packed_data.range(23, 16).to_uint64();
    }
    explicit un0BRegSt(sc_bv<un0BRegSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = 8 + 32 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const un0ARegSt & rhs) const {
        bool ret = true;
        ret = ret && (fa == rhs.fa);
        ret = ret && (fb == rhs.fb);
        ret = ret && (fc == rhs.fc);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const un0ARegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.fa, NAME + ".fa");
        sc_trace(tf,v.fb, NAME + ".fb");
        sc_trace(tf,v.fc, NAME + ".fc");
    }
    inline friend ostream& operator << ( ostream& os,  un0ARegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("fa:0x{:02x} fb:0x{:08x} fc:0x{:02x}",
           (uint64_t) fa,
           (uint64_t) fb,
           (uint64_t) fc
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, un0ARegSt::_byteWidth);
        _ret = fc;
        _ret |= (uint64_t)fb << (8 & 63);
        _ret |= (uint64_t)fa << (40 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        fc = (u8T)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
        _pos += 8;
        fb = (u32T)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += 32;
        fa = (u8T)((_src >> (_pos & 63)) & ((1ULL << 8) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        (( fa & ((1ULL<<8)-1) ) << 0)
 +
        (( fb & ((1ULL<<32)-1) ) << 8)
 +
        (( fc & ((1ULL<<8)-1) ) << 40);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        fa = ( u8T ) (( packedValue >> 0 ) & (( (uint64_t)1 << 8 ) - 1)) ;
        fb = ( u32T ) (( packedValue >> 8 ) & (( (uint64_t)1 << 32 ) - 1)) ;
        fc = ( u8T ) (( packedValue >> 40 ) & (( (uint64_t)1 << 8 ) - 1)) ;
        }
    inline sc_bv<un0ARegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<un0ARegSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = fc;
        packed_data.range(39, 8) = fb;
        packed_data.range(47, 40) = fa;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<un0ARegSt::_bitWidth> packed_data)
    {
        fc = (u8T) packed_data.range(7, 0).to_uint64();
        fb = (u32T) packed_data.range(39, 8).to_uint64();
        fa = (u8T) packed_data.range(47, 40).to_uint64();
    }
    explicit un0ARegSt(sc_bv<un0ARegSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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

    static constexpr uint16_t _bitWidth = ASIZE;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const aSizeRegSt & rhs) const {
        bool ret = true;
        ret = ret && (index == rhs.index);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const aSizeRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.index, NAME + ".index");
    }
    inline friend ostream& operator << ( ostream& os,  aSizeRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("index:0x{:08x}",
           (uint64_t) index
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aSizeRegSt::_byteWidth);
        _ret = index;
    }
    inline void unpack(const _packedSt &_src)
    {
        index = (aSizeT)((_src) & ((1ULL << 29) - 1));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        (( index & ((1ULL<<ASIZE)-1) ) << 0);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        index = ( aSizeT ) (( packedValue >> 0 ) & (( (uint64_t)1 << ASIZE ) - 1)) ;
        }
    inline sc_bv<aSizeRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<aSizeRegSt::_bitWidth> packed_data;
        packed_data.range(28, 0) = index;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<aSizeRegSt::_bitWidth> packed_data)
    {
        index = (aSizeT) packed_data.range(28, 0).to_uint64();
    }
    explicit aSizeRegSt(sc_bv<aSizeRegSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit aSizeRegSt(
        aSizeT index_) :
        index(index_)
    {}
    explicit aSizeRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

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
struct aMemAddrSt {
    aAddrBitsT address; //

    aMemAddrSt() {}

    static constexpr uint16_t _bitWidth = MEMORYA_WORDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const aMemAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const aMemAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  aMemAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("address:0x{:02x}",
           (uint64_t) address
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aMemAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (aAddrBitsT)((_src) & ((1ULL << 5) - 1));
    }
    inline sc_bv<aMemAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<aMemAddrSt::_bitWidth> packed_data;
        packed_data.range(4, 0) = address;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<aMemAddrSt::_bitWidth> packed_data)
    {
        address = (aAddrBitsT) packed_data.range(4, 0).to_uint64();
    }
    explicit aMemAddrSt(sc_bv<aMemAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit aMemAddrSt(
        aAddrBitsT address_) :
        address(address_)
    {}
    explicit aMemAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct aMemSt {
    aDataBitsT data; //

    aMemSt() {}

    static constexpr uint16_t _bitWidth = MEMORYA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const aMemSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const aMemSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  aMemSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:016x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, aMemSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (aDataBitsT)((_src) & ((1ULL << 63) - 1));
    }
    inline sc_bv<aMemSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<aMemSt::_bitWidth> packed_data;
        packed_data.range(62, 0) = data;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<aMemSt::_bitWidth> packed_data)
    {
        data = (aDataBitsT) packed_data.range(62, 0).to_uint64();
    }
    explicit aMemSt(sc_bv<aMemSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit aMemSt(
        aDataBitsT data_) :
        data(data_)
    {}
    explicit aMemSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bMemAddrSt {
    bAddrBitsT address; //

    bMemAddrSt() {}

    static constexpr uint16_t _bitWidth = MEMORYB_WORDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const bMemAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bMemAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  bMemAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("address:0x{:02x}",
           (uint64_t) address
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, bMemAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (bAddrBitsT)((_src) & ((1ULL << 5) - 1));
    }
    inline sc_bv<bMemAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bMemAddrSt::_bitWidth> packed_data;
        packed_data.range(4, 0) = address;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bMemAddrSt::_bitWidth> packed_data)
    {
        address = (bAddrBitsT) packed_data.range(4, 0).to_uint64();
    }
    explicit bMemAddrSt(sc_bv<bMemAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bMemAddrSt(
        bAddrBitsT address_) :
        address(address_)
    {}
    explicit bMemAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct bMemSt {
    u32T data[3]; //

    bMemSt() {}

    static constexpr uint16_t _bitWidth = 32*3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const bMemSt & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<3; i++) {
            ret = ret && (data[i] == rhs.data[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const bMemSt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<3; i++) {
            sc_trace(tf,v.data[i], NAME + ".data[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  bMemSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data[0:2]: {}",
           staticArrayPrt<u32T, 3>(data, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, bMemSt::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            pack_bits((uint64_t *)&_ret, _pos, data[i], 32);
            _pos += 32;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<3; i++) {
            uint16_t _bits = 32;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            data[i] = (u32T)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 32) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                data[i] = (u32T)(data[i] | ((_src[ _pos >> 6 ] << _consume) & ((1ULL << 32) - 1)));
                _pos += _bits;
            }
        }
    }
    inline sc_bv<bMemSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<bMemSt::_bitWidth> packed_data;
        for(unsigned int i=0; i<3; i++) {
            packed_data.range(0+(i+1)*32-1, 0+i*32) = data[i];
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<bMemSt::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<3; i++) {
            data[i] = (u32T) packed_data.range(0+(i+1)*32-1, 0+i*32).to_uint64();
        }
    }
    explicit bMemSt(sc_bv<bMemSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit bMemSt(
        u32T data_[3])
    {
        memcpy(&data, &data_, sizeof(data));
    }
    explicit bMemSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace apbDecode_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace apbDecode_test_ns {
class test_apbDecode_structs {
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
} // namespace apbDecode_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace apbDecode_test_ns {
using namespace apbDecode_ns;
std::string test_apbDecode_structs::name(void) { return "test_apbDecode_structs"; }
void test_apbDecode_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<aRegSt>("aRegSt", patterns);
    roundTrip<un0BRegSt>("un0BRegSt", patterns);
    roundTrip<un0ARegSt>("un0ARegSt", patterns);
    roundTrip<aSizeRegSt>("aSizeRegSt", patterns);
    roundTrip<apbAddrSt>("apbAddrSt", patterns);
    roundTrip<apbDataSt>("apbDataSt", patterns);
    roundTrip<aMemAddrSt>("aMemAddrSt", patterns);
    roundTrip<aMemSt>("aMemSt", patterns);
    roundTrip<bMemAddrSt>("bMemAddrSt", patterns);
    roundTrip<bMemSt>("bMemSt", patterns);
}
} // namespace apbDecode_test_ns

// GENERATED_CODE_END
