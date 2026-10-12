
// GENERATED_CODE_PARAM --project=twoClk --context=../../yaml/twoClk.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module twoClk;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import twoClkIp;
using namespace twoClkIp_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace twoClk_ns {
//constants
inline constexpr uint32_t TWO_CLK_TICK_DIV = 4;  // clkSlow cycles between consecutive tick words
inline constexpr uint32_t TWO_CLK_TICK_WORDS = 4;  // Tick words the slow sink checks before voting end-of-test
inline constexpr uint32_t TWO_CLK_SLOW_PERIOD_NS = 3;  // clkSlow period in ns; must equal clocks.clkSlow.period in prj/yaml/project.yaml
inline constexpr uint32_t TWO_CLK_TBL_WORDS = 8;  // Row count of twoClkTable's tbl memory
inline constexpr uint32_t TWO_CLK_TBL_WORDS_LOG2 = 3;  // tbl row address width in bits
inline constexpr uint32_t TWO_CLK_LUT_WORDS = 4;  // Row count of twoClkTable's lut and stats memories
inline constexpr uint32_t TWO_CLK_LUT_WORDS_LOG2 = 2;  // lut and stats row address width in bits
inline constexpr uint32_t TWO_CLK_REG_ADDR_WIDTH = 32;  // twoClkReg address bus width
inline constexpr uint32_t TWO_CLK_REG_DATA_WIDTH = 32;  // twoClkReg data bus width

} // namespace twoClk_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace twoClk_ns {
// types
typedef uint32_t twoClkRegAddrT; // [32] for addressing a register via twoClkReg
typedef uint32_t twoClkRegDataT; // [32] for data sent or received via twoClkReg
typedef uint8_t twoClkTblAddrBitsT; // [3] size of tbl's row address in bits
typedef uint32_t twoClkTblLoT; // [32] tbl row bits [31:0]
typedef uint16_t twoClkTblHiT; // [16] tbl row bits [47:32]
typedef uint8_t twoClkLutAddrBitsT; // [2] size of lut and stats row address in bits
typedef uint16_t twoClkLutValT; // [16] lut and stats row value

} // namespace twoClk_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace twoClk_ns {
// enums
enum  addr_id_tbl {          //Generated type for addressing tbl instances
    ADDR_ID_TBL_UTABLE=0 };  // uTable instance address
inline const char* addr_id_tbl_prt( addr_id_tbl val )
{
    switch( val )
    {
        case ADDR_ID_TBL_UTABLE: return( "ADDR_ID_TBL_UTABLE" );
    }
    return("!!!BADENUM!!!");
}

} // namespace twoClk_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace twoClk_ns {
// structures
struct twoClkRegAddrSt {
    twoClkRegAddrT address; //

    twoClkRegAddrSt() {}

