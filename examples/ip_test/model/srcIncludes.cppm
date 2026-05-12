
// GENERATED_CODE_PARAM --context=src.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module src;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace src_ns {
//constants

} // namespace src_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace src_ns {
// types
template<typename Config> using srcOut0DataT = uint64_t; // [max:16] src out0 data word, parameterizable
template<typename Config> using srcOut1DataT = uint64_t; // [max:16] src out1 data word, parameterizable

} // namespace src_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace src_ns {
// enums

} // namespace src_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace src_ns {
// structures
template<typename Config>
struct srcOut0St {
    srcOut0DataT<Config> data; //src out0 payload

    srcOut0St() {}

    static constexpr uint16_t _bitWidth = Config::OUT0_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const srcOut0St<Config> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const srcOut0St<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  srcOut0St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:02x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, srcOut0St<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::OUT0_DATA_WIDTH);
        _pos += Config::OUT0_DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (srcOut0DataT<Config>)((_src) & ((1ULL << Config::OUT0_DATA_WIDTH) - 1));
    }
    inline sc_bv<srcOut0St<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<srcOut0St<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::OUT0_DATA_WIDTH-1, _pos) = data;
        _pos += Config::OUT0_DATA_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<srcOut0St<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (srcOut0DataT<Config>) packed_data.range(_pos+Config::OUT0_DATA_WIDTH-1, _pos).to_uint64();
        _pos += Config::OUT0_DATA_WIDTH;
    }
    explicit srcOut0St(sc_bv<srcOut0St<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit srcOut0St(
        srcOut0DataT<Config> data_) :
        data(data_)
    {}
    explicit srcOut0St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
template<typename Config>
struct srcOut1St {
    srcOut1DataT<Config> data; //src out1 payload

    srcOut1St() {}

    static constexpr uint16_t _bitWidth = Config::OUT1_DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const srcOut1St<Config> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const srcOut1St<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  srcOut1St const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:03x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, srcOut1St<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::OUT1_DATA_WIDTH);
        _pos += Config::OUT1_DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (srcOut1DataT<Config>)((_src) & ((1ULL << Config::OUT1_DATA_WIDTH) - 1));
    }
    inline sc_bv<srcOut1St<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<srcOut1St<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::OUT1_DATA_WIDTH-1, _pos) = data;
        _pos += Config::OUT1_DATA_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<srcOut1St<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (srcOut1DataT<Config>) packed_data.range(_pos+Config::OUT1_DATA_WIDTH-1, _pos).to_uint64();
        _pos += Config::OUT1_DATA_WIDTH;
    }
    explicit srcOut1St(sc_bv<srcOut1St<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit srcOut1St(
        srcOut1DataT<Config> data_) :
        data(data_)
    {}
    explicit srcOut1St(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace src_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace src_ns {
template<typename Config>
class test_src_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace src_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace src_ns {
template<typename Config>
std::string test_src_structs<Config>::name(void) { return "test_src_structs"; }
template<typename Config>
void test_src_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        typename srcOut0St<Config>::_packedSt packed;
        memset(&packed, pattern, srcOut0St<Config>::_byteWidth);
        sc_bv<srcOut0St<Config>::_bitWidth> aInit;
        sc_bv<srcOut0St<Config>::_bitWidth> aTest;
        for (int i = 0; i < srcOut0St<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, srcOut0St<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        srcOut0St<Config> a;
        a.sc_unpack(aInit);
        srcOut0St<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"srcOut0St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"srcOut0St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = srcOut0St<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"srcOut0St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        typename srcOut1St<Config>::_packedSt packed;
        memset(&packed, pattern, srcOut1St<Config>::_byteWidth);
        sc_bv<srcOut1St<Config>::_bitWidth> aInit;
        sc_bv<srcOut1St<Config>::_bitWidth> aTest;
        for (int i = 0; i < srcOut1St<Config>::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, srcOut1St<Config>::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        srcOut1St<Config> a;
        a.sc_unpack(aInit);
        srcOut1St<Config> b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"srcOut1St fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"srcOut1St fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = srcOut1St<Config>::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"srcOut1St fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace src_ns

// GENERATED_CODE_END
