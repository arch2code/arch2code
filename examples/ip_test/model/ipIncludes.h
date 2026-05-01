
#ifndef IPINCLUDES_H_
#define IPINCLUDES_H_
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --context=ip.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t IP_DATA_WIDTH = 8;  // Per-instance data width
const uint32_t IP_MEM_DEPTH = 16;  // Per-instance memory depth
const uint32_t IP_DATA_WIDTH_X2 = 16;  // Derived width, 2x data (maxValue auto-derived)

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint8_t ipDataT; // [8] IP data word, parameterizable
typedef uint8_t enableT; // [1] Single enable bit
typedef uint8_t ipMemAddrT; // [4] Index into ipMem (0 .. IP_MEM_DEPTH-1)
typedef uint8_t ipFixedT; // [8] Fixed 8-bit byte (non-parameterizable)
typedef uint8_t ipFixedAddrT; // [8] Fixed 8-bit address index (non-parameterizable)

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
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

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct ipDataSt {
    ipDataT data; //Data word

    ipDataSt() {}

    static constexpr uint16_t _bitWidth = IP_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    bool operator == (const ipDataSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const ipDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  ipDataSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<ipDataSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<ipDataSt::_bitWidth> packed_data);
    explicit ipDataSt(sc_bv<ipDataSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipDataSt(
        ipDataT data_) :
        data(data_)
    {}
    explicit ipDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipCfgSt {
    ipDataT threshold; //Threshold value
    ipModeT mode; //Operating mode
    enableT enable; //Enable bit

    ipCfgSt() {}

    static constexpr uint16_t _bitWidth = IP_DATA_WIDTH + 2 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    bool operator == (const ipCfgSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const ipCfgSt & v, const std::string & NAME ) {
        sc_trace(tf,v.enable, NAME + ".enable");
        sc_trace(tf,v.mode, NAME + ".mode");
        sc_trace(tf,v.threshold, NAME + ".threshold");
    }
    inline friend ostream& operator << ( ostream& os,  ipCfgSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<ipCfgSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<ipCfgSt::_bitWidth> packed_data);
    explicit ipCfgSt(sc_bv<ipCfgSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipCfgSt(
        ipDataT threshold_,
        ipModeT mode_,
        enableT enable_) :
        threshold(threshold_),
        mode(mode_),
        enable(enable_)
    {}
    explicit ipCfgSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipMemSt {
    ipDataT data; //Data word

    ipMemSt() {}

    static constexpr uint16_t _bitWidth = IP_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    bool operator == (const ipMemSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const ipMemSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  ipMemSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<ipMemSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<ipMemSt::_bitWidth> packed_data);
    explicit ipMemSt(sc_bv<ipMemSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipMemSt(
        ipDataT data_) :
        data(data_)
    {}
    explicit ipMemSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipMemAddrSt {
    ipMemAddrT address; //Memory address

    ipMemAddrSt() {}

    static constexpr uint16_t _bitWidth = clog2(IP_MEM_DEPTH);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    bool operator == (const ipMemAddrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const ipMemAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  ipMemAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<ipMemAddrSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<ipMemAddrSt::_bitWidth> packed_data);
    explicit ipMemAddrSt(sc_bv<ipMemAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipMemAddrSt(
        ipMemAddrT address_) :
        address(address_)
    {}
    explicit ipMemAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct ipBurstSt {
    ipDataT samples[IP_MEM_DEPTH]; //Burst of parameterizable samples

    ipBurstSt() {}

    static constexpr uint16_t _bitWidth = IP_DATA_WIDTH*IP_MEM_DEPTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    bool operator == (const ipBurstSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const ipBurstSt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<IP_MEM_DEPTH; i++) {
            sc_trace(tf,v.samples[i], NAME + ".samples[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  ipBurstSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<ipBurstSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<ipBurstSt::_bitWidth> packed_data);
    explicit ipBurstSt(sc_bv<ipBurstSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipBurstSt(
        ipDataT samples_[IP_MEM_DEPTH])
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
    bool operator == (const ipFixedSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedSt & v, const std::string & NAME ) {
        sc_trace(tf,v.b, NAME + ".b");
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<ipFixedSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<ipFixedSt::_bitWidth> packed_data);
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
    bool operator == (const ipFixedAddrSt & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const ipFixedAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.a, NAME + ".a");
    }
    inline friend ostream& operator << ( ostream& os,  ipFixedAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    sc_bv<ipFixedAddrSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<ipFixedAddrSt::_bitWidth> packed_data);
    explicit ipFixedAddrSt(sc_bv<ipFixedAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipFixedAddrSt(
        ipFixedAddrT a_) :
        a(a_)
    {}
    explicit ipFixedAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END
#endif //IPINCLUDES_H_
