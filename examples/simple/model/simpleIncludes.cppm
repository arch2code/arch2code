
// GENERATED_CODE_PARAM --context=simple.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module simple;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace simple_ns {
//constants
const uint32_t NUM_TAGS = 32;  // number of tags
const uint32_t NUM_TAGS_LOG2 = 5;  // log2 of number of tags

} // namespace simple_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace simple_ns {
// types
typedef uint8_t tag; // [5] tag

} // namespace simple_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace simple_ns {
// enums

} // namespace simple_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace simple_ns {
// structures
struct tag_st {
    tag tagId; //tag id

    tag_st() {}

    static constexpr uint16_t _bitWidth = NUM_TAGS_LOG2;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const tag_st & rhs) const {
        bool ret = true;
        ret = ret && (tagId == rhs.tagId);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const tag_st & v, const std::string & NAME ) {
        sc_trace(tf,v.tagId, NAME + ".tagId");
    }
    inline friend ostream& operator << ( ostream& os,  tag_st const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("tagId:0x{:02x}",
           (uint64_t) tagId
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, tag_st::_byteWidth);
        _ret = tagId;
    }
    inline void unpack(const _packedSt &_src)
    {
        tagId = (tag)((_src) & ((1ULL << 5) - 1));
    }
    inline sc_bv<tag_st::_bitWidth> sc_pack(void) const
    {
        sc_bv<tag_st::_bitWidth> packed_data;
        packed_data.range(4, 0) = tagId;
        return packed_data;
    }
    inline void sc_unpack(sc_bv<tag_st::_bitWidth> packed_data)
    {
        tagId = (tag) packed_data.range(4, 0).to_uint64();
    }
    explicit tag_st(sc_bv<tag_st::_bitWidth> packed_data) { sc_unpack(packed_data); }
    explicit tag_st(
        tag tagId_) :
        tagId(tagId_)
    {}
    explicit tag_st(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace simple_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace simple_ns {
template<typename Config>
class test_simple_structs {
public:
    static std::string name(void);
    static void test(void);
};
} // namespace simple_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace simple_ns {
template<typename Config>
std::string test_simple_structs<Config>::name(void) { return "test_simple_structs"; }
template<typename Config>
void test_simple_structs<Config>::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    for(auto pattern : patterns) {
        tag_st::_packedSt packed;
        memset(&packed, pattern, tag_st::_byteWidth);
        sc_bv<tag_st::_bitWidth> aInit;
        sc_bv<tag_st::_bitWidth> aTest;
        for (int i = 0; i < tag_st::_byteWidth; i++) {
            int end = std::min((i+1)*8-1, tag_st::_bitWidth-1);
            aInit.range(end, i*8) = pattern;
        }
        tag_st a;
        a.sc_unpack(aInit);
        tag_st b;
        b.unpack(packed);
        if (!(b == a)) {;
            cout << a.prt();
            cout << b.prt();
            Q_ASSERT(false,"tag_st fail");
        }
        uint64_t test;
        memset(&test, pattern, 8);
        b.pack(packed);
        aTest = a.sc_pack();
        if (!(aTest == aInit)) {;
            cout << a.prt();
            cout << aTest;
            Q_ASSERT(false,"tag_st fail");
        }
        uint64_t *ptr = (uint64_t *)&packed;
        uint16_t bitsLeft = tag_st::_bitWidth;
        do {
            int bits = std::min((uint16_t)64, bitsLeft);
            uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);
            if ((*ptr & mask) != (test & mask)) {;
                cout << a.prt();
                cout << b.prt();
                Q_ASSERT(false,"tag_st fail");
            }
            bitsLeft -= bits;
            ptr++;
        } while(bitsLeft > 0);
    }
}
} // namespace simple_ns

// GENERATED_CODE_END
