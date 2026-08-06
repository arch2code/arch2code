
// GENERATED_CODE_PARAM --project=ip_test --context=../../leaf/yaml/ipLeaf.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module ip_test_ipLeaf;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_test_ipLeaf_ns {
//constants

} // namespace ip_test_ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_test_ipLeaf_ns {
// types
template<typename Config> using ipLeafMemAddrT = uint64_t; // [max:3] Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)
template<typename Config> using ipLeafDataT = uint64_t; // [max:16] ipLeaf data word, parameterizable

} // namespace ip_test_ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_test_ipLeaf_ns {
// enums

} // namespace ip_test_ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ip_test_ipLeaf_ns {
// structures
template<typename Config>
struct ipLeafMemSt {
    ipLeafDataT<Config> data; //Leaf memory word

    ipLeafMemSt() {}

    static constexpr uint16_t _bitWidth = Config::LEAF_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const ipLeafMemSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipLeafMemSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  ipLeafMemSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:01x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, ipLeafMemSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::LEAF_DATA_WIDTH);
        _pos += Config::LEAF_DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (ipLeafDataT<Config>)((_src) & ((1ULL << (Config::LEAF_DATA_WIDTH)) - 1));
    }
    inline sc_bv<ipLeafMemSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipLeafMemSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::LEAF_DATA_WIDTH-1, _pos) = data;
        _pos += Config::LEAF_DATA_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipLeafMemSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (ipLeafDataT<Config>) packed_data.range(_pos+Config::LEAF_DATA_WIDTH-1, _pos).to_uint64();
        _pos += Config::LEAF_DATA_WIDTH;
    }
    explicit ipLeafMemSt(sc_bv<ipLeafMemSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipLeafMemSt(
        ipLeafDataT<Config> data_) :
        data(data_)
    {}
    explicit ipLeafMemSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct ipLeafMemAddrSt {
    ipLeafMemAddrT<Config> address; //Leaf memory address

    ipLeafMemAddrSt() {}

    static constexpr uint16_t _bitWidth = clog2(Config::LEAF_MEM_DEPTH);
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const ipLeafMemAddrSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const ipLeafMemAddrSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  ipLeafMemAddrSt const & v ) {
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
        memset(&_ret, 0, ipLeafMemAddrSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, address, clog2(Config::LEAF_MEM_DEPTH));
        _pos += clog2(Config::LEAF_MEM_DEPTH);
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (ipLeafMemAddrT<Config>)((_src) & ((1ULL << (clog2(Config::LEAF_MEM_DEPTH))) - 1));
    }
    inline sc_bv<ipLeafMemAddrSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<ipLeafMemAddrSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+clog2(Config::LEAF_MEM_DEPTH)-1, _pos) = address;
        _pos += clog2(Config::LEAF_MEM_DEPTH);
        return packed_data;
    }
    inline void sc_unpack(sc_bv<ipLeafMemAddrSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        address = (ipLeafMemAddrT<Config>) packed_data.range(_pos+clog2(Config::LEAF_MEM_DEPTH)-1, _pos).to_uint64();
        _pos += clog2(Config::LEAF_MEM_DEPTH);
    }
    explicit ipLeafMemAddrSt(sc_bv<ipLeafMemAddrSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit ipLeafMemAddrSt(
        ipLeafMemAddrT<Config> address_) :
        address(address_)
    {}
    explicit ipLeafMemAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace ip_test_ipLeaf_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ip_test_ipLeaf_test_ns {
class test_ipLeaf_structs {
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
} // namespace ip_test_ipLeaf_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ip_test_ipLeaf_test_ns {
using namespace ip_test_ipLeaf_ns;
struct ipLeafTestConfigDefault {
    static constexpr uint32_t LEAF_DATA_WIDTH = 4;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};
struct ipLeafTestConfigMid {
    static constexpr uint32_t LEAF_DATA_WIDTH = 8;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};
struct ipLeafTestConfigMax {
    static constexpr uint32_t LEAF_DATA_WIDTH = 16;
    static constexpr uint32_t LEAF_MEM_DEPTH = 8;
};
std::string test_ipLeaf_structs::name(void) { return "test_ipLeaf_structs"; }
void test_ipLeaf_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<ipLeafMemSt<ipLeafTestConfigDefault>>("ipLeafMemSt", patterns);
    roundTrip<ipLeafMemSt<ipLeafTestConfigMid>>("ipLeafMemSt", patterns);
    roundTrip<ipLeafMemSt<ipLeafTestConfigMax>>("ipLeafMemSt", patterns);
    roundTrip<ipLeafMemAddrSt<ipLeafTestConfigDefault>>("ipLeafMemAddrSt", patterns);
    roundTrip<ipLeafMemAddrSt<ipLeafTestConfigMid>>("ipLeafMemAddrSt", patterns);
    roundTrip<ipLeafMemAddrSt<ipLeafTestConfigMax>>("ipLeafMemAddrSt", patterns);
}
} // namespace ip_test_ipLeaf_test_ns

// GENERATED_CODE_END
