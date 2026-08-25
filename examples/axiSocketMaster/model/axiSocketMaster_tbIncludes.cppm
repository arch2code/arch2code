
// GENERATED_CODE_PARAM --project=axiSocketMaster --context=axiSocketMaster_tb.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module axiSocketMaster_tb;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import axiSocketMaster_axiStd;
using namespace axiSocketMaster_axiStd_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace axiSocketMaster_tb_ns {
//constants
inline constexpr uint32_t AXI_ADDRESS_WIDTH = 32;  // The width of the AXI address busses
inline constexpr uint32_t AXI_DATA_WIDTH = 32;  // The width of the AXI data busses
inline constexpr uint32_t AXI_STROBE_WIDTH = 4;  // The width of the AXI strobe signals

} // namespace axiSocketMaster_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace axiSocketMaster_tb_ns {
// types
typedef uint32_t axiAddrT; // [32] Address Width
typedef uint32_t axiDataT; // [32] Width of the data bus.
typedef uint8_t axiStrobeT; // [4] Width of the strobe bus.

} // namespace axiSocketMaster_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace axiSocketMaster_tb_ns {
// enums

} // namespace axiSocketMaster_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace axiSocketMaster_tb_ns {
// structures
struct axiAddrSt {
    axiAddrT addr; //

    axiAddrSt() {}

    static constexpr uint16_t _bitWidth = AXI_ADDRESS_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const axiAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (addr == rhs.addr);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const axiAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.addr, NAME + ".addr");
    }
    inline friend ostream& operator << ( ostream& os,  axiAddrSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("addr:0x{:08x}",
           (uint64_t) addr
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, axiAddrSt::_byteWidth);
        _ret = addr;
    }
    inline void unpack(const _packedSt &_src)
    {
        addr = (axiAddrT)((_src));
    }
    inline sc_bv<axiAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<axiAddrSt::_bitWidth> packed_data;
        packed_data.range(31, 0) = addr;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<axiAddrSt::_bitWidth> packed_data)
    {
        addr = (axiAddrT) packed_data.range(31, 0).to_uint64();
    }
    explicit axiAddrSt(sc_bv<axiAddrSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit axiAddrSt(
        axiAddrT addr_) :
        addr(addr_)
    {}
    explicit axiAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct axiDataSt {
    axiDataT data; //

    axiDataSt() {}

    static constexpr uint16_t _bitWidth = AXI_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const axiDataSt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const axiDataSt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  axiDataSt const & v ) {
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
        memset(&_ret, 0, axiDataSt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (axiDataT)((_src));
    }
    inline sc_bv<axiDataSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<axiDataSt::_bitWidth> packed_data;
        packed_data.range(31, 0) = data;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<axiDataSt::_bitWidth> packed_data)
    {
        data = (axiDataT) packed_data.range(31, 0).to_uint64();
    }
    explicit axiDataSt(sc_bv<axiDataSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit axiDataSt(
        axiDataT data_) :
        data(data_)
    {}
    explicit axiDataSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct axiStrobeSt {
    axiStrobeT strobe; //

    axiStrobeSt() {}

    static constexpr uint16_t _bitWidth = AXI_STROBE_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const axiStrobeSt & rhs) const {
        bool ret = true;
        ret = ret && (strobe == rhs.strobe);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const axiStrobeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.strobe, NAME + ".strobe");
    }
    inline friend ostream& operator << ( ostream& os,  axiStrobeSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("strobe:0x{:01x}",
           (uint64_t) strobe
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, axiStrobeSt::_byteWidth);
        _ret = strobe;
    }
    inline void unpack(const _packedSt &_src)
    {
        strobe = (axiStrobeT)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<axiStrobeSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<axiStrobeSt::_bitWidth> packed_data;
        packed_data.range(3, 0) = strobe;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<axiStrobeSt::_bitWidth> packed_data)
    {
        strobe = (axiStrobeT) packed_data.range(3, 0).to_uint64();
    }
    explicit axiStrobeSt(sc_bv<axiStrobeSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit axiStrobeSt(
        axiStrobeT strobe_) :
        strobe(strobe_)
    {}
    explicit axiStrobeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace axiSocketMaster_tb_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace axiSocketMaster_tb_test_ns {
class test_axiSocketMaster_tb_structs {
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
} // namespace axiSocketMaster_tb_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace axiSocketMaster_tb_test_ns {
using namespace axiSocketMaster_tb_ns;
std::string test_axiSocketMaster_tb_structs::name(void) { return "test_axiSocketMaster_tb_structs"; }
void test_axiSocketMaster_tb_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<axiAddrSt>("axiAddrSt", patterns);
    roundTrip<axiDataSt>("axiDataSt", patterns);
    roundTrip<axiStrobeSt>("axiStrobeSt", patterns);
}
} // namespace axiSocketMaster_tb_test_ns

// GENERATED_CODE_END
