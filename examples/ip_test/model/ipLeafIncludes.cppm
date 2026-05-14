
// GENERATED_CODE_PARAM --context=ipLeaf.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module ipLeaf;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ipLeaf_ns {
//constants

} // namespace ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ipLeaf_ns {
// types
template<typename Config> using ipLeafDataT = uint64_t; // [max:8] ipLeaf data word, parameterizable
template<typename Config> using ipLeafMemAddrT = uint64_t; // [max:3] Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)

} // namespace ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ipLeaf_ns {
// enums

} // namespace ipLeaf_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace ipLeaf_ns {
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
        data = (ipLeafDataT<Config>)((_src) & ((1ULL << Config::LEAF_DATA_WIDTH) - 1));
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
        address = (ipLeafMemAddrT<Config>)((_src) & ((1ULL << clog2(Config::LEAF_MEM_DEPTH)) - 1));
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
} // namespace ipLeaf_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace ipLeaf_ns {
template<typename Config>
class test_ipLeaf_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace ipLeaf_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace ipLeaf_ns {
template<typename Config>
std::string test_ipLeaf_structs<Config>::name(void) { return "test_ipLeaf_structs"; }
template<typename Config>
void test_ipLeaf_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        typename ipLeafMemSt<Config>::_packedSt packed;
        memset(&packed, pattern, ipLeafMemSt<Config>::_byteWidth);
        sc_bv<ipLeafMemSt<Config>::_bitWidth> aInit;
        sc_bv<ipLeafMemSt<Config>::_bitWidth> aTest;
        for (int i = 0; i < ipLeafMemSt<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipLeafMemSt<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipLeafMemSt<Config> a;
        a.sc_unpack(aInit);
        ipLeafMemSt<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipLeafMemSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipLeafMemSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipLeafMemSt<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipLeafMemSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        typename ipLeafMemAddrSt<Config>::_packedSt packed;
        memset(&packed, pattern, ipLeafMemAddrSt<Config>::_byteWidth);
        sc_bv<ipLeafMemAddrSt<Config>::_bitWidth> aInit;
        sc_bv<ipLeafMemAddrSt<Config>::_bitWidth> aTest;
        for (int i = 0; i < ipLeafMemAddrSt<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, ipLeafMemAddrSt<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        ipLeafMemAddrSt<Config> a;
        a.sc_unpack(aInit);
        ipLeafMemAddrSt<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"ipLeafMemAddrSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"ipLeafMemAddrSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = ipLeafMemAddrSt<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"ipLeafMemAddrSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace ipLeaf_ns

// GENERATED_CODE_END
