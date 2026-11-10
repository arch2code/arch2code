
// GENERATED_CODE_PARAM --project=ahbDecode --context=ahbDecode.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module ahbDecode;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ahbDecode_ns {
//constants
inline constexpr uint32_t DWORD = 32;  // Register bus width
inline constexpr uint32_t TBL_WORDS = 8;  // Rows in leafA's table

} // namespace ahbDecode_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ahbDecode_ns {
// types
typedef uint32_t ahbAddrT; // [32] AHB address
typedef uint32_t ahbDataT; // [32] AHB data
typedef uint16_t u16T; // [16] sixteen bit integral type
typedef uint32_t u32T; // [32] thirty two bit integral type
typedef uint8_t tblAddrT; // [3] leafA table row

} // namespace ahbDecode_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ahbDecode_ns {
// enums
enum  addr_id_ahb_top {      //Generated type for addressing top instances
    ADDR_ID_AHB_TOP_ULEAFA=0,   // uLeafA instance address
    ADDR_ID_AHB_TOP_ULEAFB=1,   // uLeafB instance address
    ADDR_ID_AHB_TOP_USUBSYS=2 }; // uSubSys instance address
inline const char* addr_id_ahb_top_prt( addr_id_ahb_top val )
{
    switch( val )
    {
        case ADDR_ID_AHB_TOP_ULEAFA: return( "ADDR_ID_AHB_TOP_ULEAFA" );
        case ADDR_ID_AHB_TOP_ULEAFB: return( "ADDR_ID_AHB_TOP_ULEAFB" );
        case ADDR_ID_AHB_TOP_USUBSYS: return( "ADDR_ID_AHB_TOP_USUBSYS" );
    }
    return("!!!BADENUM!!!");
}
enum  addr_id_ahb_sub {      //Generated type for addressing sub instances
    ADDR_ID_AHB_SUB_ULEAFC=0 }; // uLeafC instance address
inline const char* addr_id_ahb_sub_prt( addr_id_ahb_sub val )
{
    switch( val )
    {
        case ADDR_ID_AHB_SUB_ULEAFC: return( "ADDR_ID_AHB_SUB_ULEAFC" );
    }
    return("!!!BADENUM!!!");
}

} // namespace ahbDecode_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ahbDecode_ns {
// structures
struct ahbAddrSt {
    ahbAddrT address; //

