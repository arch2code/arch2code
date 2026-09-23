
// GENERATED_CODE_PARAM --project=twoClk --context=../../yaml/twoClk.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

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
inline constexpr uint32_t TWO_CLK_REG_ADDR_WIDTH = 32;  // twoClkReg address bus width
inline constexpr uint32_t TWO_CLK_REG_DATA_WIDTH = 32;  // twoClkReg data bus width
inline constexpr uint32_t TWO_CLK_RESET_SETTLE_NS = 100;  // cpu start delay so both rst_n and rstSlow_n have released before the first bridged access

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
        memset(&_ret, 0, twoClkRegAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (twoClkRegAddrT)((_src));
    }
    inline sc_bv<twoClkRegAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkRegAddrSt::_bitWidth> packed_data;
        packed_data.range(31, 0) = address;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<twoClkRegAddrSt::_bitWidth> packed_data)
    {
        address = (twoClkRegAddrT) packed_data.range(31, 0).to_uint64();
    }
    explicit twoClkRegAddrSt(sc_bv<twoClkRegAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, twoClkRegDataSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (twoClkRegDataT)((_src));
    }
    inline sc_bv<twoClkRegDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkRegDataSt::_bitWidth> packed_data;
        packed_data.range(31, 0) = data;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<twoClkRegDataSt::_bitWidth> packed_data)
    {
        data = (twoClkRegDataT) packed_data.range(31, 0).to_uint64();
    }
    explicit twoClkRegDataSt(sc_bv<twoClkRegDataSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, twoClkTblAddrSt::_byteWidth);
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (twoClkTblAddrBitsT)((_src) & ((1ULL << 3) - 1));
    }
    inline sc_bv<twoClkTblAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<twoClkTblAddrSt::_bitWidth> packed_data;
        packed_data.range(2, 0) = address;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<twoClkTblAddrSt::_bitWidth> packed_data)
    {
        address = (twoClkTblAddrBitsT) packed_data.range(2, 0).to_uint64();
    }
    explicit twoClkTblAddrSt(sc_bv<twoClkTblAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
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
        memset(&_ret, 0, twoClkTblSt::_byteWidth);
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
        packed_data.range(31, 0) = lo;
        packed_data.range(47, 32) = hi;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<twoClkTblSt::_bitWidth> packed_data)
    {
        lo = (twoClkTblLoT) packed_data.range(31, 0).to_uint64();
        hi = (twoClkTblHiT) packed_data.range(47, 32).to_uint64();
    }
    explicit twoClkTblSt(sc_bv<twoClkTblSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit twoClkTblSt(
        twoClkTblLoT lo_,
        twoClkTblHiT hi_) :
        lo(lo_),
        hi(hi_)
    {}
    explicit twoClkTblSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace twoClk_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace twoClk_test_ns {
class test_twoClk_structs {
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
}
} // namespace twoClk_test_ns

// GENERATED_CODE_END
