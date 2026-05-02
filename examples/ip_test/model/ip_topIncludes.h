
#ifndef IP_TOPINCLUDES_H_
#define IP_TOPINCLUDES_H_
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --context=ip_top.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr
#include "ipIncludes.h"
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants
const uint32_t DWORD = 32;  // Width of an APB dword

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint32_t apbAddrT; // [32] APB address
typedef uint32_t apbDataT; // [32] APB data

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums
enum  addr_id_top {          //Generated type for addressing top instances
    ADDR_ID_TOP_UIP0=0,      // uIp0 instance address
    ADDR_ID_TOP_UIP1=1 };    // uIp1 instance address
inline const char* addr_id_top_prt( addr_id_top val )
{
    switch( val )
    {
        case ADDR_ID_TOP_UIP0: return( "ADDR_ID_TOP_UIP0" );
        case ADDR_ID_TOP_UIP1: return( "ADDR_ID_TOP_UIP1" );
    }
    return("!!!BADENUM!!!");
}

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct apbAddrSt {
    apbAddrT address; //

    apbAddrSt() {}

    static constexpr uint16_t _bitWidth = DWORD;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
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
    sc_bv<apbAddrSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<apbAddrSt::_bitWidth> packed_data);
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
    sc_bv<apbDataSt::_bitWidth> sc_pack(void) const;
    void sc_unpack(sc_bv<apbDataSt::_bitWidth> packed_data);
    explicit apbDataSt(sc_bv<apbDataSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit apbDataSt(
        apbDataT data_) :
        data(data_)
    {}
    explicit apbDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END
#endif //IP_TOPINCLUDES_H_
