
// GENERATED_CODE_PARAM --project=xif --context=xif.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module xif;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace xif_ns {
//constants

} // namespace xif_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace xif_ns {
// types
template<typename Config> using streamDataT = uint64_t; // [max:32] Parameterized stream payload word
typedef uint16_t streamBndryDataT; // [16] Non-parameterized boundary payload word (matches DATA_WIDTH=16)

} // namespace xif_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace xif_ns {
// enums

} // namespace xif_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace xif_ns {
// structures
template<typename Config>
struct streamSt {
    streamDataT<Config> data; //Parameterized stream payload

    streamSt() {}

    static constexpr uint16_t _bitWidth = Config::DATA_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const streamSt<Config> & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const streamSt<Config> & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  streamSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:04x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, streamSt<Config>::_byteWidth);
        uint16_t _pos{0};
        pack_bits((uint64_t *)&_ret, _pos, data, Config::DATA_WIDTH);
        _pos += Config::DATA_WIDTH;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (streamDataT<Config>)((_src) & ((1ULL << (Config::DATA_WIDTH)) - 1));
    }
    inline sc_bv<streamSt<Config>::_bitWidth> sc_pack(void) const
    {
        sc_bv<streamSt<Config>::_bitWidth> packed_data;
        uint16_t _pos{0};
        packed_data.range(_pos+Config::DATA_WIDTH-1, _pos) = data;
        _pos += Config::DATA_WIDTH;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<streamSt<Config>::_bitWidth> packed_data)
    {
    uint16_t _pos{0};
        data = (streamDataT<Config>) packed_data.range(_pos+Config::DATA_WIDTH-1, _pos).to_uint64();
        _pos += Config::DATA_WIDTH;
    }
    explicit streamSt(sc_bv<streamSt<Config>::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit streamSt(
        streamDataT<Config> data_) :
        data(data_)
    {}
    explicit streamSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct streamBndrySt {
    streamBndryDataT data; //Boundary payload; packed layout matches streamSt<dutV0>

    streamBndrySt() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const streamBndrySt & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const streamBndrySt & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  streamBndrySt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:04x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, streamBndrySt::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (streamBndryDataT)((_src));
    }
    inline sc_bv<streamBndrySt::_bitWidth> sc_pack(void) const
    {
        sc_bv<streamBndrySt::_bitWidth> packed_data;
        packed_data.range(15, 0) = data;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<streamBndrySt::_bitWidth> packed_data)
    {
        data = (streamBndryDataT) packed_data.range(15, 0).to_uint64();
    }
    explicit streamBndrySt(sc_bv<streamBndrySt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit streamBndrySt(
        streamBndryDataT data_) :
        data(data_)
    {}
    explicit streamBndrySt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace xif_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace xif_test_ns {
class test_xif_structs {
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
} // namespace xif_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace xif_test_ns {
using namespace xif_ns;
struct xifTestConfigDefault {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};
struct xifTestConfigMax {
    static constexpr uint32_t DATA_WIDTH = 32;
    static constexpr uint32_t FRAME_HEIGHT = 16;
    static constexpr uint32_t FRAME_WIDTH = 16;
};
std::string test_xif_structs::name(void) { return "test_xif_structs"; }
void test_xif_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<streamSt<xifTestConfigDefault>>("streamSt", patterns);
    roundTrip<streamSt<xifTestConfigMax>>("streamSt", patterns);
    roundTrip<streamBndrySt>("streamBndrySt", patterns);
}
} // namespace xif_test_ns

// GENERATED_CODE_END
