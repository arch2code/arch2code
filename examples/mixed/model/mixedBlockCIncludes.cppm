
// GENERATED_CODE_PARAM --context=mixedBlockC.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module mixedBlockC;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace mixedBlockC_ns {
//constants
const uint32_t CSIZE = 2;  // The size of C
const uint32_t CSIZE_PLUS = 3;  // The size of C plus 1

} // namespace mixedBlockC_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace mixedBlockC_ns {
// types
typedef uint8_t cSizeT; // [2] size of c
typedef uint8_t cSizePlusT; // [3] size of c plus 1
typedef uint16_t cBiggerT; // [13] yet another type

} // namespace mixedBlockC_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace mixedBlockC_ns {
// enums

} // namespace mixedBlockC_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace mixedBlockC_ns {
// structures
struct seeSt {
    cSizePlusT variablec2; //Three bits of C
    cSizeT variablec; //Two bits of C

    seeSt() {}

    static constexpr uint16_t _bitWidth = CSIZE_PLUS + CSIZE;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const seeSt & rhs) const {
        bool ret = true;
        ret = ret && (variablec == rhs.variablec);
        ret = ret && (variablec2 == rhs.variablec2);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const seeSt & v, const std::string & NAME ) {
        sc_trace(tf,v.variablec, NAME + ".variablec");
        sc_trace(tf,v.variablec2, NAME + ".variablec2");
    }
    inline friend ostream& operator << ( ostream& os,  seeSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("variablec:0x{:01x} variablec2:0x{:01x}",
           (uint64_t) variablec,
           (uint64_t) variablec2
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, seeSt::_byteWidth);
        _ret = variablec2;
        _ret |= (uint8_t)variablec << (3 & 7);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        variablec2 = (cSizePlusT)((_src >> (_pos & 7)) & ((1ULL << 3) - 1));
        _pos += 3;
        variablec = (cSizeT)((_src >> (_pos & 7)) & ((1ULL << 2) - 1));
    }
    inline sc_bv<seeSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<seeSt::_bitWidth> packed_data;
        packed_data.range(2, 0) = variablec2;
        packed_data.range(4, 3) = variablec;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<seeSt::_bitWidth> packed_data)
    {
        variablec2 = (cSizePlusT) packed_data.range(2, 0).to_uint64();
        variablec = (cSizeT) packed_data.range(4, 3).to_uint64();
    }
    explicit seeSt(sc_bv<seeSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit seeSt(
        cSizePlusT variablec2_,
        cSizeT variablec_) :
        variablec2(variablec2_),
        variablec(variablec_)
    {}
    explicit seeSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct cHeaderSt {
    cBiggerT hdr; //

    cHeaderSt() {}

    static constexpr uint16_t _bitWidth = 13;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const cHeaderSt & rhs) const {
        bool ret = true;
        ret = ret && (hdr == rhs.hdr);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const cHeaderSt & v, const std::string & NAME ) {
        sc_trace(tf,v.hdr, NAME + ".hdr");
    }
    inline friend ostream& operator << ( ostream& os,  cHeaderSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("hdr:0x{:04x}",
           (uint64_t) hdr
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, cHeaderSt::_byteWidth);
        _ret = hdr;
    }
    inline void unpack(const _packedSt &_src)
    {
        hdr = (cBiggerT)((_src) & ((1ULL << 13) - 1));
    }
    inline sc_bv<cHeaderSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<cHeaderSt::_bitWidth> packed_data;
        packed_data.range(12, 0) = hdr;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<cHeaderSt::_bitWidth> packed_data)
    {
        hdr = (cBiggerT) packed_data.range(12, 0).to_uint64();
    }
    explicit cHeaderSt(sc_bv<cHeaderSt::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit cHeaderSt(
        cBiggerT hdr_) :
        hdr(hdr_)
    {}
    explicit cHeaderSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace mixedBlockC_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace mixedBlockC_ns {
template<typename Config>
class test_mixedBlockC_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace mixedBlockC_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace mixedBlockC_ns {
template<typename Config>
std::string test_mixedBlockC_structs<Config>::name(void) { return "test_mixedBlockC_structs"; }
template<typename Config>
void test_mixedBlockC_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        seeSt::_packedSt packed;
        memset(&packed, pattern, seeSt::_byteWidth);
        sc_bv<seeSt::_bitWidth> aInit;
        sc_bv<seeSt::_bitWidth> aTest;
        for (int i = 0; i < seeSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, seeSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        seeSt a;
        a.sc_unpack(aInit);
        seeSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"seeSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"seeSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = seeSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"seeSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
    for(auto pattern : patterns) {
        cHeaderSt::_packedSt packed;
        memset(&packed, pattern, cHeaderSt::_byteWidth);
        sc_bv<cHeaderSt::_bitWidth> aInit;
        sc_bv<cHeaderSt::_bitWidth> aTest;
        for (int i = 0; i < cHeaderSt::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, cHeaderSt::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        cHeaderSt a;
        a.sc_unpack(aInit);
        cHeaderSt b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"cHeaderSt fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"cHeaderSt fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = cHeaderSt::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"cHeaderSt fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace mixedBlockC_ns

// GENERATED_CODE_END
