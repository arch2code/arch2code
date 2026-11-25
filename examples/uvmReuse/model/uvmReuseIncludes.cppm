
// GENERATED_CODE_PARAM --project=uvmReuse --context=../../yaml/uvmReuse.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module uvmReuse;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace uvmReuse_ns {
//constants
inline constexpr uint32_t UVM_REUSE_PACKETS = 4;  // Packets uDrv sends in the SystemC testbench
inline constexpr uint32_t UVM_REUSE_PACKET_WORDS = 8;  // Words per packet uDrv sends in the SystemC testbench
inline constexpr uint32_t UVM_REUSE_TB_OFFSET_A = 33;  // uLeafA offset uDrv programs
inline constexpr uint32_t UVM_REUSE_TB_OFFSET_B = 3;  // uLeafB offset uDrv programs

} // namespace uvmReuse_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace uvmReuse_ns {
// types
typedef uint8_t uvmReuseCountT; // [8] Tick count

} // namespace uvmReuse_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace uvmReuse_ns {
// enums
enum  addr_id_uvm_reuse_chain { //Generated type for addressing chain instances
    ADDR_ID_UVM_REUSE_CHAIN_ULEAFA=0,   // uLeafA instance address
    ADDR_ID_UVM_REUSE_CHAIN_ULEAFB=1 }; // uLeafB instance address
inline const char* addr_id_uvm_reuse_chain_prt( addr_id_uvm_reuse_chain val )
{
    switch( val )
    {
        case ADDR_ID_UVM_REUSE_CHAIN_ULEAFA: return( "ADDR_ID_UVM_REUSE_CHAIN_ULEAFA" );
        case ADDR_ID_UVM_REUSE_CHAIN_ULEAFB: return( "ADDR_ID_UVM_REUSE_CHAIN_ULEAFB" );
    }
    return("!!!BADENUM!!!");
}

} // namespace uvmReuse_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace uvmReuse_ns {
// structures
struct uvmReuseCountSt {
    uvmReuseCountT count; //Tick count

    uvmReuseCountSt() {}

    static constexpr uint16_t _bitWidth = 8;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const uvmReuseCountSt & rhs) const {
        bool ret = true;
        ret = ret && (count == rhs.count);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmReuseCountSt & v, const std::string & NAME ) {
        sc_trace(tf,v.count, NAME + ".count");
    }
    inline friend ostream& operator << ( ostream& os,  uvmReuseCountSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("count:0x{:02x}",
           (uint64_t) count
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = count;
    }
    inline void unpack(const _packedSt &_src)
    {
        count = (uvmReuseCountT)((_src));
    }
    inline sc_bv<uvmReuseCountSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmReuseCountSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        const int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmReuseCountSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmReuseCountSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmReuseCountSt(const sc_bv<uvmReuseCountSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmReuseCountSt(
        uvmReuseCountT count_) :
        count(count_)
    {}
    explicit uvmReuseCountSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace uvmReuse_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace uvmReuse_ns {
inline sc_bv<uvmReuseCountSt::_bitWidth> testRefPack(const uvmReuseCountSt &x);
inline void testRefUnpack(uvmReuseCountSt &x, const sc_bv<uvmReuseCountSt::_bitWidth> &packed_data);
inline sc_bv<uvmReuseCountSt::_bitWidth> testRefPack(const uvmReuseCountSt &x)
{
    sc_bv<uvmReuseCountSt::_bitWidth> packed_data;
    packed_data.range(0+8-1, 0) = x.count;
    return packed_data;
}
inline void testRefUnpack(uvmReuseCountSt &x, const sc_bv<uvmReuseCountSt::_bitWidth> &packed_data)
{
    x.count = (uvmReuseCountT) packed_data.range(0+8-1, 0).to_uint64();
}
} // namespace uvmReuse_ns
export namespace uvmReuse_test_ns {
class test_uvmReuse_structs {
public:
    static std::string name(void);
    static void test(void);
private:
    template<typename T>
    static void roundTrip(const char* sName, const std::vector<uint8_t>& patterns) {
        for(auto pattern : patterns) {
            roundTripBytes<T>(sName, pattern, 0);
        }
        // Bytes that differ by position expose a field placed a whole number of bytes off.
        roundTripBytes<T>(sName, 0x5b, 0x35);
    }
    template<typename T>
    static void roundTripBytes(const char* sName, uint8_t first, uint8_t step) {
        using P = typename T::_packedSt;
        P words{};
        sc_bv<T::_bitWidth> aInit;
        for (int i = 0; i < T::_byteWidth; i++) {
            uint8_t byte = (uint8_t)(first + i * step);
            int end = std::min((i+1)*8-1, T::_bitWidth-1);
            aInit.range(end, i*8) = byte;
            if constexpr (std::is_array_v<P>) {
                words[i / 8] |= (uint64_t)byte << ((i % 8) * 8);
            } else {
                words |= (P)((uint64_t)byte << (i * 8));
            }
        }
        T ref;
        testRefUnpack(ref, aInit);
        Q_ASSERT(testRefPack(ref) == aInit, std::string(sName) + ": testRefPack(testRefUnpack(pattern)) is not the pattern");
        T b;
        b.unpack(words);
        if (!(b == ref)) {
            cout << ref.prt() << endl << b.prt() << endl;
            Q_ASSERT(false, std::string(sName) + ": unpack() differs from the reference layout");
        }
        T c;
        c.sc_unpack(aInit);
        if (!(c == ref)) {
            cout << ref.prt() << endl << c.prt() << endl;
            Q_ASSERT(false, std::string(sName) + ": sc_unpack() differs from the reference layout");
        }
        P out;
        ref.pack(out);
        sc_bv<T::_bitWidth> outBits;
        for (int i = 0; i < T::_bitWidth; i++) {
            uint64_t word;
            if constexpr (std::is_array_v<P>) {
                word = out[i / 64];
            } else {
                word = (uint64_t)out;
            }
            outBits[i] = (bool)((word >> (i % 64)) & 1);
        }
        if (!(outBits == aInit)) {
            cout << ref.prt() << endl << outBits << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": pack() differs from the reference layout");
        }
        sc_bv<T::_bitWidth> scPacked = ref.sc_pack();
        if (!(scPacked == aInit)) {
            cout << ref.prt() << endl << scPacked << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": sc_pack() differs from the reference layout");
        }
        b.pack(out);
        for (int i = 0; i < T::_bitWidth; i++) {
            uint64_t word;
            if constexpr (std::is_array_v<P>) {
                word = out[i / 64];
            } else {
                word = (uint64_t)out;
            }
            outBits[i] = (bool)((word >> (i % 64)) & 1);
        }
        if (!(outBits == aInit)) {
            cout << b.prt() << endl << outBits << endl << aInit << endl;
            Q_ASSERT(false, std::string(sName) + ": pack(unpack(pattern)) is not the pattern");
        }
    }
};
} // namespace uvmReuse_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace uvmReuse_test_ns {
using namespace uvmReuse_ns;
struct uvmReuseTestConfigDefault {
    static constexpr uint32_t UVM_REUSE_B_W = 8;
};
struct uvmReuseTestConfigMid {
    static constexpr uint32_t UVM_REUSE_B_W = 4;
};
std::string test_uvmReuse_structs::name(void) { return "test_uvmReuse_structs"; }
void test_uvmReuse_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<uvmReuseCountSt>("uvmReuseCountSt", patterns);
}
} // namespace uvmReuse_test_ns

// GENERATED_CODE_END