    ahbAddrSt() {}

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const ahbAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ahbAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  ahbAddrSt const & v ) {
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
    inline ahbAddrT _getAddress(void) { return( address); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ahbAddrT)((_src));
    }
    inline sc_bv<ahbAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<ahbAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "ahbAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<ahbAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit ahbAddrSt(const sc_bv<ahbAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit ahbAddrSt(
        ahbAddrT address_) :
        address(address_)
    {}
    explicit ahbAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ahbDataSt {
    ahbDataT data; //

    ahbDataSt() {}

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const ahbDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ahbDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  ahbDataSt const & v ) {
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
    inline ahbDataT _getData(void) { return( data); }
    inline void _setData(ahbDataT value) { data = value; }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (ahbDataT)((_src));
    }
    inline sc_bv<ahbDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<ahbDataSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "ahbDataSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<ahbDataSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit ahbDataSt(const sc_bv<ahbDataSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit ahbDataSt(
        ahbDataT data_) :
        data(data_)
    {}
    explicit ahbDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cfgRegSt {
    u32T value; //

    cfgRegSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const cfgRegSt & rhs) const {
        bool ret = true;
        ret = ret && (value == rhs.value);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cfgRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.value, NAME + ".value");
    }
    inline friend ostream& operator << ( ostream& os,  cfgRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("value:0x{:08x}",
           (uint64_t) value
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = value;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (u32T)((_src));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        (( value & ((1ULL<<32)-1) ) << 0);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        value = ( u32T ) (( packedValue >> 0 ) & (( (uint64_t)1 << 32 ) - 1)) ;
        }
    inline sc_bv<cfgRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<cfgRegSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "cfgRegSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<cfgRegSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit cfgRegSt(const sc_bv<cfgRegSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit cfgRegSt(
        u32T value_) :
        value(value_)
    {}
    explicit cfgRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct statRegSt {
    u16T value; //

    statRegSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const statRegSt & rhs) const {
        bool ret = true;
        ret = ret && (value == rhs.value);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const statRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.value, NAME + ".value");
    }
    inline friend ostream& operator << ( ostream& os,  statRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("value:0x{:04x}",
           (uint64_t) value
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = value;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (u16T)((_src));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        (( value & ((1ULL<<16)-1) ) << 0);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        value = ( u16T ) (( packedValue >> 0 ) & (( (uint64_t)1 << 16 ) - 1)) ;
        }
    inline sc_bv<statRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<statRegSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "statRegSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<statRegSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit statRegSt(const sc_bv<statRegSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit statRegSt(
        u16T value_) :
        value(value_)
    {}
    explicit statRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cmdRegSt {
    u16T value; //

    cmdRegSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const cmdRegSt & rhs) const {
        bool ret = true;
        ret = ret && (value == rhs.value);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cmdRegSt & v, const std::string & NAME ) {
        sc_trace(tf,v.value, NAME + ".value");
    }
    inline friend ostream& operator << ( ostream& os,  cmdRegSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("value:0x{:04x}",
           (uint64_t) value
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = value;
    }
    inline void unpack(const _packedSt &_src)
    {
        value = (u16T)((_src));
    }
    // register functions
    inline int _size(void) {return( (_bitWidth + 7) >> 4 ); }
    uint64_t _getValue(void)
    {
        uint64_t ret =
        (( value & ((1ULL<<16)-1) ) << 0);
        return( ret );
    }
    void _setValue(uint64_t packedValue)
    {
        value = ( u16T ) (( packedValue >> 0 ) & (( (uint64_t)1 << 16 ) - 1)) ;
        }
    inline sc_bv<cmdRegSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<cmdRegSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "cmdRegSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<cmdRegSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit cmdRegSt(const sc_bv<cmdRegSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit cmdRegSt(
        u16T value_) :
        value(value_)
    {}
    explicit cmdRegSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tblSt {
    u32T data; //

    tblSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const tblSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tblSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  tblSt const & v ) {
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
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (u32T)((_src));
    }
    inline sc_bv<tblSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<tblSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "tblSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<tblSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit tblSt(const sc_bv<tblSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit tblSt(
        u32T data_) :
        data(data_)
    {}
    explicit tblSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tblAddrSt {
    tblAddrT address; //

    tblAddrSt() {}

    static constexpr uint16_t _bitWidth = 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const tblAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tblAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  tblAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("address:0x{:01x}",
           (uint64_t) address
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (tblAddrT)((_src) & ((1ULL << 3) - 1));
    }
    inline sc_bv<tblAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<tblAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "tblAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<tblAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit tblAddrSt(const sc_bv<tblAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit tblAddrSt(
        tblAddrT address_) :
        address(address_)
    {}
    explicit tblAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace ahbDecode_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ahbDecode_ns {
inline sc_bv<ahbAddrSt::_bitWidth> testRefPack(const ahbAddrSt &x);
inline void testRefUnpack(ahbAddrSt &x, const sc_bv<ahbAddrSt::_bitWidth> &packed_data);
inline sc_bv<ahbDataSt::_bitWidth> testRefPack(const ahbDataSt &x);
inline void testRefUnpack(ahbDataSt &x, const sc_bv<ahbDataSt::_bitWidth> &packed_data);
inline sc_bv<cfgRegSt::_bitWidth> testRefPack(const cfgRegSt &x);
inline void testRefUnpack(cfgRegSt &x, const sc_bv<cfgRegSt::_bitWidth> &packed_data);
inline sc_bv<statRegSt::_bitWidth> testRefPack(const statRegSt &x);
inline void testRefUnpack(statRegSt &x, const sc_bv<statRegSt::_bitWidth> &packed_data);
inline sc_bv<cmdRegSt::_bitWidth> testRefPack(const cmdRegSt &x);
inline void testRefUnpack(cmdRegSt &x, const sc_bv<cmdRegSt::_bitWidth> &packed_data);
inline sc_bv<tblSt::_bitWidth> testRefPack(const tblSt &x);
inline void testRefUnpack(tblSt &x, const sc_bv<tblSt::_bitWidth> &packed_data);
inline sc_bv<tblAddrSt::_bitWidth> testRefPack(const tblAddrSt &x);
inline void testRefUnpack(tblAddrSt &x, const sc_bv<tblAddrSt::_bitWidth> &packed_data);
inline sc_bv<ahbAddrSt::_bitWidth> testRefPack(const ahbAddrSt &x)
{
    sc_bv<ahbAddrSt::_bitWidth> packed_data;
    packed_data.range(0+DWORD-1, 0) = x.address;
    return packed_data;
}
inline void testRefUnpack(ahbAddrSt &x, const sc_bv<ahbAddrSt::_bitWidth> &packed_data)
{
    x.address = (ahbAddrT) packed_data.range(0+DWORD-1, 0).to_uint64();
}
inline sc_bv<ahbDataSt::_bitWidth> testRefPack(const ahbDataSt &x)
{
    sc_bv<ahbDataSt::_bitWidth> packed_data;
    packed_data.range(0+DWORD-1, 0) = x.data;
    return packed_data;
}
inline void testRefUnpack(ahbDataSt &x, const sc_bv<ahbDataSt::_bitWidth> &packed_data)
{
    x.data = (ahbDataT) packed_data.range(0+DWORD-1, 0).to_uint64();
}
inline sc_bv<cfgRegSt::_bitWidth> testRefPack(const cfgRegSt &x)
{
    sc_bv<cfgRegSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.value;
    return packed_data;
}
inline void testRefUnpack(cfgRegSt &x, const sc_bv<cfgRegSt::_bitWidth> &packed_data)
{
    x.value = (u32T) packed_data.range(0+32-1, 0).to_uint64();
}
inline sc_bv<statRegSt::_bitWidth> testRefPack(const statRegSt &x)
{
    sc_bv<statRegSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.value;
    return packed_data;
}
inline void testRefUnpack(statRegSt &x, const sc_bv<statRegSt::_bitWidth> &packed_data)
{
    x.value = (u16T) packed_data.range(0+16-1, 0).to_uint64();
}
inline sc_bv<cmdRegSt::_bitWidth> testRefPack(const cmdRegSt &x)
{
    sc_bv<cmdRegSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.value;
    return packed_data;
}
inline void testRefUnpack(cmdRegSt &x, const sc_bv<cmdRegSt::_bitWidth> &packed_data)
{
    x.value = (u16T) packed_data.range(0+16-1, 0).to_uint64();
}
inline sc_bv<tblSt::_bitWidth> testRefPack(const tblSt &x)
{
    sc_bv<tblSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.data;
    return packed_data;
}
inline void testRefUnpack(tblSt &x, const sc_bv<tblSt::_bitWidth> &packed_data)
{
    x.data = (u32T) packed_data.range(0+32-1, 0).to_uint64();
}
inline sc_bv<tblAddrSt::_bitWidth> testRefPack(const tblAddrSt &x)
{
    sc_bv<tblAddrSt::_bitWidth> packed_data;
    packed_data.range(0+3-1, 0) = x.address;
    return packed_data;
}
inline void testRefUnpack(tblAddrSt &x, const sc_bv<tblAddrSt::_bitWidth> &packed_data)
{
    x.address = (tblAddrT) packed_data.range(0+3-1, 0).to_uint64();
}
} // namespace ahbDecode_ns
export namespace ahbDecode_test_ns {
class test_ahbDecode_structs {
public:
    static std::string name(void);
    static void test(void);
private:
    template<typename T>
    static void roundTrip(const char* sName, const std::vector<uint8_t>& patterns) {
        for(auto pattern : patterns) {
            roundTripBytes<T>(sName, pattern, 0);
        }
        // Bytes that differ by position expose a field placed a whole number of bytes off.
        roundTripBytes<T>(sName, 0x5b, 0x35);
    }
    template<typename T>
    static void roundTripBytes(const char* sName, uint8_t first, uint8_t step) {
        using P = typename T::_packedSt;
        P words{};
        sc_bv<T::_bitWidth> aInit;
        for (int i = 0; i < T::_byteWidth; i++) {
            uint8_t byte = (uint8_t)(first + i * step);
            int end = std::min((i+1)*8-1, T::_bitWidth-1);
            aInit.range(end, i*8) = byte;
            if constexpr (std::is_array_v<P>) {
                words[i / 8] |= (uint64_t)byte << ((i % 8) * 8);
            } else {
                words |= (P)((uint64_t)byte << (i * 8));
            }
        }
        T ref;
        testRefUnpack(ref, aInit);
        Q_ASSERT(testRefPack(ref) == aInit, std::string(sName) + ": testRefPack(testRefUnpack(pattern)) is not the pattern");
        T b;
        b.unpack(words);
        if (!(b == ref)) {
            cout << ref.prt() << endl << b.prt() << endl;
            Q_ASSERT(false, std::string(sName) + ": unpack() differs from the reference layout");
        }
        T c;
        c.sc_unpack(aInit);
        if (!(c == ref)) {
            cout << ref.prt() << endl << c.prt() << endl;
            Q_ASSERT(false, std::string(sName) + ": sc_unpack() differs from the reference layout");
        }
        P out;
        ref.pack(out);
        sc_bv<T::_bitWidth> outBits;
        for (int i = 0; i < T::_bitWidth; i++) {
            uint64_t word;
            if constexpr (std::is_array_v<P>) {
                word = out[i / 64];
            } else {
                word = (uint64_t)out;
            }
            outBits[i] = (bool)((word >> (i % 64)) & 1);
        }
        if (!(outBits == aInit)) {
            cout << ref.prt() << endl << outBits << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": pack() differs from the reference layout");
        }
        sc_bv<T::_bitWidth> scPacked = ref.sc_pack();
        if (!(scPacked == aInit)) {
            cout << ref.prt() << endl << scPacked << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": sc_pack() differs from the reference layout");
        }
        b.pack(out);
        for (int i = 0; i < T::_bitWidth; i++) {
            uint64_t word;
            if constexpr (std::is_array_v<P>) {
                word = out[i / 64];
            } else {
                word = (uint64_t)out;
            }
            outBits[i] = (bool)((word >> (i % 64)) & 1);
        }
        if (!(outBits == aInit)) {
            cout << b.prt() << endl << outBits << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": pack(unpack(pattern)) is not the pattern");
        }
    }
};
} // namespace ahbDecode_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ahbDecode_test_ns {
using namespace ahbDecode_ns;
std::string test_ahbDecode_structs::name(void) { return "test_ahbDecode_structs"; }
void test_ahbDecode_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<ahbAddrSt>("ahbAddrSt", patterns);
    roundTrip<ahbDataSt>("ahbDataSt", patterns);
    roundTrip<cfgRegSt>("cfgRegSt", patterns);
    roundTrip<statRegSt>("statRegSt", patterns);
    roundTrip<cmdRegSt>("cmdRegSt", patterns);
    roundTrip<tblSt>("tblSt", patterns);
    roundTrip<tblAddrSt>("tblAddrSt", patterns);
}
} // namespace ahbDecode_test_ns

// GENERATED_CODE_END
