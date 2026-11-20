
// GENERATED_CODE_PARAM --project=uvmMem --context=../../yaml/uvmMem.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module uvmMem;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace uvmMem_ns {
//constants
inline constexpr uint32_t UVM_MEM_WORDS = 16;  // Words in the memory the wr and rd ports reach
inline constexpr uint32_t UVM_MEM_ADDR_WIDTH = 4;  // Memory address width in bits
inline constexpr uint32_t UVM_MEM_CMDS = 64;  // Commands uSrc sends in the SystemC testbench
inline constexpr uint32_t UVM_MEM_DATA_BASE = 4096;  // Word uSrc's command 0 writes; command i writes UVM_MEM_DATA_BASE + i

} // namespace uvmMem_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace uvmMem_ns {
// types
typedef uint8_t uvmMemAddrT; // [4] Memory word address
typedef uint32_t uvmMemDataT; // [32] Memory word

} // namespace uvmMem_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace uvmMem_ns {
// enums

} // namespace uvmMem_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace uvmMem_ns {
// structures
struct uvmMemAddrSt {
    uvmMemAddrT address; //

    uvmMemAddrSt() {}

    static constexpr uint16_t _bitWidth = UVM_MEM_ADDR_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const uvmMemAddrSt & rhs) const {
        bool ret = true;
        ret = ret && (address == rhs.address);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmMemAddrSt & v, const std::string & NAME ) {
        sc_trace(tf,v.address, NAME + ".address");
    }
    inline friend ostream& operator << ( ostream& os,  uvmMemAddrSt const & v ) {
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
    inline uvmMemAddrT _getAddress(void) { return( address); }
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = address;
    }
    inline void unpack(const _packedSt &_src)
    {
        address = (uvmMemAddrT)((_src) & ((1ULL << 4) - 1));
    }
    inline sc_bv<uvmMemAddrSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmMemAddrSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmMemAddrSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmMemAddrSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmMemAddrSt(const sc_bv<uvmMemAddrSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmMemAddrSt(
        uvmMemAddrT address_) :
        address(address_)
    {}
    explicit uvmMemAddrSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmMemWordSt {
    uvmMemDataT word; //

    uvmMemWordSt() {}

    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const uvmMemWordSt & rhs) const {
        bool ret = true;
        ret = ret && (word == rhs.word);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmMemWordSt & v, const std::string & NAME ) {
        sc_trace(tf,v.word, NAME + ".word");
    }
    inline friend ostream& operator << ( ostream& os,  uvmMemWordSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("word:0x{:08x}",
           (uint64_t) word
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = word;
    }
    inline void unpack(const _packedSt &_src)
    {
        word = (uvmMemDataT)((_src));
    }
    inline sc_bv<uvmMemWordSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmMemWordSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmMemWordSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmMemWordSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmMemWordSt(const sc_bv<uvmMemWordSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmMemWordSt(
        uvmMemDataT word_) :
        word(word_)
    {}
    explicit uvmMemWordSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmMemCmdSt {
    uvmMemDataT data; //Word the command writes
    uvmMemAddrT rdAddr; //Address the command reads before its write
    uvmMemAddrT wrAddr; //Address the command writes

    uvmMemCmdSt() {}

    static constexpr uint16_t _bitWidth = 32 + UVM_MEM_ADDR_WIDTH + UVM_MEM_ADDR_WIDTH;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt;
    inline bool operator == (const uvmMemCmdSt & rhs) const {
        bool ret = true;
        ret = ret && (wrAddr == rhs.wrAddr);
        ret = ret && (rdAddr == rhs.rdAddr);
        ret = ret && (data == rhs.data);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmMemCmdSt & v, const std::string & NAME ) {
        sc_trace(tf,v.wrAddr, NAME + ".wrAddr");
        sc_trace(tf,v.rdAddr, NAME + ".rdAddr");
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  uvmMemCmdSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("wrAddr:0x{:01x} rdAddr:0x{:01x} data:0x{:08x}",
           (uint64_t) wrAddr,
           (uint64_t) rdAddr,
           (uint64_t) data
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = data;
        _ret |= (uint64_t)rdAddr << (32 & 63);
        _ret |= (uint64_t)wrAddr << (36 & 63);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        data = (uvmMemDataT)((_src >> (_pos & 63)) & ((1ULL << 32) - 1));
        _pos += 32;
        rdAddr = (uvmMemAddrT)((_src >> (_pos & 63)) & ((1ULL << 4) - 1));
        _pos += 4;
        wrAddr = (uvmMemAddrT)((_src >> (_pos & 63)) & ((1ULL << 4) - 1));
    }
    inline sc_bv<uvmMemCmdSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmMemCmdSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmMemCmdSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmMemCmdSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmMemCmdSt(const sc_bv<uvmMemCmdSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmMemCmdSt(
        uvmMemDataT data_,
        uvmMemAddrT rdAddr_,
        uvmMemAddrT wrAddr_) :
        data(data_),
        rdAddr(rdAddr_),
        wrAddr(wrAddr_)
    {}
    explicit uvmMemCmdSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace uvmMem_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace uvmMem_ns {
inline sc_bv<uvmMemAddrSt::_bitWidth> testRefPack(const uvmMemAddrSt &x);
inline void testRefUnpack(uvmMemAddrSt &x, const sc_bv<uvmMemAddrSt::_bitWidth> &packed_data);
inline sc_bv<uvmMemWordSt::_bitWidth> testRefPack(const uvmMemWordSt &x);
inline void testRefUnpack(uvmMemWordSt &x, const sc_bv<uvmMemWordSt::_bitWidth> &packed_data);
inline sc_bv<uvmMemCmdSt::_bitWidth> testRefPack(const uvmMemCmdSt &x);
inline void testRefUnpack(uvmMemCmdSt &x, const sc_bv<uvmMemCmdSt::_bitWidth> &packed_data);
inline sc_bv<uvmMemAddrSt::_bitWidth> testRefPack(const uvmMemAddrSt &x)
{
    sc_bv<uvmMemAddrSt::_bitWidth> packed_data;
    packed_data.range(0+UVM_MEM_ADDR_WIDTH-1, 0) = x.address;
    return packed_data;
}
inline void testRefUnpack(uvmMemAddrSt &x, const sc_bv<uvmMemAddrSt::_bitWidth> &packed_data)
{
    x.address = (uvmMemAddrT) packed_data.range(0+UVM_MEM_ADDR_WIDTH-1, 0).to_uint64();
}
inline sc_bv<uvmMemWordSt::_bitWidth> testRefPack(const uvmMemWordSt &x)
{
    sc_bv<uvmMemWordSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.word;
    return packed_data;
}
inline void testRefUnpack(uvmMemWordSt &x, const sc_bv<uvmMemWordSt::_bitWidth> &packed_data)
{
    x.word = (uvmMemDataT) packed_data.range(0+32-1, 0).to_uint64();
}
inline sc_bv<uvmMemCmdSt::_bitWidth> testRefPack(const uvmMemCmdSt &x)
{
    sc_bv<uvmMemCmdSt::_bitWidth> packed_data;
    packed_data.range(0+32-1, 0) = x.data;
    packed_data.range(32+UVM_MEM_ADDR_WIDTH-1, 32) = x.rdAddr;
    packed_data.range(36+UVM_MEM_ADDR_WIDTH-1, 36) = x.wrAddr;
    return packed_data;
}
inline void testRefUnpack(uvmMemCmdSt &x, const sc_bv<uvmMemCmdSt::_bitWidth> &packed_data)
{
    x.data = (uvmMemDataT) packed_data.range(0+32-1, 0).to_uint64();
    x.rdAddr = (uvmMemAddrT) packed_data.range(32+UVM_MEM_ADDR_WIDTH-1, 32).to_uint64();
    x.wrAddr = (uvmMemAddrT) packed_data.range(36+UVM_MEM_ADDR_WIDTH-1, 36).to_uint64();
}
} // namespace uvmMem_ns
export namespace uvmMem_test_ns {
class test_uvmMem_structs {
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
} // namespace uvmMem_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace uvmMem_test_ns {
using namespace uvmMem_ns;
std::string test_uvmMem_structs::name(void) { return "test_uvmMem_structs"; }
void test_uvmMem_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<uvmMemAddrSt>("uvmMemAddrSt", patterns);
    roundTrip<uvmMemWordSt>("uvmMemWordSt", patterns);
    roundTrip<uvmMemCmdSt>("uvmMemCmdSt", patterns);
}
} // namespace uvmMem_test_ns

// GENERATED_CODE_END
