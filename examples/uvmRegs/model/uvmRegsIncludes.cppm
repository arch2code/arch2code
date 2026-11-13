
// GENERATED_CODE_PARAM --project=uvmRegs --context=../../yaml/uvmRegs.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module uvmRegs;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace uvmRegs_ns {
//constants
inline constexpr uint32_t UVM_REGS_WORDS = 64;  // Words uDrv streams in the SystemC testbench
inline constexpr uint32_t UVM_REGS_TAB_ROWS = 8;  // Rows of uStat's tab and hist tables
inline constexpr uint32_t UVM_REGS_IDENT = 42435;  // Value of uDeep's ident register
inline constexpr uint32_t UVM_REGS_TB_OFFSET0 = 3;  // uScale0 offset uDrv programs
inline constexpr uint32_t UVM_REGS_TB_OFFSET1 = 33;  // uScale1 offset uDrv programs
inline constexpr uint32_t UVM_REGS_TB_TAB_STEP = 273;  // uDrv programs tab row i with i times this

} // namespace uvmRegs_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace uvmRegs_ns {
// types
typedef uint16_t uvmRegsWordT; // [16] Datapath word
typedef uint32_t uvmRegsBusT; // [32] Register bus address and data
template<uint32_t UVM_REGS_SCALE_W> using uvmRegsScaleT_v = uint64_t; // [max:8] Scale offset
template<typename Config> using uvmRegsScaleT = uvmRegsScaleT_v<Config::UVM_REGS_SCALE_W>;
template<uint32_t UVM_REGS_TAB_W> using uvmRegsTabT_v = uint64_t; // [max:40] Tab row
template<typename Config> using uvmRegsTabT = uvmRegsTabT_v<Config::UVM_REGS_TAB_W>;
typedef uint8_t uvmRegsIdxT; // [3] Row of tab or hist
typedef uint8_t uvmRegsBitT; // [1] One-bit flag
typedef uint8_t uvmRegsByteT; // [8] Byte register

} // namespace uvmRegs_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace uvmRegs_ns {
// enums
enum  addr_id_uvm_regs {     //Generated type for addressing regs instances
    ADDR_ID_UVM_REGS_USCALE0=0,   // uScale0 instance address
    ADDR_ID_UVM_REGS_USCALE1=1,   // uScale1 instance address
    ADDR_ID_UVM_REGS_USTAT=3,   // uStat instance address
    ADDR_ID_UVM_REGS_UBRIDGE=4,   // uBridge instance address
    ADDR_ID_UVM_REGS_UWRAP=5 }; // uWrap instance address
inline const char* addr_id_uvm_regs_prt( addr_id_uvm_regs val )
{
    switch( val )
    {
        case ADDR_ID_UVM_REGS_USCALE0: return( "ADDR_ID_UVM_REGS_USCALE0" );
        case ADDR_ID_UVM_REGS_USCALE1: return( "ADDR_ID_UVM_REGS_USCALE1" );
        case ADDR_ID_UVM_REGS_USTAT: return( "ADDR_ID_UVM_REGS_USTAT" );
        case ADDR_ID_UVM_REGS_UBRIDGE: return( "ADDR_ID_UVM_REGS_UBRIDGE" );
        case ADDR_ID_UVM_REGS_UWRAP: return( "ADDR_ID_UVM_REGS_UWRAP" );
    }
    return("!!!BADENUM!!!");
}
enum  addr_id_uvm_regs_bridge { //Generated type for addressing bridge instances
    ADDR_ID_UVM_REGS_BRIDGE_UDEEP=0 }; // uDeep instance address
inline const char* addr_id_uvm_regs_bridge_prt( addr_id_uvm_regs_bridge val )
{
    switch( val )
    {
        case ADDR_ID_UVM_REGS_BRIDGE_UDEEP: return( "ADDR_ID_UVM_REGS_BRIDGE_UDEEP" );
    }
    return("!!!BADENUM!!!");
}

} // namespace uvmRegs_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace uvmRegs_ns {
// structures
struct uvmRegsWordSt {
    uvmRegsWordT word; //Datapath word

    uvmRegsWordSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const uvmRegsWordSt & rhs) const {
        bool ret = true;
        ret = ret && (word == rhs.word);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsWordSt & v, const std::string & NAME ) {
        sc_trace(tf,v.word, NAME + ".word");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsWordSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("word:0x{:04x}",
           (uint64_t) word
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = word;
    }
    inline void unpack(const _packedSt &_src)
    {
        word = (uvmRegsWordT)((_src));
    }
    inline sc_bv<uvmRegsWordSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsWordSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsWordSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsWordSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsWordSt(const sc_bv<uvmRegsWordSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsWordSt(
        uvmRegsWordT word_) :
        word(word_)
    {}
    explicit uvmRegsWordSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmRegsAddrSt {
    uvmRegsBusT address; //

    uvmRegsAddrSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const uvmRegsAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsAddrSt const & v ) {
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
    inline uvmRegsBusT _getAddress(void) { return( address); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (uvmRegsBusT)((_src));
    }
    inline sc_bv<uvmRegsAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsAddrSt(const sc_bv<uvmRegsAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsAddrSt(
        uvmRegsBusT address_) :
        address(address_)
    {}
    explicit uvmRegsAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmRegsDataSt {
    uvmRegsBusT data; //

    uvmRegsDataSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const uvmRegsDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsDataSt const & v ) {
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
    inline uvmRegsBusT _getData(void) { return( data); }
    inline void _setData(uvmRegsBusT value) { data = value; }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (uvmRegsBusT)((_src));
    }
    inline sc_bv<uvmRegsDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsDataSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsDataSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsDataSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsDataSt(const sc_bv<uvmRegsDataSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsDataSt(
        uvmRegsBusT data_) :
        data(data_)
    {}
    explicit uvmRegsDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<uint32_t UVM_REGS_SCALE_W>
struct uvmRegsScaleSt_v {
    uvmRegsScaleT_v<UVM_REGS_SCALE_W> offset; //Added to each word

    uvmRegsScaleSt_v() {}

    static constexpr uint16_t _bitWidth = UVM_REGS_SCALE_W;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const uvmRegsScaleSt_v<UVM_REGS_SCALE_W> & rhs) const {
        bool ret = true;
        ret = ret && (offset == rhs.offset);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsScaleSt_v<UVM_REGS_SCALE_W> & v, const std::string & NAME ) {
        sc_trace(tf,v.offset, NAME + ".offset");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsScaleSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("offset:0x{:01x}",
           (uint64_t) offset
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, offset, UVM_REGS_SCALE_W);
        _pos += UVM_REGS_SCALE_W;
    }
    inline void unpack(const _packedSt &_src)
    {
        offset = (uvmRegsScaleT_v<UVM_REGS_SCALE_W>)((_src) & (~0ULL >> (64 - (UVM_REGS_SCALE_W))));
    }
    inline sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsScaleSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsScaleSt_v(const sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsScaleSt_v(
        uvmRegsScaleT_v<UVM_REGS_SCALE_W> offset_) :
        offset(offset_)
    {}
    explicit uvmRegsScaleSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using uvmRegsScaleSt = uvmRegsScaleSt_v<Config::UVM_REGS_SCALE_W>;
struct uvmRegsModeSt {
    uvmRegsBitT invert; //Invert each word after the tab

    uvmRegsModeSt() {}

    static constexpr uint16_t _bitWidth = 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const uvmRegsModeSt & rhs) const {
        bool ret = true;
        ret = ret && (invert == rhs.invert);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsModeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.invert, NAME + ".invert");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsModeSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("invert:0x{:01x}",
           (uint64_t) invert
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = invert;
    }
    inline void unpack(const _packedSt &_src)
    {
        invert = (uvmRegsBitT)((_src) & 1);
    }
    inline bool sc_pack(void) const
    {
        bool packed_data;
        packed_data = (bool) invert;
        return packed_data;
    }
    inline void sc_unpack(bool packed_data)
    {
        invert = (uvmRegsBitT) packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsModeSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsModeSt(bool packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsModeSt(
        uvmRegsBitT invert_) :
        invert(invert_)
    {}
    explicit uvmRegsModeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmRegsCountSt {
    uvmRegsWordT count; //Words passed, wrapping

    uvmRegsCountSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const uvmRegsCountSt & rhs) const {
        bool ret = true;
        ret = ret && (count == rhs.count);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsCountSt & v, const std::string & NAME ) {
        sc_trace(tf,v.count, NAME + ".count");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsCountSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("count:0x{:04x}",
           (uint64_t) count
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = count;
    }
    inline void unpack(const _packedSt &_src)
    {
        count = (uvmRegsWordT)((_src));
    }
    inline sc_bv<uvmRegsCountSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsCountSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsCountSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsCountSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsCountSt(const sc_bv<uvmRegsCountSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsCountSt(
        uvmRegsWordT count_) :
        count(count_)
    {}
    explicit uvmRegsCountSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmRegsScratchSt {
    uvmRegsWordT value; //Scratch value

    uvmRegsScratchSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const uvmRegsScratchSt & rhs) const {
        bool ret = true;
        ret = ret && (value == rhs.value);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsScratchSt & v, const std::string & NAME ) {
        sc_trace(tf,v.value, NAME + ".value");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsScratchSt const & v ) {
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
        value = (uvmRegsWordT)((_src));
    }
    inline sc_bv<uvmRegsScratchSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsScratchSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsScratchSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsScratchSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsScratchSt(const sc_bv<uvmRegsScratchSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsScratchSt(
        uvmRegsWordT value_) :
        value(value_)
    {}
    explicit uvmRegsScratchSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<uint32_t UVM_REGS_TAB_W>
struct uvmRegsTabSt_v {
    uvmRegsTabT_v<UVM_REGS_TAB_W> entry; //XORed into each word whose low bits select the row

    uvmRegsTabSt_v() {}

    static constexpr uint16_t _bitWidth = UVM_REGS_TAB_W;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const uvmRegsTabSt_v<UVM_REGS_TAB_W> & rhs) const {
        bool ret = true;
        ret = ret && (entry == rhs.entry);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsTabSt_v<UVM_REGS_TAB_W> & v, const std::string & NAME ) {
        sc_trace(tf,v.entry, NAME + ".entry");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsTabSt_v const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("entry:0x{:03x}",
           (uint64_t) entry
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, entry, UVM_REGS_TAB_W);
        _pos += UVM_REGS_TAB_W;
    }
    inline void unpack(const _packedSt &_src)
    {
        entry = (uvmRegsTabT_v<UVM_REGS_TAB_W>)((_src) & (~0ULL >> (64 - (UVM_REGS_TAB_W))));
    }
    inline sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsTabSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsTabSt_v(const sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsTabSt_v(
        uvmRegsTabT_v<UVM_REGS_TAB_W> entry_) :
        entry(entry_)
    {}
    explicit uvmRegsTabSt_v(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config> using uvmRegsTabSt = uvmRegsTabSt_v<Config::UVM_REGS_TAB_W>;
struct uvmRegsIdxSt {
    uvmRegsIdxT idx; //Row

    uvmRegsIdxSt() {}

    static constexpr uint16_t _bitWidth = 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const uvmRegsIdxSt & rhs) const {
        bool ret = true;
        ret = ret && (idx == rhs.idx);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsIdxSt & v, const std::string & NAME ) {
        sc_trace(tf,v.idx, NAME + ".idx");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsIdxSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("idx:0x{:01x}",
           (uint64_t) idx
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = idx;
    }
    inline void unpack(const _packedSt &_src)
    {
        idx = (uvmRegsIdxT)((_src) & ((1ULL << 3) - 1));
    }
    inline sc_bv<uvmRegsIdxSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsIdxSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsIdxSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsIdxSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsIdxSt(const sc_bv<uvmRegsIdxSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsIdxSt(
        uvmRegsIdxT idx_) :
        idx(idx_)
    {}
    explicit uvmRegsIdxSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmRegsIdentSt {
    uvmRegsWordT ident; //Fixed identifier

    uvmRegsIdentSt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const uvmRegsIdentSt & rhs) const {
        bool ret = true;
        ret = ret && (ident == rhs.ident);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsIdentSt & v, const std::string & NAME ) {
        sc_trace(tf,v.ident, NAME + ".ident");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsIdentSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("ident:0x{:04x}",
           (uint64_t) ident
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = ident;
    }
    inline void unpack(const _packedSt &_src)
    {
        ident = (uvmRegsWordT)((_src));
    }
    inline sc_bv<uvmRegsIdentSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsIdentSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsIdentSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsIdentSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsIdentSt(const sc_bv<uvmRegsIdentSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsIdentSt(
        uvmRegsWordT ident_) :
        ident(ident_)
    {}
    explicit uvmRegsIdentSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmRegsByteSt {
    uvmRegsByteT value; //Byte

    uvmRegsByteSt() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const uvmRegsByteSt & rhs) const {
        bool ret = true;
        ret = ret && (value == rhs.value);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmRegsByteSt & v, const std::string & NAME ) {
        sc_trace(tf,v.value, NAME + ".value");
    }
    inline friend ostream& operator << ( ostream& os,  uvmRegsByteSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("value:0x{:02x}",
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
        value = (uvmRegsByteT)((_src));
    }
    inline sc_bv<uvmRegsByteSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmRegsByteSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmRegsByteSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmRegsByteSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmRegsByteSt(const sc_bv<uvmRegsByteSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmRegsByteSt(
        uvmRegsByteT value_) :
        value(value_)
    {}
    explicit uvmRegsByteSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace uvmRegs_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace uvmRegs_ns {
inline sc_bv<uvmRegsWordSt::_bitWidth> testRefPack(const uvmRegsWordSt &x);
inline void testRefUnpack(uvmRegsWordSt &x, const sc_bv<uvmRegsWordSt::_bitWidth> &packed_data);
inline sc_bv<uvmRegsAddrSt::_bitWidth> testRefPack(const uvmRegsAddrSt &x);
inline void testRefUnpack(uvmRegsAddrSt &x, const sc_bv<uvmRegsAddrSt::_bitWidth> &packed_data);
inline sc_bv<uvmRegsDataSt::_bitWidth> testRefPack(const uvmRegsDataSt &x);
inline void testRefUnpack(uvmRegsDataSt &x, const sc_bv<uvmRegsDataSt::_bitWidth> &packed_data);
template<uint32_t UVM_REGS_SCALE_W> inline sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> testRefPack(const uvmRegsScaleSt_v<UVM_REGS_SCALE_W> &x);
template<uint32_t UVM_REGS_SCALE_W> inline void testRefUnpack(uvmRegsScaleSt_v<UVM_REGS_SCALE_W> &x, const sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> &packed_data);
inline sc_bv<uvmRegsModeSt::_bitWidth> testRefPack(const uvmRegsModeSt &x);
inline void testRefUnpack(uvmRegsModeSt &x, const sc_bv<uvmRegsModeSt::_bitWidth> &packed_data);
inline sc_bv<uvmRegsCountSt::_bitWidth> testRefPack(const uvmRegsCountSt &x);
inline void testRefUnpack(uvmRegsCountSt &x, const sc_bv<uvmRegsCountSt::_bitWidth> &packed_data);
inline sc_bv<uvmRegsScratchSt::_bitWidth> testRefPack(const uvmRegsScratchSt &x);
inline void testRefUnpack(uvmRegsScratchSt &x, const sc_bv<uvmRegsScratchSt::_bitWidth> &packed_data);
template<uint32_t UVM_REGS_TAB_W> inline sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> testRefPack(const uvmRegsTabSt_v<UVM_REGS_TAB_W> &x);
template<uint32_t UVM_REGS_TAB_W> inline void testRefUnpack(uvmRegsTabSt_v<UVM_REGS_TAB_W> &x, const sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> &packed_data);
inline sc_bv<uvmRegsIdxSt::_bitWidth> testRefPack(const uvmRegsIdxSt &x);
inline void testRefUnpack(uvmRegsIdxSt &x, const sc_bv<uvmRegsIdxSt::_bitWidth> &packed_data);
inline sc_bv<uvmRegsIdentSt::_bitWidth> testRefPack(const uvmRegsIdentSt &x);
inline void testRefUnpack(uvmRegsIdentSt &x, const sc_bv<uvmRegsIdentSt::_bitWidth> &packed_data);
inline sc_bv<uvmRegsByteSt::_bitWidth> testRefPack(const uvmRegsByteSt &x);
inline void testRefUnpack(uvmRegsByteSt &x, const sc_bv<uvmRegsByteSt::_bitWidth> &packed_data);
inline sc_bv<uvmRegsWordSt::_bitWidth> testRefPack(const uvmRegsWordSt &x)
{
    sc_bv<uvmRegsWordSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.word;
    return packed_data;
}
inline void testRefUnpack(uvmRegsWordSt &x, const sc_bv<uvmRegsWordSt::_bitWidth> &packed_data)
{
    x.word = (uvmRegsWordT) packed_data.range(0+16-1, 0).to_uint64();
}
inline sc_bv<uvmRegsAddrSt::_bitWidth> testRefPack(const uvmRegsAddrSt &x)
{
    sc_bv<uvmRegsAddrSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.address;
    return packed_data;
}
inline void testRefUnpack(uvmRegsAddrSt &x, const sc_bv<uvmRegsAddrSt::_bitWidth> &packed_data)
{
    x.address = (uvmRegsBusT) packed_data.range(0+32-1, 0).to_uint64();
}
inline sc_bv<uvmRegsDataSt::_bitWidth> testRefPack(const uvmRegsDataSt &x)
{
    sc_bv<uvmRegsDataSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.data;
    return packed_data;
}
inline void testRefUnpack(uvmRegsDataSt &x, const sc_bv<uvmRegsDataSt::_bitWidth> &packed_data)
{
    x.data = (uvmRegsBusT) packed_data.range(0+32-1, 0).to_uint64();
}
template<uint32_t UVM_REGS_SCALE_W> inline sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> testRefPack(const uvmRegsScaleSt_v<UVM_REGS_SCALE_W> &x)
{
    sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+UVM_REGS_SCALE_W-1, _pos) = x.offset;
    _pos += UVM_REGS_SCALE_W;
    return packed_data;
}
template<uint32_t UVM_REGS_SCALE_W> inline void testRefUnpack(uvmRegsScaleSt_v<UVM_REGS_SCALE_W> &x, const sc_bv<uvmRegsScaleSt_v<UVM_REGS_SCALE_W>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.offset = (uvmRegsScaleT_v<UVM_REGS_SCALE_W>) packed_data.range(_pos+UVM_REGS_SCALE_W-1, _pos).to_uint64();
    _pos += UVM_REGS_SCALE_W;
}
inline sc_bv<uvmRegsModeSt::_bitWidth> testRefPack(const uvmRegsModeSt &x)
{
    sc_bv<uvmRegsModeSt::_bitWidth> packed_data;
    packed_data.range(0+1-1, 0) = x.invert;
    return packed_data;
}
inline void testRefUnpack(uvmRegsModeSt &x, const sc_bv<uvmRegsModeSt::_bitWidth> &packed_data)
{
    x.invert = (uvmRegsBitT) packed_data.range(0+1-1, 0).to_uint64();
}
inline sc_bv<uvmRegsCountSt::_bitWidth> testRefPack(const uvmRegsCountSt &x)
{
    sc_bv<uvmRegsCountSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.count;
    return packed_data;
}
inline void testRefUnpack(uvmRegsCountSt &x, const sc_bv<uvmRegsCountSt::_bitWidth> &packed_data)
{
    x.count = (uvmRegsWordT) packed_data.range(0+16-1, 0).to_uint64();
}
inline sc_bv<uvmRegsScratchSt::_bitWidth> testRefPack(const uvmRegsScratchSt &x)
{
    sc_bv<uvmRegsScratchSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.value;
    return packed_data;
}
inline void testRefUnpack(uvmRegsScratchSt &x, const sc_bv<uvmRegsScratchSt::_bitWidth> &packed_data)
{
    x.value = (uvmRegsWordT) packed_data.range(0+16-1, 0).to_uint64();
}
template<uint32_t UVM_REGS_TAB_W> inline sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> testRefPack(const uvmRegsTabSt_v<UVM_REGS_TAB_W> &x)
{
    sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> packed_data;
    uint16_t _pos{0};
    packed_data.range(_pos+UVM_REGS_TAB_W-1, _pos) = x.entry;
    _pos += UVM_REGS_TAB_W;
    return packed_data;
}
template<uint32_t UVM_REGS_TAB_W> inline void testRefUnpack(uvmRegsTabSt_v<UVM_REGS_TAB_W> &x, const sc_bv<uvmRegsTabSt_v<UVM_REGS_TAB_W>::_bitWidth> &packed_data)
{
    uint16_t _pos{0};
    x.entry = (uvmRegsTabT_v<UVM_REGS_TAB_W>) packed_data.range(_pos+UVM_REGS_TAB_W-1, _pos).to_uint64();
    _pos += UVM_REGS_TAB_W;
}
inline sc_bv<uvmRegsIdxSt::_bitWidth> testRefPack(const uvmRegsIdxSt &x)
{
    sc_bv<uvmRegsIdxSt::_bitWidth> packed_data;
    packed_data.range(0+3-1, 0) = x.idx;
    return packed_data;
}
inline void testRefUnpack(uvmRegsIdxSt &x, const sc_bv<uvmRegsIdxSt::_bitWidth> &packed_data)
{
    x.idx = (uvmRegsIdxT) packed_data.range(0+3-1, 0).to_uint64();
}
inline sc_bv<uvmRegsIdentSt::_bitWidth> testRefPack(const uvmRegsIdentSt &x)
{
    sc_bv<uvmRegsIdentSt::_bitWidth> packed_data;
    packed_data.range(0+16-1, 0) = x.ident;
    return packed_data;
}
inline void testRefUnpack(uvmRegsIdentSt &x, const sc_bv<uvmRegsIdentSt::_bitWidth> &packed_data)
{
    x.ident = (uvmRegsWordT) packed_data.range(0+16-1, 0).to_uint64();
}
inline sc_bv<uvmRegsByteSt::_bitWidth> testRefPack(const uvmRegsByteSt &x)
{
    sc_bv<uvmRegsByteSt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.value;
    return packed_data;
}
inline void testRefUnpack(uvmRegsByteSt &x, const sc_bv<uvmRegsByteSt::_bitWidth> &packed_data)
{
    x.value = (uvmRegsByteT) packed_data.range(0+8-1, 0).to_uint64();
}
} // namespace uvmRegs_ns
export namespace uvmRegs_test_ns {
class test_uvmRegs_structs {
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
} // namespace uvmRegs_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace uvmRegs_test_ns {
using namespace uvmRegs_ns;
struct uvmRegsTestConfigDefault {
    static constexpr uint32_t UVM_REGS_SCALE_W = 4;
    static constexpr uint32_t UVM_REGS_TAB_W = 12;
};
struct uvmRegsTestConfigMid {
    static constexpr uint32_t UVM_REGS_SCALE_W = 4;
    static constexpr uint32_t UVM_REGS_TAB_W = 20;
};
struct uvmRegsTestConfigMax {
    static constexpr uint32_t UVM_REGS_SCALE_W = 8;
    static constexpr uint32_t UVM_REGS_TAB_W = 40;
};
std::string test_uvmRegs_structs::name(void) { return "test_uvmRegs_structs"; }
void test_uvmRegs_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<uvmRegsWordSt>("uvmRegsWordSt", patterns);
    roundTrip<uvmRegsAddrSt>("uvmRegsAddrSt", patterns);
    roundTrip<uvmRegsDataSt>("uvmRegsDataSt", patterns);
    roundTrip<uvmRegsScaleSt<uvmRegsTestConfigDefault>>("uvmRegsScaleSt", patterns);
    roundTrip<uvmRegsScaleSt<uvmRegsTestConfigMid>>("uvmRegsScaleSt", patterns);
    roundTrip<uvmRegsScaleSt<uvmRegsTestConfigMax>>("uvmRegsScaleSt", patterns);
    roundTrip<uvmRegsModeSt>("uvmRegsModeSt", patterns);
    roundTrip<uvmRegsCountSt>("uvmRegsCountSt", patterns);
    roundTrip<uvmRegsScratchSt>("uvmRegsScratchSt", patterns);
    roundTrip<uvmRegsTabSt<uvmRegsTestConfigDefault>>("uvmRegsTabSt", patterns);
    roundTrip<uvmRegsTabSt<uvmRegsTestConfigMid>>("uvmRegsTabSt", patterns);
    roundTrip<uvmRegsTabSt<uvmRegsTestConfigMax>>("uvmRegsTabSt", patterns);
    roundTrip<uvmRegsIdxSt>("uvmRegsIdxSt", patterns);
    roundTrip<uvmRegsIdentSt>("uvmRegsIdentSt", patterns);
    roundTrip<uvmRegsByteSt>("uvmRegsByteSt", patterns);
}
} // namespace uvmRegs_test_ns

// GENERATED_CODE_END
