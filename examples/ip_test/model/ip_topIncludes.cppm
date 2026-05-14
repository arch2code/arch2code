
// GENERATED_CODE_PARAM --context=ip_top.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module ip_top;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import ip;
import ipLeaf;
import src;
import ipBridge;
using namespace ip_ns;
using namespace ipLeaf_ns;
using namespace src_ns;
using namespace ipBridge_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_top_ns {
//constants
const uint32_t DWORD = 32;  // Width of an APB dword

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_top_ns {
// types
typedef uint32_t apbAddrT; // [32] APB address
typedef uint32_t apbDataT; // [32] APB data

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_top_ns {
// enums
enum  addr_id_top {          //Generated type for addressing top instances
    ADDR_ID_TOP_UIP0=0,      // uIp0 instance address
    ADDR_ID_TOP_UIP1=1,      // uIp1 instance address
    ADDR_ID_TOP_UBRIDGE=2 }; // uBridge instance address
inline const char* addr_id_top_prt( addr_id_top val )
{
    switch( val )
    {
        case ADDR_ID_TOP_UIP0: return( "ADDR_ID_TOP_UIP0" );
        case ADDR_ID_TOP_UIP1: return( "ADDR_ID_TOP_UIP1" );
        case ADDR_ID_TOP_UBRIDGE: return( "ADDR_ID_TOP_UBRIDGE" );
    }
    return("!!!BADENUM!!!");
}

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ip_top_ns {
// structures
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
} // namespace ip_top_ns

// GENERATED_CODE_END
