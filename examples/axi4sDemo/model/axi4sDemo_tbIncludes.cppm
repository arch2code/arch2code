
// GENERATED_CODE_PARAM --context=axi4sDemo_tb.yaml --mode=module
// 

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module axi4sDemo_tb;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace axi4sDemo_tb_ns {
//constants

} // namespace axi4sDemo_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace axi4sDemo_tb_ns {
// types
typedef uint8_t bv4_t; // [4] Bit Vector 4 bits
typedef uint8_t bv8_t; // [8] Bit Vector 8 bits
typedef uint16_t bv16_t; // [16] Bit Vector 16 bits
typedef uint64_t bv64_t; // [64] Bit Vector 64 bits
struct bv256_t { uint64_t word[ 4 ]; }; // [256] Bit Vector 256 bits

} // namespace axi4sDemo_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace axi4sDemo_tb_ns {
// enums

} // namespace axi4sDemo_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace axi4sDemo_tb_ns {
// structures
struct data_t1_t {
    bv256_t data; //

    data_t1_t() {}

    static constexpr uint16_t _bitWidth = 256;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[4];
    inline bool operator == (const data_t1_t & rhs) const {
        bool ret = true;
        ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
        ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
        ret = ret && (data.word[ 2 ] == rhs.data.word[ 2 ]);
        ret = ret && (data.word[ 3 ] == rhs.data.word[ 3 ]);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const data_t1_t & v, const std::string & NAME ) {
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
        sc_trace(tf,v.data.word[ 2 ], NAME + ".data.word[ 2 ]");
        sc_trace(tf,v.data.word[ 3 ], NAME + ".data.word[ 3 ]");
    }
    inline friend ostream& operator << ( ostream& os,  data_t1_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:016x}{:016x}{:016x}{:016x}",
           data.word[3],
           data.word[2],
           data.word[1],
           data.word[0]
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, data_t1_t::_byteWidth);
        pack_bits((uint64_t *)&_ret, 0, (uint64_t *)&data, 256);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data.word[0] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        data.word[1] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        data.word[2] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
        _pos += 64;
        data.word[3] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
    }
    inline sc_bv<data_t1_t::_bitWidth> sc_pack(void) const
    {
        sc_bv<data_t1_t::_bitWidth> packed_data;
        packed_data.range(63, 0) = data.word[0];
        packed_data.range(127, 64) = data.word[1];
        packed_data.range(191, 128) = data.word[2];
        packed_data.range(255, 192) = data.word[3];
        return packed_data;
    }
    inline void sc_unpack(sc_bv<data_t1_t::_bitWidth> packed_data)
    {
        data.word[0] = (uint64_t) packed_data.range(63, 0).to_uint64();
        data.word[1] = (uint64_t) packed_data.range(127, 64).to_uint64();
        data.word[2] = (uint64_t) packed_data.range(191, 128).to_uint64();
        data.word[3] = (uint64_t) packed_data.range(255, 192).to_uint64();
    }
    explicit data_t1_t(sc_bv<data_t1_t::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit data_t1_t(
        bv256_t data_) :
        data(data_)
    {}
    explicit data_t1_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tid_t1_t {
    bv4_t tid; //

    tid_t1_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const tid_t1_t & rhs) const {
        bool ret = true;
        ret = ret && (tid == rhs.tid);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tid_t1_t & v, const std::string & NAME ) {
        sc_trace(tf,v.tid, NAME + ".tid");
    }
    inline friend ostream& operator << ( ostream& os,  tid_t1_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tid:0x{:01x}",
           (uint64_t) tid
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tid_t1_t::_byteWidth);
        _ret = tid;
    }
    inline void unpack(const _packedSt &_src)
    {
        tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<tid_t1_t::_bitWidth> sc_pack(void) const
    {
        sc_bv<tid_t1_t::_bitWidth> packed_data;
        packed_data.range(3, 0) = tid;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<tid_t1_t::_bitWidth> packed_data)
    {
        tid = (bv4_t) packed_data.range(3, 0).to_uint64();
    }
    explicit tid_t1_t(sc_bv<tid_t1_t::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit tid_t1_t(
        bv4_t tid_) :
        tid(tid_)
    {}
    explicit tid_t1_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tdest_t1_t {
    bv4_t tid; //

    tdest_t1_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const tdest_t1_t & rhs) const {
        bool ret = true;
        ret = ret && (tid == rhs.tid);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tdest_t1_t & v, const std::string & NAME ) {
        sc_trace(tf,v.tid, NAME + ".tid");
    }
    inline friend ostream& operator << ( ostream& os,  tdest_t1_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tid:0x{:01x}",
           (uint64_t) tid
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tdest_t1_t::_byteWidth);
        _ret = tid;
    }
    inline void unpack(const _packedSt &_src)
    {
        tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<tdest_t1_t::_bitWidth> sc_pack(void) const
    {
        sc_bv<tdest_t1_t::_bitWidth> packed_data;
        packed_data.range(3, 0) = tid;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<tdest_t1_t::_bitWidth> packed_data)
    {
        tid = (bv4_t) packed_data.range(3, 0).to_uint64();
    }
    explicit tdest_t1_t(sc_bv<tdest_t1_t::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit tdest_t1_t(
        bv4_t tid_) :
        tid(tid_)
    {}
    explicit tdest_t1_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tuser_t1_t {
    bv16_t parity; //

    tuser_t1_t() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const tuser_t1_t & rhs) const {
        bool ret = true;
        ret = ret && (parity == rhs.parity);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tuser_t1_t & v, const std::string & NAME ) {
        sc_trace(tf,v.parity, NAME + ".parity");
    }
    inline friend ostream& operator << ( ostream& os,  tuser_t1_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("parity:0x{:04x}",
           (uint64_t) parity
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tuser_t1_t::_byteWidth);
        _ret = parity;
    }
    inline void unpack(const _packedSt &_src)
    {
        parity = (bv16_t)((_src));
    }
    inline sc_bv<tuser_t1_t::_bitWidth> sc_pack(void) const
    {
        sc_bv<tuser_t1_t::_bitWidth> packed_data;
        packed_data.range(15, 0) = parity;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<tuser_t1_t::_bitWidth> packed_data)
    {
        parity = (bv16_t) packed_data.range(15, 0).to_uint64();
    }
    explicit tuser_t1_t(sc_bv<tuser_t1_t::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit tuser_t1_t(
        bv16_t parity_) :
        parity(parity_)
    {}
    explicit tuser_t1_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct data_t2_t {
    bv64_t data; //

    data_t2_t() {}

    static constexpr uint16_t _bitWidth = 64;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const data_t2_t & rhs) const {
        bool ret = true;
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const data_t2_t & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  data_t2_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("data:0x{:016x}",
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, data_t2_t::_byteWidth);
        _ret = data;
    }
    inline void unpack(const _packedSt &_src)
    {
        data = (bv64_t)((_src));
    }
    inline sc_bv<data_t2_t::_bitWidth> sc_pack(void) const
    {
        sc_bv<data_t2_t::_bitWidth> packed_data;
        packed_data.range(63, 0) = data;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<data_t2_t::_bitWidth> packed_data)
    {
        data = (bv64_t) packed_data.range(63, 0).to_uint64();
    }
    explicit data_t2_t(sc_bv<data_t2_t::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit data_t2_t(
        bv64_t data_) :
        data(data_)
    {}
    explicit data_t2_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tid_t2_t {
    bv4_t tid; //

    tid_t2_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const tid_t2_t & rhs) const {
        bool ret = true;
        ret = ret && (tid == rhs.tid);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tid_t2_t & v, const std::string & NAME ) {
        sc_trace(tf,v.tid, NAME + ".tid");
    }
    inline friend ostream& operator << ( ostream& os,  tid_t2_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tid:0x{:01x}",
           (uint64_t) tid
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tid_t2_t::_byteWidth);
        _ret = tid;
    }
    inline void unpack(const _packedSt &_src)
    {
        tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<tid_t2_t::_bitWidth> sc_pack(void) const
    {
        sc_bv<tid_t2_t::_bitWidth> packed_data;
        packed_data.range(3, 0) = tid;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<tid_t2_t::_bitWidth> packed_data)
    {
        tid = (bv4_t) packed_data.range(3, 0).to_uint64();
    }
    explicit tid_t2_t(sc_bv<tid_t2_t::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit tid_t2_t(
        bv4_t tid_) :
        tid(tid_)
    {}
    explicit tid_t2_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tdest_t2_t {
    bv4_t tid; //

    tdest_t2_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const tdest_t2_t & rhs) const {
        bool ret = true;
        ret = ret && (tid == rhs.tid);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tdest_t2_t & v, const std::string & NAME ) {
        sc_trace(tf,v.tid, NAME + ".tid");
    }
    inline friend ostream& operator << ( ostream& os,  tdest_t2_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tid:0x{:01x}",
           (uint64_t) tid
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tdest_t2_t::_byteWidth);
        _ret = tid;
    }
    inline void unpack(const _packedSt &_src)
    {
        tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<tdest_t2_t::_bitWidth> sc_pack(void) const
    {
        sc_bv<tdest_t2_t::_bitWidth> packed_data;
        packed_data.range(3, 0) = tid;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<tdest_t2_t::_bitWidth> packed_data)
    {
        tid = (bv4_t) packed_data.range(3, 0).to_uint64();
    }
    explicit tdest_t2_t(sc_bv<tdest_t2_t::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit tdest_t2_t(
        bv4_t tid_) :
        tid(tid_)
    {}
    explicit tdest_t2_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tuser_t2_t {
    bv4_t parity; //

    tuser_t2_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const tuser_t2_t & rhs) const {
        bool ret = true;
        ret = ret && (parity == rhs.parity);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tuser_t2_t & v, const std::string & NAME ) {
        sc_trace(tf,v.parity, NAME + ".parity");
    }
    inline friend ostream& operator << ( ostream& os,  tuser_t2_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("parity:0x{:01x}",
           (uint64_t) parity
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tuser_t2_t::_byteWidth);
        _ret = parity;
    }
    inline void unpack(const _packedSt &_src)
    {
        parity = (bv4_t)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<tuser_t2_t::_bitWidth> sc_pack(void) const
    {
        sc_bv<tuser_t2_t::_bitWidth> packed_data;
        packed_data.range(3, 0) = parity;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<tuser_t2_t::_bitWidth> packed_data)
    {
        parity = (bv4_t) packed_data.range(3, 0).to_uint64();
    }
    explicit tuser_t2_t(sc_bv<tuser_t2_t::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit tuser_t2_t(
        bv4_t parity_) :
        parity(parity_)
    {}
    explicit tuser_t2_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace axi4sDemo_tb_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace axi4sDemo_tb_ns {
template<typename Config>
class test_axi4sDemo_tb_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace axi4sDemo_tb_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace axi4sDemo_tb_ns {
template<typename Config>
std::string test_axi4sDemo_tb_structs<Config>::name(void) { return "test_axi4sDemo_tb_structs"; }
template<typename Config>
void test_axi4sDemo_tb_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        data_t1_t::_packedSt packed;
        memset(&packed, pattern, data_t1_t::_byteWidth);
        sc_bv<data_t1_t::_bitWidth> aInit;
        sc_bv<data_t1_t::_bitWidth> aTest;
        for (int i = 0; i < data_t1_t::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, data_t1_t::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        data_t1_t a;
        a.sc_unpack(aInit);
        data_t1_t b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"data_t1_t fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"data_t1_t fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = data_t1_t::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"data_t1_t fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        tid_t1_t::_packedSt packed;
        memset(&packed, pattern, tid_t1_t::_byteWidth);
        sc_bv<tid_t1_t::_bitWidth> aInit;
        sc_bv<tid_t1_t::_bitWidth> aTest;
        for (int i = 0; i < tid_t1_t::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, tid_t1_t::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        tid_t1_t a;
        a.sc_unpack(aInit);
        tid_t1_t b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"tid_t1_t fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"tid_t1_t fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = tid_t1_t::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"tid_t1_t fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        tdest_t1_t::_packedSt packed;
        memset(&packed, pattern, tdest_t1_t::_byteWidth);
        sc_bv<tdest_t1_t::_bitWidth> aInit;
        sc_bv<tdest_t1_t::_bitWidth> aTest;
        for (int i = 0; i < tdest_t1_t::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, tdest_t1_t::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        tdest_t1_t a;
        a.sc_unpack(aInit);
        tdest_t1_t b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"tdest_t1_t fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"tdest_t1_t fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = tdest_t1_t::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"tdest_t1_t fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        tuser_t1_t::_packedSt packed;
        memset(&packed, pattern, tuser_t1_t::_byteWidth);
        sc_bv<tuser_t1_t::_bitWidth> aInit;
        sc_bv<tuser_t1_t::_bitWidth> aTest;
        for (int i = 0; i < tuser_t1_t::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, tuser_t1_t::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        tuser_t1_t a;
        a.sc_unpack(aInit);
        tuser_t1_t b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"tuser_t1_t fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"tuser_t1_t fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = tuser_t1_t::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"tuser_t1_t fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        data_t2_t::_packedSt packed;
        memset(&packed, pattern, data_t2_t::_byteWidth);
        sc_bv<data_t2_t::_bitWidth> aInit;
        sc_bv<data_t2_t::_bitWidth> aTest;
        for (int i = 0; i < data_t2_t::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, data_t2_t::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        data_t2_t a;
        a.sc_unpack(aInit);
        data_t2_t b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"data_t2_t fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"data_t2_t fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = data_t2_t::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"data_t2_t fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        tid_t2_t::_packedSt packed;
        memset(&packed, pattern, tid_t2_t::_byteWidth);
        sc_bv<tid_t2_t::_bitWidth> aInit;
        sc_bv<tid_t2_t::_bitWidth> aTest;
        for (int i = 0; i < tid_t2_t::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, tid_t2_t::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        tid_t2_t a;
        a.sc_unpack(aInit);
        tid_t2_t b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"tid_t2_t fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"tid_t2_t fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = tid_t2_t::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"tid_t2_t fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        tdest_t2_t::_packedSt packed;
        memset(&packed, pattern, tdest_t2_t::_byteWidth);
        sc_bv<tdest_t2_t::_bitWidth> aInit;
        sc_bv<tdest_t2_t::_bitWidth> aTest;
        for (int i = 0; i < tdest_t2_t::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, tdest_t2_t::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        tdest_t2_t a;
        a.sc_unpack(aInit);
        tdest_t2_t b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"tdest_t2_t fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"tdest_t2_t fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = tdest_t2_t::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"tdest_t2_t fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        tuser_t2_t::_packedSt packed;
        memset(&packed, pattern, tuser_t2_t::_byteWidth);
        sc_bv<tuser_t2_t::_bitWidth> aInit;
        sc_bv<tuser_t2_t::_bitWidth> aTest;
        for (int i = 0; i < tuser_t2_t::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, tuser_t2_t::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        tuser_t2_t a;
        a.sc_unpack(aInit);
        tuser_t2_t b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"tuser_t2_t fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"tuser_t2_t fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = tuser_t2_t::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"tuser_t2_t fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace axi4sDemo_tb_ns

// GENERATED_CODE_END
