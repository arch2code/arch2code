
// GENERATED_CODE_PARAM --context=ip.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module ip;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_ns {
//constants
const uint32_t IP_FIXED_NIBBLE_COUNT = 5;  // Fixed array length for non-parameterized type tests
const uint32_t IP_FIXED_PAIR_COUNT = 2;  // Fixed nested-structure array length
const uint32_t IP_FIXED_WORD_COUNT = 6;  // Derived fixed array length
const uint32_t IP_FIXED_DEPTH = 9;  // Fixed depth for widthLog2 and widthLog2minus1 tests

} // namespace ip_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_ns {
// types
template<typename Config> struct ipDataT { uint64_t word[ 2 ]; }; // [max:128] IP data word, parameterizable
typedef uint8_t enableT; // [1] Single enable bit
template<typename Config> using ipMemAddrT = uint64_t; // [max:5] Index into ipMem (0 .. IP_MEM_DEPTH-1)
typedef uint8_t ipFixedT; // [8] Fixed 8-bit byte (non-parameterizable)
typedef uint8_t ipFixedAddrT; // [8] Fixed 8-bit address index (non-parameterizable)
typedef uint8_t ipNibbleT; // [4] Fixed unsigned nibble
typedef int8_t ipSignedNibbleT; // [4] Fixed signed nibble
typedef int8_t ipSigned3T; // [3] Fixed signed 3-bit value
typedef uint8_t ipUnsigned5T; // [5] Fixed unsigned 5-bit value
typedef uint16_t ipUnsigned9T; // [9] Fixed unsigned 9-bit value
typedef uint16_t ipWordT; // [16] Fixed 16-bit word
typedef uint64_t ipWide37T; // [37] Fixed 37-bit value crossing a 32-bit boundary
typedef uint8_t ipFixedCountT; // [4] Fixed count field wide enough for 0..IP_FIXED_DEPTH
typedef uint8_t ipFixedIndexT; // [4] Fixed index field wide enough for 0..IP_FIXED_DEPTH-1

} // namespace ip_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_ns {
// enums
enum  ipModeT {              //IP operating mode
    IP_MODE_OFF=0,           // Off
    IP_MODE_LOW=1,           // Low power
    IP_MODE_HIGH=2 };        // High performance
inline const char* ipModeT_prt( ipModeT val )
{
    switch( val )
    {
        case IP_MODE_OFF: return( "IP_MODE_OFF" );
        case IP_MODE_LOW: return( "IP_MODE_LOW" );
        case IP_MODE_HIGH: return( "IP_MODE_HIGH" );
    }
    return("!!!BADENUM!!!");
}
enum  ipFixedStatusT {       //Fixed status enum
    IP_STATUS_IDLE=0,        // Idle
    IP_STATUS_BUSY=1,        // Busy
    IP_STATUS_DONE=4 };      // Done
inline const char* ipFixedStatusT_prt( ipFixedStatusT val )
{
    switch( val )
    {
        case IP_STATUS_IDLE: return( "IP_STATUS_IDLE" );
        case IP_STATUS_BUSY: return( "IP_STATUS_BUSY" );
        case IP_STATUS_DONE: return( "IP_STATUS_DONE" );
    }
    return("!!!BADENUM!!!");
}
enum  ipFixedOpcodeT {       //Fixed-width opcode enum
    IP_OP_NOP=0,             // No operation
    IP_OP_LOAD=3,            // Load
    IP_OP_STORE=9 };         // Store
inline const char* ipFixedOpcodeT_prt( ipFixedOpcodeT val )
{
    switch( val )
    {
        case IP_OP_NOP: return( "IP_OP_NOP" );
        case IP_OP_LOAD: return( "IP_OP_LOAD" );
        case IP_OP_STORE: return( "IP_OP_STORE" );
    }
    return("!!!BADENUM!!!");
}

} // namespace ip_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ip_ns {
// structures
template<typename Config>
struct ipDataSt {
    ipDataT<Config> data; //Data word
    enableT marker; //Marker bit expected after the data payload

    ipDataSt() {}