    static constexpr uint16_t _bitWidth = TWO_CLK_REG_ADDR_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const twoClkRegAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const twoClkRegAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  twoClkRegAddrSt const & v ) {
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
    inline twoClkRegAddrT _getAddress(void) { return( address); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (twoClkRegAddrT)((_src));
    }
    inline sc_bv<twoClkRegAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkRegAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "twoClkRegAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<twoClkRegAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit twoClkRegAddrSt(const sc_bv<twoClkRegAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit twoClkRegAddrSt(
        twoClkRegAddrT address_) :
        address(address_)
    {}
    explicit twoClkRegAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct twoClkRegDataSt {
    twoClkRegDataT data; //

    twoClkRegDataSt() {}

    static constexpr uint16_t _bitWidth = TWO_CLK_REG_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const twoClkRegDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const twoClkRegDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  twoClkRegDataSt const & v ) {
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
    inline twoClkRegDataT _getData(void) { return( data); }
    inline void _setData(twoClkRegDataT value) { data = value; }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (twoClkRegDataT)((_src));
    }
    inline sc_bv<twoClkRegDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkRegDataSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "twoClkRegDataSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<twoClkRegDataSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit twoClkRegDataSt(const sc_bv<twoClkRegDataSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit twoClkRegDataSt(
        twoClkRegDataT data_) :
        data(data_)
    {}
    explicit twoClkRegDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct twoClkTblAddrSt {
    twoClkTblAddrBitsT address; //

    twoClkTblAddrSt() {}

    static constexpr uint16_t _bitWidth = TWO_CLK_TBL_WORDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const twoClkTblAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const twoClkTblAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  twoClkTblAddrSt const & v ) {
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
    inline twoClkTblAddrBitsT _getAddress(void) { return( address); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (twoClkTblAddrBitsT)((_src) & ((1ULL << 3) - 1));
    }
    inline sc_bv<twoClkTblAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkTblAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "twoClkTblAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<twoClkTblAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit twoClkTblAddrSt(const sc_bv<twoClkTblAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit twoClkTblAddrSt(
        twoClkTblAddrBitsT address_) :
        address(address_)
    {}
    explicit twoClkTblAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct twoClkTblSt {
    twoClkTblLoT lo; //row bits [31:0]
    twoClkTblHiT hi; //row bits [47:32]

    twoClkTblSt() {}

    static constexpr uint16_t _bitWidth = 32 + 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const twoClkTblSt & rhs) const {
        bool ret = true;
        ret = ret && (hi == rhs.hi);
        ret = ret && (lo == rhs.lo);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const twoClkTblSt & v, const std::string & NAME ) {
        sc_trace(tf,v.hi, NAME + ".hi");
        sc_trace(tf,v.lo, NAME + ".lo");
    }
    inline friend ostream& operator << ( ostream& os,  twoClkTblSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("hi:0x{:04x} lo:0x{:08x}",
           (uint64_t) hi,
           (uint64_t) lo
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = lo;
        _ret |= (uint64_t)hi << (32 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        lo = (twoClkTblLoT)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += 32;
        hi = (twoClkTblHiT)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
    }
    inline sc_bv<twoClkTblSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkTblSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "twoClkTblSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<twoClkTblSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit twoClkTblSt(const sc_bv<twoClkTblSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit twoClkTblSt(
        twoClkTblLoT lo_,
        twoClkTblHiT hi_) :
        lo(lo_),
        hi(hi_)
    {}
    explicit twoClkTblSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct twoClkLutAddrSt {
    twoClkLutAddrBitsT address; //

    twoClkLutAddrSt() {}

    static constexpr uint16_t _bitWidth = TWO_CLK_LUT_WORDS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const twoClkLutAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const twoClkLutAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  twoClkLutAddrSt const & v ) {
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
    inline twoClkLutAddrBitsT _getAddress(void) { return( address); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (twoClkLutAddrBitsT)((_src) & ((1ULL << 2) - 1));
    }
    inline sc_bv<twoClkLutAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkLutAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "twoClkLutAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<twoClkLutAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit twoClkLutAddrSt(const sc_bv<twoClkLutAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit twoClkLutAddrSt(
        twoClkLutAddrBitsT address_) :
        address(address_)
    {}
    explicit twoClkLutAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct twoClkLutSt {
    twoClkLutValT val; //value firmware loads

    twoClkLutSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const twoClkLutSt & rhs) const {
        bool ret = true;
        ret = ret && (val == rhs.val);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const twoClkLutSt & v, const std::string & NAME ) {
        sc_trace(tf,v.val, NAME + ".val");
    }
    inline friend ostream& operator << ( ostream& os,  twoClkLutSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("val:0x{:04x}",
           (uint64_t) val
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = val;
    }
    inline void unpack(const _packedSt &_src)
    {
        val = (twoClkLutValT)((_src));
    }
    inline sc_bv<twoClkLutSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkLutSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "twoClkLutSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<twoClkLutSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit twoClkLutSt(const sc_bv<twoClkLutSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit twoClkLutSt(
        twoClkLutValT val_) :
        val(val_)
    {}
    explicit twoClkLutSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct twoClkStatsSt {
    twoClkLutValT val; //lut value plus one, written by the sweep

    twoClkStatsSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const twoClkStatsSt & rhs) const {
        bool ret = true;
        ret = ret && (val == rhs.val);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const twoClkStatsSt & v, const std::string & NAME ) {
        sc_trace(tf,v.val, NAME + ".val");
    }
    inline friend ostream& operator << ( ostream& os,  twoClkStatsSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("val:0x{:04x}",
           (uint64_t) val
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = val;
    }
    inline void unpack(const _packedSt &_src)
    {
        val = (twoClkLutValT)((_src));
    }
    inline sc_bv<twoClkStatsSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkStatsSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "twoClkStatsSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<twoClkStatsSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit twoClkStatsSt(const sc_bv<twoClkStatsSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit twoClkStatsSt(
        twoClkLutValT val_) :
        val(val_)
    {}
    explicit twoClkStatsSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace twoClk_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace twoClk_ns {
inline sc_bv<twoClkRegAddrSt::_bitWidth> testRefPack(const twoClkRegAddrSt &x);
inline void testRefUnpack(twoClkRegAddrSt &x, const sc_bv<twoClkRegAddrSt::_bitWidth> &packed_data);
inline sc_bv<twoClkRegDataSt::_bitWidth> testRefPack(const twoClkRegDataSt &x);
inline void testRefUnpack(twoClkRegDataSt &x, const sc_bv<twoClkRegDataSt::_bitWidth> &packed_data);
inline sc_bv<twoClkTblAddrSt::_bitWidth> testRefPack(const twoClkTblAddrSt &x);
inline void testRefUnpack(twoClkTblAddrSt &x, const sc_bv<twoClkTblAddrSt::_bitWidth> &packed_data);
inline sc_bv<twoClkTblSt::_bitWidth> testRefPack(const twoClkTblSt &x);
inline void testRefUnpack(twoClkTblSt &x, const sc_bv<twoClkTblSt::_bitWidth> &packed_data);
inline sc_bv<twoClkLutAddrSt::_bitWidth> testRefPack(const twoClkLutAddrSt &x);
inline void testRefUnpack(twoClkLutAddrSt &x, const sc_bv<twoClkLutAddrSt::_bitWidth> &packed_data);
inline sc_bv<twoClkLutSt::_bitWidth> testRefPack(const twoClkLutSt &x);
inline void testRefUnpack(twoClkLutSt &x, const sc_bv<twoClkLutSt::_bitWidth> &packed_data);
inline sc_bv<twoClkStatsSt::_bitWidth> testRefPack(const twoClkStatsSt &x);
inline void testRefUnpack(twoClkStatsSt &x, const sc_bv<twoClkStatsSt::_bitWidth> &packed_data);
inline sc_bv<twoClkRegAddrSt::_bitWidth> testRefPack(const twoClkRegAddrSt &x)
{
    sc_bv<twoClkRegAddrSt::_bitWidth> packed_data;
    packed_data.range(0+TWO_CLK_REG_ADDR_WIDTH-1, 0) = x.address;
    return packed_data;
}
inline void testRefUnpack(twoClkRegAddrSt &x, const sc_bv<twoClkRegAddrSt::_bitWidth> &packed_data)
{
    x.address = (twoClkRegAddrT) packed_data.range(0+TWO_CLK_REG_ADDR_WIDTH-1, 0).to_uint64();
}
inline sc_bv<twoClkRegDataSt::_bitWidth> testRefPack(const twoClkRegDataSt &x)
{
    sc_bv<twoClkRegDataSt::_bitWidth> packed_data;
    packed_data.range(0+TWO_CLK_REG_DATA_WIDTH-1, 0) = x.data;
    return packed_data;
}
inline void testRefUnpack(twoClkRegDataSt &x, const sc_bv<twoClkRegDataSt::_bitWidth> &packed_data)
{
    x.data = (twoClkRegDataT) packed_data.range(0+TWO_CLK_REG_DATA_WIDTH-1, 0).to_uint64();
}
inline sc_bv<twoClkTblAddrSt::_bitWidth> testRefPack(const twoClkTblAddrSt &x)
{
    sc_bv<twoClkTblAddrSt::_bitWidth> packed_data;
    packed_data.range(0+TWO_CLK_TBL_WORDS_LOG2-1, 0) = x.address;
    return packed_data;
}
inline void testRefUnpack(twoClkTblAddrSt &x, const sc_bv<twoClkTblAddrSt::_bitWidth> &packed_data)
{
    x.address = (twoClkTblAddrBitsT) packed_data.range(0+TWO_CLK_TBL_WORDS_LOG2-1, 0).to_uint64();
}
inline sc_bv<twoClkTblSt::_bitWidth> testRefPack(const twoClkTblSt &x)
{
    sc_bv<twoClkTblSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.lo;
    packed_data.range(32+16-1, 32) = x.hi;
    return packed_data;
}
inline void testRefUnpack(twoClkTblSt &x, const sc_bv<twoClkTblSt::_bitWidth> &packed_data)
{
    x.lo = (twoClkTblLoT) packed_data.range(0+32-1, 0).to_uint64();
    x.hi = (twoClkTblHiT) packed_data.range(32+16-1, 32).to_uint64();
}
inline sc_bv<twoClkLutAddrSt::_bitWidth> testRefPack(const twoClkLutAddrSt &x)
{
    sc_bv<twoClkLutAddrSt::_bitWidth> packed_data;
    packed_data.range(0+TWO_CLK_LUT_WORDS_LOG2-1, 0) = x.address;
    return packed_data;
}
inline void testRefUnpack(twoClkLutAddrSt &x, const sc_bv<twoClkLutAddrSt::_bitWidth> &packed_data)
{
    x.address = (twoClkLutAddrBitsT) packed_data.range(0+TWO_CLK_LUT_WORDS_LOG2-1, 0).to_uint64();
}
inline sc_bv<twoClkLutSt::_bitWidth> testRefPack(const twoClkLutSt &x)
{
    sc_bv<twoClkLutSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.val;
    return packed_data;
}
inline void testRefUnpack(twoClkLutSt &x, const sc_bv<twoClkLutSt::_bitWidth> &packed_data)
{
    x.val = (twoClkLutValT) packed_data.range(0+16-1, 0).to_uint64();
}
inline sc_bv<twoClkStatsSt::_bitWidth> testRefPack(const twoClkStatsSt &x)
{
    sc_bv<twoClkStatsSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.val;
    return packed_data;
}
inline void testRefUnpack(twoClkStatsSt &x, const sc_bv<twoClkStatsSt::_bitWidth> &packed_data)
{
    x.val = (twoClkLutValT) packed_data.range(0+16-1, 0).to_uint64();
}
} // namespace twoClk_ns
export namespace twoClk_test_ns {
class test_twoClk_structs {
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
} // namespace twoClk_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace twoClk_test_ns {
using namespace twoClk_ns;
std::string test_twoClk_structs::name(void) { return "test_twoClk_structs"; }
void test_twoClk_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<twoClkRegAddrSt>("twoClkRegAddrSt", patterns);
    roundTrip<twoClkRegDataSt>("twoClkRegDataSt", patterns);
    roundTrip<twoClkTblAddrSt>("twoClkTblAddrSt", patterns);
    roundTrip<twoClkTblSt>("twoClkTblSt", patterns);
    roundTrip<twoClkLutAddrSt>("twoClkLutAddrSt", patterns);
    roundTrip<twoClkLutSt>("twoClkLutSt", patterns);
    roundTrip<twoClkStatsSt>("twoClkStatsSt", patterns);
}
} // namespace twoClk_test_ns

// GENERATED_CODE_END