    static constexpr uint16_t _bitWidth = Config::IP_DATA_WIDTH + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline bool operator == (const ipDataSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (marker == rhs.marker);
        ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
        ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipDataSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.marker, NAME + ".marker");
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  ipDataSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("marker:0x{:01x} data:0x{:02x}{:016x}",
           (uint64_t) marker,
           data.word[1],
           data.word[0]
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipDataSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&data, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, marker, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&data, 0, sizeof(data));
        unpack_bits((uint64_t *)&data, 0, (uint64_t *)&_src, _pos, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
        marker = (enableT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    inline sc_bv<ipDataSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipDataSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        if (Config::IP_DATA_WIDTH > 0) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 0));
            packed_data.range(_pos + 0 + _bits - 1, _pos + 0) = data.word[0];
        }
        if (Config::IP_DATA_WIDTH > 64) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 64));
            packed_data.range(_pos + 64 + _bits - 1, _pos + 64) = data.word[1];
        }
        _pos += Config::IP_DATA_WIDTH;
        packed_data.range(_pos+1-1, _pos) = marker;
        _pos += 1;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipDataSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        if (Config::IP_DATA_WIDTH > 0) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 0));
            data.word[0] = (uint64_t) packed_data.range(_pos + 0 + _bits - 1, _pos + 0).to_uint64();
        }
        if (Config::IP_DATA_WIDTH > 64) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 64));
            data.word[1] = (uint64_t) packed_data.range(_pos + 64 + _bits - 1, _pos + 64).to_uint64();
        }
        _pos += Config::IP_DATA_WIDTH;
        marker = (enableT) packed_data.range(_pos+1-1, _pos).to_uint64();
        _pos += 1;
    }
    explicit ipDataSt(sc_bv<ipDataSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipDataSt(
        ipDataT<Config> data_,
        enableT marker_) :
        data(data_),
        marker(marker_)
    {}
    explicit ipDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct ipCfgSt {
    ipDataT<Config> threshold; //Threshold value
    ipModeT mode; //Operating mode
    enableT enable; //Enable bit

    ipCfgSt() {}

    static constexpr uint16_t _bitWidth = Config::IP_DATA_WIDTH + 2 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline bool operator == (const ipCfgSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (enable == rhs.enable);
        ret = ret && (mode == rhs.mode);
        ret = ret && (threshold.word[ 0 ] == rhs.threshold.word[ 0 ]);
        ret = ret && (threshold.word[ 1 ] == rhs.threshold.word[ 1 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipCfgSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.enable, NAME + ".enable");
        sc_trace(tf,v.mode, NAME + ".mode");
        sc_trace(tf,v.threshold.word[ 0 ], NAME + ".threshold.word[ 0 ]");
        sc_trace(tf,v.threshold.word[ 1 ], NAME + ".threshold.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  ipCfgSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("enable:0x{:01x} mode:{} threshold:0x{:02x}{:016x}",
           (uint64_t) enable,
           ipModeT_prt( mode ),
           threshold.word[1],
           threshold.word[0]
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipCfgSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&threshold, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
        pack_bits((uint64_t *)&_ret, _pos, mode, 2);
        _pos += 2;
        pack_bits((uint64_t *)&_ret, _pos, enable, 1);
        _pos += 1;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&threshold, 0, sizeof(threshold));
        unpack_bits((uint64_t *)&threshold, 0, (uint64_t *)&_src, _pos, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
        mode = (ipModeT)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 2) - 1));
        _pos += 2;
        enable = (enableT)((_src[ _pos >> 6 ] >> (_pos & 63)) & 1);
    }
    inline sc_bv<ipCfgSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipCfgSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        if (Config::IP_DATA_WIDTH > 0) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 0));
            packed_data.range(_pos + 0 + _bits - 1, _pos + 0) = threshold.word[0];
        }
        if (Config::IP_DATA_WIDTH > 64) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 64));
            packed_data.range(_pos + 64 + _bits - 1, _pos + 64) = threshold.word[1];
        }
        _pos += Config::IP_DATA_WIDTH;
        packed_data.range(_pos+2-1, _pos) = mode;
        _pos += 2;
        packed_data.range(_pos+1-1, _pos) = enable;
        _pos += 1;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipCfgSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        if (Config::IP_DATA_WIDTH > 0) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 0));
            threshold.word[0] = (uint64_t) packed_data.range(_pos + 0 + _bits - 1, _pos + 0).to_uint64();
        }
        if (Config::IP_DATA_WIDTH > 64) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 64));
            threshold.word[1] = (uint64_t) packed_data.range(_pos + 64 + _bits - 1, _pos + 64).to_uint64();
        }
        _pos += Config::IP_DATA_WIDTH;
        mode = (ipModeT) packed_data.range(_pos+2-1, _pos).to_uint64();
        _pos += 2;
        enable = (enableT) packed_data.range(_pos+1-1, _pos).to_uint64();
        _pos += 1;
    }
    explicit ipCfgSt(sc_bv<ipCfgSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipCfgSt(
        ipDataT<Config> threshold_,
        ipModeT mode_,
        enableT enable_) :
        threshold(threshold_),
        mode(mode_),
        enable(enable_)
    {}
    explicit ipCfgSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct ipMemSt {
    ipDataT<Config> data; //Data word

    ipMemSt() {}

    static constexpr uint16_t _bitWidth = Config::IP_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const ipMemSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
        ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipMemSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
    }
    inline friend ostream& operator << ( ostream& os,  ipMemSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:02x}{:016x}",
           data.word[1],
           data.word[0]
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipMemSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&data, Config::IP_DATA_WIDTH);
        _pos += Config::IP_DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        memset((uint64_t *)&data, 0, sizeof(data));
        unpack_bits((uint64_t *)&data, 0, (uint64_t *)&_src, _pos, Config::IP_DATA_WIDTH);
    }
    inline sc_bv<ipMemSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipMemSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        if (Config::IP_DATA_WIDTH > 0) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 0));
            packed_data.range(_pos + 0 + _bits - 1, _pos + 0) = data.word[0];
        }
        if (Config::IP_DATA_WIDTH > 64) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 64));
            packed_data.range(_pos + 64 + _bits - 1, _pos + 64) = data.word[1];
        }
        _pos += Config::IP_DATA_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipMemSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        if (Config::IP_DATA_WIDTH > 0) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 0));
            data.word[0] = (uint64_t) packed_data.range(_pos + 0 + _bits - 1, _pos + 0).to_uint64();
        }
        if (Config::IP_DATA_WIDTH > 64) {
            uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 64));
            data.word[1] = (uint64_t) packed_data.range(_pos + 64 + _bits - 1, _pos + 64).to_uint64();
        }
        _pos += Config::IP_DATA_WIDTH;
    }
    explicit ipMemSt(sc_bv<ipMemSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipMemSt(
        ipDataT<Config> data_) :
        data(data_)
    {}
    explicit ipMemSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct ipMemAddrSt {
    ipMemAddrT<Config> address; //Memory address

    ipMemAddrSt() {}

    static constexpr uint16_t _bitWidth = clog2(Config::IP_MEM_DEPTH);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const ipMemAddrSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipMemAddrSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  ipMemAddrSt const & v ) {
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
        memset(&_ret, 0, ipMemAddrSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, address, clog2(Config::IP_MEM_DEPTH));
        _pos += clog2(Config::IP_MEM_DEPTH);
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ipMemAddrT<Config>)((_src) & ((1ULL << clog2(Config::IP_MEM_DEPTH)) - 1));
    }
    inline sc_bv<ipMemAddrSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipMemAddrSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+clog2(Config::IP_MEM_DEPTH)-1, _pos) = address;
        _pos += clog2(Config::IP_MEM_DEPTH);
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipMemAddrSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        address = (ipMemAddrT<Config>) packed_data.range(_pos+clog2(Config::IP_MEM_DEPTH)-1, _pos).to_uint64();
        _pos += clog2(Config::IP_MEM_DEPTH);
    }
    explicit ipMemAddrSt(sc_bv<ipMemAddrSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipMemAddrSt(
        ipMemAddrT<Config> address_) :
        address(address_)
    {}
    explicit ipMemAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct ipBurstSt {
    ipDataT<Config> samples[Config::IP_MEM_DEPTH]; //Burst of parameterizable samples

    ipBurstSt() {}

    static constexpr uint16_t _bitWidth = Config::IP_DATA_WIDTH*Config::IP_MEM_DEPTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[64];
    inline bool operator == (const ipBurstSt<Config> & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<Config::IP_MEM_DEPTH; i++) {
            ret = ret && (samples[i].word[ 0 ] == rhs.samples[i].word[ 0 ]);
            ret = ret && (samples[i].word[ 1 ] == rhs.samples[i].word[ 1 ]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipBurstSt<Config> & v, const std::string & NAME ) {
        for(unsigned int i=0; i<Config::IP_MEM_DEPTH; i++) {
            sc_trace(tf,v.samples[i].word[ 0 ], NAME + ".samples[i].word[ 0 ]");
            sc_trace(tf,v.samples[i].word[ 1 ], NAME + ".samples[i].word[ 1 ]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  ipBurstSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("samples[0:15]: {}",
           static2DArrayPrt<ipDataT<Config>, uint64_t, Config::IP_MEM_DEPTH, 2>(samples, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipBurstSt<Config>::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<Config::IP_MEM_DEPTH; i++) {
            pack_bits((uint64_t *)&_ret, _pos, (uint64_t *)&samples[i], Config::IP_DATA_WIDTH);
            _pos += Config::IP_DATA_WIDTH;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<Config::IP_MEM_DEPTH; i++) {
            uint16_t _bits = Config::IP_DATA_WIDTH;
            uint16_t _consume;
            memset((uint64_t *)&samples[i], 0, sizeof(samples[i]));
            unpack_bits((uint64_t *)&samples[i], 0, (uint64_t *)&_src, _pos, Config::IP_DATA_WIDTH);
            _pos += Config::IP_DATA_WIDTH;
        }
    }
    inline sc_bv<ipBurstSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipBurstSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        for(unsigned int i=0; i<Config::IP_MEM_DEPTH; i++) {
            if (Config::IP_DATA_WIDTH > 0) {
                uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 0));
                packed_data.range(_pos + 0 + _bits - 1, _pos + 0) = samples[i].word[0];
            }
            if (Config::IP_DATA_WIDTH > 64) {
                uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 64));
                packed_data.range(_pos + 64 + _bits - 1, _pos + 64) = samples[i].word[1];
            }
            _pos += Config::IP_DATA_WIDTH;
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipBurstSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        for(unsigned int i=0; i<Config::IP_MEM_DEPTH; i++) {
            if (Config::IP_DATA_WIDTH > 0) {
                uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 0));
                samples[i].word[0] = (uint64_t) packed_data.range(_pos + 0 + _bits - 1, _pos + 0).to_uint64();
            }
            if (Config::IP_DATA_WIDTH > 64) {
                uint16_t _bits = std::min((uint16_t)64, (uint16_t)(Config::IP_DATA_WIDTH - 64));
                samples[i].word[1] = (uint64_t) packed_data.range(_pos + 64 + _bits - 1, _pos + 64).to_uint64();
            }
            _pos += Config::IP_DATA_WIDTH;
        }
    }
    explicit ipBurstSt(sc_bv<ipBurstSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipBurstSt(
        ipDataT<Config> samples_[Config::IP_MEM_DEPTH])
    {
        memcpy(&samples, &samples_, sizeof(samples));
    }
    explicit ipBurstSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipFixedSt {
    ipFixedT b; //Fixed byte

    ipFixedSt() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const ipFixedSt & rhs) const {
        bool ret = true;
        ret = ret && (b == rhs.b);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.b, NAME + ".b");
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("b:0x{:02x}",
           (uint64_t) b
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedSt::_byteWidth);
        _ret = b;
    }
    inline void unpack(const _packedSt &_src)
    {
        b = (ipFixedT)((_src));
    }
    inline sc_bv<ipFixedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipFixedSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = b;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipFixedSt::_bitWidth> packed_data)
    {
        b = (ipFixedT) packed_data.range(7, 0).to_uint64();
    }
    explicit ipFixedSt(sc_bv<ipFixedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipFixedSt(
        ipFixedT b_) :
        b(b_)
    {}
    explicit ipFixedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipFixedAddrSt {
    ipFixedAddrT a; //Fixed-width address

    ipFixedAddrSt() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const ipFixedAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (a == rhs.a);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedAddrSt const & v ) {
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
        memset(&_ret, 0, ipFixedAddrSt::_byteWidth);
        _ret = a;
    }
    inline void unpack(const _packedSt &_src)
    {
        a = (ipFixedAddrT)((_src));
    }
    inline sc_bv<ipFixedAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipFixedAddrSt::_bitWidth> packed_data;
        packed_data.range(7, 0) = a;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipFixedAddrSt::_bitWidth> packed_data)
    {
        a = (ipFixedAddrT) packed_data.range(7, 0).to_uint64();
    }
    explicit ipFixedAddrSt(sc_bv<ipFixedAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipFixedAddrSt(
        ipFixedAddrT a_) :
        a(a_)
    {}
    explicit ipFixedAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipFixedHeaderSt {
    ipNibbleT tag; //Fixed packet tag
    ipFixedStatusT status; //Fixed status
    ipFixedOpcodeT opcode; //Fixed opcode

    ipFixedHeaderSt() {}

    static constexpr uint16_t _bitWidth = 4 + 3 + 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const ipFixedHeaderSt & rhs) const {
        bool ret = true;
        ret = ret && (opcode == rhs.opcode);
        ret = ret && (status == rhs.status);
        ret = ret && (tag == rhs.tag);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedHeaderSt & v, const std::string & NAME ) {
        sc_trace(tf,v.opcode, NAME + ".opcode");
        sc_trace(tf,v.status, NAME + ".status");
        sc_trace(tf,v.tag, NAME + ".tag");
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedHeaderSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("opcode:{} status:{} tag:0x{:01x}",
           ipFixedOpcodeT_prt( opcode ),
           ipFixedStatusT_prt( status ),
           (uint64_t) tag
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedHeaderSt::_byteWidth);
        _ret = tag;
        _ret |= (uint16_t)status << (4 & 15);
        _ret |= (uint16_t)opcode << (7 & 15);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        tag = (ipNibbleT)((_src >> (_pos & 15)) & ((1ULL << 4) - 1));
        _pos += 4;
        status = (ipFixedStatusT)((_src >> (_pos & 15)) & ((1ULL << 3) - 1));
        _pos += 3;
        opcode = (ipFixedOpcodeT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
    }
    inline sc_bv<ipFixedHeaderSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipFixedHeaderSt::_bitWidth> packed_data;
        packed_data.range(3, 0) = tag;
        packed_data.range(6, 4) = status;
        packed_data.range(14, 7) = opcode;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipFixedHeaderSt::_bitWidth> packed_data)
    {
        tag = (ipNibbleT) packed_data.range(3, 0).to_uint64();
        status = (ipFixedStatusT) packed_data.range(6, 4).to_uint64();
        opcode = (ipFixedOpcodeT) packed_data.range(14, 7).to_uint64();
    }
    explicit ipFixedHeaderSt(sc_bv<ipFixedHeaderSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipFixedHeaderSt(
        ipNibbleT tag_,
        ipFixedStatusT status_,
        ipFixedOpcodeT opcode_) :
        tag(tag_),
        status(status_),
        opcode(opcode_)
    {}
    explicit ipFixedHeaderSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipFixedSignedSt {
    ipUnsigned9T lane; //Unsigned 9-bit field
    ipUnsigned5T magnitude; //Unsigned 5-bit field
    ipSignedNibbleT offset; //Signed 4-bit field
    ipSigned3T tiny; //Signed 3-bit field

    ipFixedSignedSt() {}

    static constexpr uint16_t _bitWidth = 9 + 5 + 4 + 3;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const ipFixedSignedSt & rhs) const {
        bool ret = true;
        ret = ret && (tiny == rhs.tiny);
        ret = ret && (offset == rhs.offset);
        ret = ret && (magnitude == rhs.magnitude);
        ret = ret && (lane == rhs.lane);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedSignedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.tiny, NAME + ".tiny");
        sc_trace(tf,v.offset, NAME + ".offset");
        sc_trace(tf,v.magnitude, NAME + ".magnitude");
        sc_trace(tf,v.lane, NAME + ".lane");
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedSignedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tiny:0x{:01x} offset:0x{:01x} magnitude:0x{:02x} lane:0x{:03x}",
           (uint64_t) tiny,
           (uint64_t) offset,
           (uint64_t) magnitude,
           (uint64_t) lane
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedSignedSt::_byteWidth);
        _ret = lane;
        _ret |= (uint32_t)magnitude << (9 & 31);
        _ret |= ((uint32_t)(offset & ((1ULL << 4) - 1))) << (14 & 31);
        _ret |= ((uint32_t)(tiny & ((1ULL << 3) - 1))) << (18 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        lane = (ipUnsigned9T)((_src >> (_pos & 31)) & ((1ULL << 9) - 1));
        _pos += 9;
        magnitude = (ipUnsigned5T)((_src >> (_pos & 31)) & ((1ULL << 5) - 1));
        _pos += 5;
        offset = (ipSignedNibbleT)((_src >> (_pos & 31)) & ((1ULL << 4) - 1));
        _pos += 4;
        // Sign extension for signed type
        if (offset & (1ULL << (4 - 1))) {
            offset = (ipSignedNibbleT)(offset | ~((1ULL << 4) - 1));
        }
        tiny = (ipSigned3T)((_src >> (_pos & 31)) & ((1ULL << 3) - 1));
        _pos += 3;
        // Sign extension for signed type
        if (tiny & (1ULL << (3 - 1))) {
            tiny = (ipSigned3T)(tiny | ~((1ULL << 3) - 1));
        }
    }
    inline sc_bv<ipFixedSignedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipFixedSignedSt::_bitWidth> packed_data;
        packed_data.range(8, 0) = lane;
        packed_data.range(13, 9) = magnitude;
        packed_data.range(17, 14) = offset;
        packed_data.range(20, 18) = tiny;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipFixedSignedSt::_bitWidth> packed_data)
    {
        lane = (ipUnsigned9T) packed_data.range(8, 0).to_uint64();
        magnitude = (ipUnsigned5T) packed_data.range(13, 9).to_uint64();
        offset = (ipSignedNibbleT) packed_data.range(17, 14).to_uint64();
        // Sign extension for signed type
        if (offset & (1ULL << (4 - 1))) {
            offset = (ipSignedNibbleT)(offset | ~((1ULL << 4) - 1));
        }
        tiny = (ipSigned3T) packed_data.range(20, 18).to_uint64();
        // Sign extension for signed type
        if (tiny & (1ULL << (3 - 1))) {
            tiny = (ipSigned3T)(tiny | ~((1ULL << 3) - 1));
        }
    }
    explicit ipFixedSignedSt(sc_bv<ipFixedSignedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipFixedSignedSt(
        ipUnsigned9T lane_,
        ipUnsigned5T magnitude_,
        ipSignedNibbleT offset_,
        ipSigned3T tiny_) :
        lane(lane_),
        magnitude(magnitude_),
        offset(offset_),
        tiny(tiny_)
    {}
    explicit ipFixedSignedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipFixedArraySt {
    ipWordT words[IP_FIXED_PAIR_COUNT]; //Fixed word array
    ipNibbleT nibbles[IP_FIXED_NIBBLE_COUNT]; //Fixed nibble array

    ipFixedArraySt() {}

    static constexpr uint16_t _bitWidth = 16*IP_FIXED_PAIR_COUNT + 4*IP_FIXED_NIBBLE_COUNT;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const ipFixedArraySt & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<IP_FIXED_NIBBLE_COUNT; i++) {
            ret = ret && (nibbles[i] == rhs.nibbles[i]);
        }
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            ret = ret && (words[i] == rhs.words[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedArraySt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<IP_FIXED_NIBBLE_COUNT; i++) {
            sc_trace(tf,v.nibbles[i], NAME + ".nibbles[i]");
        }
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            sc_trace(tf,v.words[i], NAME + ".words[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedArraySt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("nibbles[0:4]: {} words[0:1]: {}",
           staticArrayPrt<ipNibbleT, IP_FIXED_NIBBLE_COUNT>(nibbles, all),
           staticArrayPrt<ipWordT, IP_FIXED_PAIR_COUNT>(words, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedArraySt::_byteWidth);
        uint16_t _pos{0};
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            pack_bits((uint64_t *)&_ret, _pos, words[i], 16);
            _pos += 16;
        }
        for(unsigned int i=0; i<IP_FIXED_NIBBLE_COUNT; i++) {
            pack_bits((uint64_t *)&_ret, _pos, nibbles[i], 4);
            _pos += 4;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            uint16_t _bits = 16;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            words[i] = (ipWordT)((_src >> (_pos & 63)) & ((1ULL << 16) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                words[i] = (ipWordT)(words[i] | ((_src << _consume) & ((1ULL << 16) - 1)));
                _pos += _bits;
            }
        }
        for(unsigned int i=0; i<IP_FIXED_NIBBLE_COUNT; i++) {
            uint16_t _bits = 4;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(64-(_pos & 63)));
            nibbles[i] = (ipNibbleT)((_src >> (_pos & 63)) & ((1ULL << 4) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 64)) {
                nibbles[i] = (ipNibbleT)(nibbles[i] | ((_src << _consume) & ((1ULL << 4) - 1)));
                _pos += _bits;
            }
        }
    }
    inline sc_bv<ipFixedArraySt::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipFixedArraySt::_bitWidth> packed_data;
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            packed_data.range(0+(i+1)*16-1, 0+i*16) = words[i];
        }
        for(unsigned int i=0; i<IP_FIXED_NIBBLE_COUNT; i++) {
            packed_data.range(32+(i+1)*4-1, 32+i*4) = nibbles[i];
        }
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipFixedArraySt::_bitWidth> packed_data)
    {
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            words[i] = (ipWordT) packed_data.range(0+(i+1)*16-1, 0+i*16).to_uint64();
        }
        for(unsigned int i=0; i<IP_FIXED_NIBBLE_COUNT; i++) {
            nibbles[i] = (ipNibbleT) packed_data.range(32+(i+1)*4-1, 32+i*4).to_uint64();
        }
    }
    explicit ipFixedArraySt(sc_bv<ipFixedArraySt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipFixedArraySt(
        ipWordT words_[IP_FIXED_PAIR_COUNT],
        ipNibbleT nibbles_[IP_FIXED_NIBBLE_COUNT])
    {
        memcpy(&words, &words_, sizeof(words));
        memcpy(&nibbles, &nibbles_, sizeof(nibbles));
    }
    explicit ipFixedArraySt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipFixedLog2St {
    ipFixedIndexT index; //Fixed widthLog2minus1 index
    ipFixedCountT count; //Fixed widthLog2 count

    ipFixedLog2St() {}

    static constexpr uint16_t _bitWidth = clog2(IP_FIXED_DEPTH) + clog2(IP_FIXED_DEPTH+1);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const ipFixedLog2St & rhs) const {
        bool ret = true;
        ret = ret && (count == rhs.count);
        ret = ret && (index == rhs.index);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedLog2St & v, const std::string & NAME ) {
        sc_trace(tf,v.count, NAME + ".count");
        sc_trace(tf,v.index, NAME + ".index");
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedLog2St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("count:0x{:01x} index:0x{:01x}",
           (uint64_t) count,
           (uint64_t) index
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedLog2St::_byteWidth);
        _ret = index;
        _ret |= (uint8_t)count << (4 & 7);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        index = (ipFixedIndexT)((_src >> (_pos & 7)) & ((1ULL << 4) - 1));
        _pos += 4;
        count = (ipFixedCountT)((_src >> (_pos & 7)) & ((1ULL << 4) - 1));
    }
    inline sc_bv<ipFixedLog2St::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipFixedLog2St::_bitWidth> packed_data;
        packed_data.range(3, 0) = index;
        packed_data.range(7, 4) = count;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipFixedLog2St::_bitWidth> packed_data)
    {
        index = (ipFixedIndexT) packed_data.range(3, 0).to_uint64();
        count = (ipFixedCountT) packed_data.range(7, 4).to_uint64();
    }
    explicit ipFixedLog2St(sc_bv<ipFixedLog2St::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipFixedLog2St(
        ipFixedIndexT index_,
        ipFixedCountT count_) :
        index(index_),
        count(count_)
    {}
    explicit ipFixedLog2St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipFixedNestedSt {
    ipWide37T wideValue; //Wide fixed value
    ipFixedLog2St log2Fields; //Nested fixed log2 fields
    ipFixedArraySt arrays[IP_FIXED_PAIR_COUNT]; //Nested fixed arrays
    ipFixedSignedSt signedFields; //Nested signed and narrow fields
    ipFixedHeaderSt header; //Nested fixed header

    ipFixedNestedSt() {}

    static constexpr uint16_t _bitWidth = 37 + ipFixedLog2St::_bitWidth + ipFixedArraySt::_bitWidth*IP_FIXED_PAIR_COUNT
                                          + ipFixedSignedSt::_bitWidth + ipFixedHeaderSt::_bitWidth;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[3];
    inline bool operator == (const ipFixedNestedSt & rhs) const {
        bool ret = true;
        ret = ret && (header == rhs.header);
        ret = ret && (signedFields == rhs.signedFields);
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            ret = ret && (arrays[i] == rhs.arrays[i]);
        }
        ret = ret && (log2Fields == rhs.log2Fields);
        ret = ret && (wideValue == rhs.wideValue);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedNestedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.header, NAME + ".header");
        sc_trace(tf,v.signedFields, NAME + ".signedFields");
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            sc_trace(tf,v.arrays[i], NAME + ".arrays[i]");
        }
        sc_trace(tf,v.log2Fields, NAME + ".log2Fields");
        sc_trace(tf,v.wideValue, NAME + ".wideValue");
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedNestedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("header:<{}> signedFields:<{}>{} log2Fields:<{}> wideValue:0x{:010x}",
           header.prt(all),
           signedFields.prt(all),
           structArrayPrt<ipFixedArraySt, IP_FIXED_PAIR_COUNT>(arrays, "arrays", all),
           log2Fields.prt(all),
           (uint64_t) wideValue
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipFixedNestedSt::_byteWidth);
        _ret[ 0 ] = wideValue;
        {
            ipFixedLog2St::_packedSt _tmp{0};
            log2Fields.pack(_tmp);
            pack_bits((uint64_t *)&_ret, 37, _tmp, ipFixedLog2St::_bitWidth);
        }
        uint16_t _pos{45};
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            ipFixedArraySt::_packedSt _tmp{0};
            arrays[i].pack(_tmp);
            pack_bits((uint64_t *)&_ret, _pos, _tmp, ipFixedArraySt::_bitWidth);
            _pos += ipFixedArraySt::_bitWidth;
        }
        {
            ipFixedSignedSt::_packedSt _tmp{0};
            signedFields.pack(_tmp);
            pack_bits((uint64_t *)&_ret, 149, _tmp, ipFixedSignedSt::_bitWidth);
        }
        {
            ipFixedHeaderSt::_packedSt _tmp{0};
            header.pack(_tmp);
            pack_bits((uint64_t *)&_ret, 170, _tmp, ipFixedHeaderSt::_bitWidth);
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        wideValue = (ipWide37T)((_src[ _pos >> 6 ] >> (_pos & 63)) & ((1ULL << 37) - 1));
        _pos += 37;
        {
            uint64_t _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipFixedLog2St::_bitWidth);
            log2Fields.unpack(*((ipFixedLog2St::_packedSt*)&_tmp));
        }
        _pos += ipFixedLog2St::_bitWidth;
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            uint16_t _bits = ipFixedArraySt::_bitWidth;
            uint16_t _consume;
            {
                ipFixedArraySt::_packedSt _tmp{0};
                unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipFixedArraySt::_bitWidth);
                arrays[i].unpack(_tmp);
            }
            _pos += ipFixedArraySt::_bitWidth;
        }
        {
            uint64_t _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipFixedSignedSt::_bitWidth);
            signedFields.unpack(*((ipFixedSignedSt::_packedSt*)&_tmp));
        }
        _pos += ipFixedSignedSt::_bitWidth;
        {
            uint64_t _tmp{0};
            unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, ipFixedHeaderSt::_bitWidth);
            header.unpack(*((ipFixedHeaderSt::_packedSt*)&_tmp));
        }
    }
    inline sc_bv<ipFixedNestedSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipFixedNestedSt::_bitWidth> packed_data;
        packed_data.range(36, 0) = wideValue;
        packed_data.range(44, 37) = log2Fields.sc_pack();
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            packed_data.range(45+(i+1)*ipFixedArraySt::_bitWidth-1, 45+i*ipFixedArraySt::_bitWidth) = arrays[i].sc_pack();
        }
        packed_data.range(169, 149) = signedFields.sc_pack();
        packed_data.range(184, 170) = header.sc_pack();
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipFixedNestedSt::_bitWidth> packed_data)
    {
        wideValue = (ipWide37T) packed_data.range(36, 0).to_uint64();
        log2Fields.sc_unpack(packed_data.range(44, 37));
        for(unsigned int i=0; i<IP_FIXED_PAIR_COUNT; i++) {
            arrays[i].sc_unpack(packed_data.range(45+(i+1)*ipFixedArraySt::_bitWidth-1, 45+i*ipFixedArraySt::_bitWidth));
        }
        signedFields.sc_unpack(packed_data.range(169, 149));
        header.sc_unpack(packed_data.range(184, 170));
    }
    explicit ipFixedNestedSt(sc_bv<ipFixedNestedSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipFixedNestedSt(
        ipWide37T wideValue_,
        ipFixedLog2St log2Fields_,
        ipFixedArraySt arrays_[IP_FIXED_PAIR_COUNT],
        ipFixedSignedSt signedFields_,
        ipFixedHeaderSt header_) :
        wideValue(wideValue_),
        log2Fields(log2Fields_),
        signedFields(signedFields_),
        header(header_)
    {
        memcpy(&arrays, &arrays_, sizeof(arrays));
    }
    explicit ipFixedNestedSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace ip_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ip_ns {
template<typename Config>
class test_ip_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace ip_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ip_ns {
template<typename Config>
std::string test_ip_structs<Config>::name(void) { return "test_ip_structs"; }
template<typename Config>
void test_ip_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        typename ipDataSt<Config>::_packedSt packed;
        memset(&packed, pattern, ipDataSt<Config>::_byteWidth);
        sc_bv<ipDataSt<Config>::_bitWidth> aInit;
        sc_bv<ipDataSt<Config>::_bitWidth> aTest;
        for (int i = 0; i < ipDataSt<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipDataSt<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipDataSt<Config> a;
        a.sc_unpack(aInit);
        ipDataSt<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipDataSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipDataSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipDataSt<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipDataSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        typename ipCfgSt<Config>::_packedSt packed;
        memset(&packed, pattern, ipCfgSt<Config>::_byteWidth);
        sc_bv<ipCfgSt<Config>::_bitWidth> aInit;
        sc_bv<ipCfgSt<Config>::_bitWidth> aTest;
        for (int i = 0; i < ipCfgSt<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipCfgSt<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipCfgSt<Config> a;
        a.sc_unpack(aInit);
        ipCfgSt<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipCfgSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipCfgSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipCfgSt<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipCfgSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        typename ipMemSt<Config>::_packedSt packed;
        memset(&packed, pattern, ipMemSt<Config>::_byteWidth);
        sc_bv<ipMemSt<Config>::_bitWidth> aInit;
        sc_bv<ipMemSt<Config>::_bitWidth> aTest;
        for (int i = 0; i < ipMemSt<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipMemSt<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipMemSt<Config> a;
        a.sc_unpack(aInit);
        ipMemSt<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipMemSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipMemSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipMemSt<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipMemSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        typename ipMemAddrSt<Config>::_packedSt packed;
        memset(&packed, pattern, ipMemAddrSt<Config>::_byteWidth);
        sc_bv<ipMemAddrSt<Config>::_bitWidth> aInit;
        sc_bv<ipMemAddrSt<Config>::_bitWidth> aTest;
        for (int i = 0; i < ipMemAddrSt<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipMemAddrSt<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipMemAddrSt<Config> a;
        a.sc_unpack(aInit);
        ipMemAddrSt<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipMemAddrSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipMemAddrSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipMemAddrSt<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipMemAddrSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        typename ipBurstSt<Config>::_packedSt packed;
        memset(&packed, pattern, ipBurstSt<Config>::_byteWidth);
        sc_bv<ipBurstSt<Config>::_bitWidth> aInit;
        sc_bv<ipBurstSt<Config>::_bitWidth> aTest;
        for (int i = 0; i < ipBurstSt<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipBurstSt<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipBurstSt<Config> a;
        a.sc_unpack(aInit);
        ipBurstSt<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipBurstSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipBurstSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipBurstSt<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipBurstSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        ipFixedSt::_packedSt packed;
        memset(&packed, pattern, ipFixedSt::_byteWidth);
        sc_bv<ipFixedSt::_bitWidth> aInit;
        sc_bv<ipFixedSt::_bitWidth> aTest;
        for (int i = 0; i < ipFixedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipFixedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipFixedSt a;
        a.sc_unpack(aInit);
        ipFixedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipFixedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipFixedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipFixedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipFixedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        ipFixedAddrSt::_packedSt packed;
        memset(&packed, pattern, ipFixedAddrSt::_byteWidth);
        sc_bv<ipFixedAddrSt::_bitWidth> aInit;
        sc_bv<ipFixedAddrSt::_bitWidth> aTest;
        for (int i = 0; i < ipFixedAddrSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipFixedAddrSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipFixedAddrSt a;
        a.sc_unpack(aInit);
        ipFixedAddrSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipFixedAddrSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipFixedAddrSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipFixedAddrSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipFixedAddrSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        ipFixedHeaderSt::_packedSt packed;
        memset(&packed, pattern, ipFixedHeaderSt::_byteWidth);
        sc_bv<ipFixedHeaderSt::_bitWidth> aInit;
        sc_bv<ipFixedHeaderSt::_bitWidth> aTest;
        for (int i = 0; i < ipFixedHeaderSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipFixedHeaderSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipFixedHeaderSt a;
        a.sc_unpack(aInit);
        ipFixedHeaderSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipFixedHeaderSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipFixedHeaderSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipFixedHeaderSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipFixedHeaderSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        ipFixedSignedSt::_packedSt packed;
        memset(&packed, pattern, ipFixedSignedSt::_byteWidth);
        sc_bv<ipFixedSignedSt::_bitWidth> aInit;
        sc_bv<ipFixedSignedSt::_bitWidth> aTest;
        for (int i = 0; i < ipFixedSignedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipFixedSignedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipFixedSignedSt a;
        a.sc_unpack(aInit);
        ipFixedSignedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipFixedSignedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipFixedSignedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipFixedSignedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipFixedSignedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        ipFixedArraySt::_packedSt packed;
        memset(&packed, pattern, ipFixedArraySt::_byteWidth);
        sc_bv<ipFixedArraySt::_bitWidth> aInit;
        sc_bv<ipFixedArraySt::_bitWidth> aTest;
        for (int i = 0; i < ipFixedArraySt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipFixedArraySt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipFixedArraySt a;
        a.sc_unpack(aInit);
        ipFixedArraySt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipFixedArraySt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipFixedArraySt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipFixedArraySt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipFixedArraySt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        ipFixedLog2St::_packedSt packed;
        memset(&packed, pattern, ipFixedLog2St::_byteWidth);
        sc_bv<ipFixedLog2St::_bitWidth> aInit;
        sc_bv<ipFixedLog2St::_bitWidth> aTest;
        for (int i = 0; i < ipFixedLog2St::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipFixedLog2St::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipFixedLog2St a;
        a.sc_unpack(aInit);
        ipFixedLog2St b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipFixedLog2St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipFixedLog2St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipFixedLog2St::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipFixedLog2St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : signedPatterns) {
        ipFixedNestedSt::_packedSt packed;
        memset(&packed, pattern, ipFixedNestedSt::_byteWidth);
        sc_bv<ipFixedNestedSt::_bitWidth> aInit;
        sc_bv<ipFixedNestedSt::_bitWidth> aTest;
        for (int i = 0; i < ipFixedNestedSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipFixedNestedSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipFixedNestedSt a;
        a.sc_unpack(aInit);
        ipFixedNestedSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipFixedNestedSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipFixedNestedSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipFixedNestedSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipFixedNestedSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace ip_ns

// GENERATED_CODE_END
