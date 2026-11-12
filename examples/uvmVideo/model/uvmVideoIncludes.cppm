
// GENERATED_CODE_PARAM --project=uvmVideo --context=../../yaml/uvmVideo.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"
#include "q_assert.h"

export module uvmVideo;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace uvmVideo_ns {
//constants
inline constexpr uint32_t UVM_VIDEO_PIXELS = 2;  // Pixels per beat
inline constexpr uint32_t UVM_VIDEO_WIDTH = 16;  // Pixels per line uSrc sends in the SystemC testbench
inline constexpr uint32_t UVM_VIDEO_HEIGHT = 4;  // Lines per frame uSrc sends in the SystemC testbench
inline constexpr uint32_t UVM_VIDEO_FRAMES = 3;  // Frames uSrc sends in the SystemC testbench

} // namespace uvmVideo_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace uvmVideo_ns {
// types
typedef uint8_t uvmVideoPixelT; // [8] One pixel
typedef uint8_t uvmVideoBitT; // [1] A level or marker

} // namespace uvmVideo_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace uvmVideo_ns {
// enums

} // namespace uvmVideo_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
export namespace uvmVideo_ns {
// structures
struct uvmVideoRawSt {
    uvmVideoPixelT pixels[UVM_VIDEO_PIXELS]; //
    uvmVideoBitT lv; //Line valid
    uvmVideoBitT fv; //Frame valid

    uvmVideoRawSt() {}

    static constexpr uint16_t _bitWidth = 8*UVM_VIDEO_PIXELS + 1 + 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint32_t _packedSt;
    inline bool operator == (const uvmVideoRawSt & rhs) const {
        bool ret = true;
        ret = ret && (fv == rhs.fv);
        ret = ret && (lv == rhs.lv);
        for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
            ret = ret && (pixels[i] == rhs.pixels[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmVideoRawSt & v, const std::string & NAME ) {
        sc_trace(tf,v.fv, NAME + ".fv");
        sc_trace(tf,v.lv, NAME + ".lv");
        for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
            sc_trace(tf,v.pixels[i], NAME + ".pixels[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  uvmVideoRawSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("fv:0x{:01x} lv:0x{:01x} pixels[0:1]: {}",
           (uint64_t) fv,
           (uint64_t) lv,
           staticArrayPrt<uvmVideoPixelT, UVM_VIDEO_PIXELS>(pixels, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
            _ret |= (uint32_t)pixels[i] << (_pos & 31);
            _pos += 8;
        }
        _ret |= (uint32_t)lv << (16 & 31);
        _ret |= (uint32_t)fv << (17 & 31);
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
            uint16_t _bits = 8;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(32-(_pos & 31)));
            pixels[i] = (uvmVideoPixelT)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 32)) {
                pixels[i] = (uvmVideoPixelT)(pixels[i] | ((_src << _consume) & ((1ULL << 8) - 1)));
                _pos += _bits;
            }
        }
        lv = (uvmVideoBitT)((_src >> (_pos & 31)) & 1);
        _pos += 1;
        fv = (uvmVideoBitT)((_src >> (_pos & 31)) & 1);
    }
    inline sc_bv<uvmVideoRawSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmVideoRawSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmVideoRawSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmVideoRawSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmVideoRawSt(const sc_bv<uvmVideoRawSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmVideoRawSt(
        uvmVideoPixelT pixels_[UVM_VIDEO_PIXELS],
        uvmVideoBitT lv_,
        uvmVideoBitT fv_) :
        lv(lv_),
        fv(fv_)
    {
        memcpy(&pixels, &pixels_, sizeof(pixels));
    }
    explicit uvmVideoRawSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmVideoBeatSt {
    uvmVideoPixelT pixels[UVM_VIDEO_PIXELS]; //

    uvmVideoBeatSt() {}

    static constexpr uint16_t _bitWidth = 8*UVM_VIDEO_PIXELS;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint16_t _packedSt;
    inline bool operator == (const uvmVideoBeatSt & rhs) const {
        bool ret = true;
        for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
            ret = ret && (pixels[i] == rhs.pixels[i]);
        }
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmVideoBeatSt & v, const std::string & NAME ) {
        for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
            sc_trace(tf,v.pixels[i], NAME + ".pixels[i]");
        }
    }
    inline friend ostream& operator << ( ostream& os,  uvmVideoBeatSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("pixels[0:1]: {}",
           staticArrayPrt<uvmVideoPixelT, UVM_VIDEO_PIXELS>(pixels, all)
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        uint16_t _pos{0};
        for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
            _ret |= (uint16_t)pixels[i] << (_pos & 15);
            _pos += 8;
        }
    }
    inline void unpack(const _packedSt &_src)
    {
        uint16_t _pos{0};
        for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
            uint16_t _bits = 8;
            uint16_t _consume;
            _consume = std::min(_bits, (uint16_t)(16-(_pos & 15)));
            pixels[i] = (uvmVideoPixelT)((_src >> (_pos & 15)) & ((1ULL << 8) - 1));
            _pos += _consume;
            _bits -= _consume;
            if ((_bits > 0) && (_consume != 16)) {
                pixels[i] = (uvmVideoPixelT)(pixels[i] | ((_src << _consume) & ((1ULL << 8) - 1)));
                _pos += _bits;
            }
        }
    }
    inline sc_bv<uvmVideoBeatSt::_bitWidth> sc_pack(void) const
    {
        sc_bv<uvmVideoBeatSt::_bitWidth> packed_data;
        _packedSt _packed;
        pack(_packed);
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            packed_data.set_word(i, (sc_digit)((uint64_t)_packed >> (i * 32)));
        }
        constexpr int _last = (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE - 1;
        Q_ASSERT_CTX((packed_data.get_word(_last) & (sc_digit)(~0ULL << (_bitWidth - _last * sc_dt::SC_DIGIT_SIZE))) == 0,
                     "uvmVideoBeatSt", "a field holds more bits than its type");
        return packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmVideoBeatSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmVideoBeatSt(const sc_bv<uvmVideoBeatSt::_bitWidth> &packed_data) { sc_unpack(packed_data); }
    explicit uvmVideoBeatSt(
        uvmVideoPixelT pixels_[UVM_VIDEO_PIXELS])
    {
        memcpy(&pixels, &pixels_, sizeof(pixels));
    }
    explicit uvmVideoBeatSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmVideoIdSt {
    uvmVideoBitT id; //

    uvmVideoIdSt() {}

    static constexpr uint16_t _bitWidth = 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const uvmVideoIdSt & rhs) const {
        bool ret = true;
        ret = ret && (id == rhs.id);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmVideoIdSt & v, const std::string & NAME ) {
        sc_trace(tf,v.id, NAME + ".id");
    }
    inline friend ostream& operator << ( ostream& os,  uvmVideoIdSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("id:0x{:01x}",
           (uint64_t) id
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = id;
    }
    inline void unpack(const _packedSt &_src)
    {
        id = (uvmVideoBitT)((_src) & 1);
    }
    inline bool sc_pack(void) const
    {
        bool packed_data;
        packed_data = (bool) id;
        return packed_data;
    }
    inline void sc_unpack(bool packed_data)
    {
        id = (uvmVideoBitT) packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmVideoIdSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmVideoIdSt(bool packed_data) { sc_unpack(packed_data); }
    explicit uvmVideoIdSt(
        uvmVideoBitT id_) :
        id(id_)
    {}
    explicit uvmVideoIdSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct uvmVideoUserSt {
    uvmVideoBitT sof; //Start of frame

    uvmVideoUserSt() {}

    static constexpr uint16_t _bitWidth = 1;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint8_t _packedSt;
    inline bool operator == (const uvmVideoUserSt & rhs) const {
        bool ret = true;
        ret = ret && (sof == rhs.sof);
        return ( ret );
        }
    inline friend void sc_trace(sc_trace_file *tf, const uvmVideoUserSt & v, const std::string & NAME ) {
        sc_trace(tf,v.sof, NAME + ".sof");
    }
    inline friend ostream& operator << ( ostream& os,  uvmVideoUserSt const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const
    {
        return (std::format("sof:0x{:01x}",
           (uint64_t) sof
        ));
    }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    inline void pack(_packedSt &_ret) const
    {
        memset(&_ret, 0, sizeof(_ret));
        _ret = sof;
    }
    inline void unpack(const _packedSt &_src)
    {
        sof = (uvmVideoBitT)((_src) & 1);
    }
    inline bool sc_pack(void) const
    {
        bool packed_data;
        packed_data = (bool) sof;
        return packed_data;
    }
    inline void sc_unpack(bool packed_data)
    {
        sof = (uvmVideoBitT) packed_data;
    }
    inline void sc_unpack(const sc_bv<uvmVideoUserSt::_bitWidth> &packed_data)
    {
        uint64_t _word{0};
        for (int i = 0; i < (_bitWidth + sc_dt::SC_DIGIT_SIZE - 1) / sc_dt::SC_DIGIT_SIZE; i++) {
            _word |= (uint64_t)packed_data.get_word(i) << (i * 32);
        }
        unpack((_packedSt)_word);
    }
    explicit uvmVideoUserSt(bool packed_data) { sc_unpack(packed_data); }
    explicit uvmVideoUserSt(
        uvmVideoBitT sof_) :
        sof(sof_)
    {}
    explicit uvmVideoUserSt(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
} // namespace uvmVideo_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
export namespace uvmVideo_ns {
inline sc_bv<uvmVideoRawSt::_bitWidth> testRefPack(const uvmVideoRawSt &x);
inline void testRefUnpack(uvmVideoRawSt &x, const sc_bv<uvmVideoRawSt::_bitWidth> &packed_data);
inline sc_bv<uvmVideoBeatSt::_bitWidth> testRefPack(const uvmVideoBeatSt &x);
inline void testRefUnpack(uvmVideoBeatSt &x, const sc_bv<uvmVideoBeatSt::_bitWidth> &packed_data);
inline sc_bv<uvmVideoIdSt::_bitWidth> testRefPack(const uvmVideoIdSt &x);
inline void testRefUnpack(uvmVideoIdSt &x, const sc_bv<uvmVideoIdSt::_bitWidth> &packed_data);
inline sc_bv<uvmVideoUserSt::_bitWidth> testRefPack(const uvmVideoUserSt &x);
inline void testRefUnpack(uvmVideoUserSt &x, const sc_bv<uvmVideoUserSt::_bitWidth> &packed_data);
inline sc_bv<uvmVideoRawSt::_bitWidth> testRefPack(const uvmVideoRawSt &x)
{
    sc_bv<uvmVideoRawSt::_bitWidth> packed_data;
    for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
        packed_data.range(0+i*8+8-1, 0+i*8) = x.pixels[i];
    }
    packed_data.range(16+1-1, 16) = x.lv;
    packed_data.range(17+1-1, 17) = x.fv;
    return packed_data;
}
inline void testRefUnpack(uvmVideoRawSt &x, const sc_bv<uvmVideoRawSt::_bitWidth> &packed_data)
{
    for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
        x.pixels[i] = (uvmVideoPixelT) packed_data.range(0+i*8+8-1, 0+i*8).to_uint64();
    }
    x.lv = (uvmVideoBitT) packed_data.range(16+1-1, 16).to_uint64();
    x.fv = (uvmVideoBitT) packed_data.range(17+1-1, 17).to_uint64();
}
inline sc_bv<uvmVideoBeatSt::_bitWidth> testRefPack(const uvmVideoBeatSt &x)
{
    sc_bv<uvmVideoBeatSt::_bitWidth> packed_data;
    for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
        packed_data.range(0+i*8+8-1, 0+i*8) = x.pixels[i];
    }
    return packed_data;
}
inline void testRefUnpack(uvmVideoBeatSt &x, const sc_bv<uvmVideoBeatSt::_bitWidth> &packed_data)
{
    for(unsigned int i=0; i<UVM_VIDEO_PIXELS; i++) {
        x.pixels[i] = (uvmVideoPixelT) packed_data.range(0+i*8+8-1, 0+i*8).to_uint64();
    }
}
inline sc_bv<uvmVideoIdSt::_bitWidth> testRefPack(const uvmVideoIdSt &x)
{
    sc_bv<uvmVideoIdSt::_bitWidth> packed_data;
    packed_data.range(0+1-1, 0) = x.id;
    return packed_data;
}
inline void testRefUnpack(uvmVideoIdSt &x, const sc_bv<uvmVideoIdSt::_bitWidth> &packed_data)
{
    x.id = (uvmVideoBitT) packed_data.range(0+1-1, 0).to_uint64();
}
inline sc_bv<uvmVideoUserSt::_bitWidth> testRefPack(const uvmVideoUserSt &x)
{
    sc_bv<uvmVideoUserSt::_bitWidth> packed_data;
    packed_data.range(0+1-1, 0) = x.sof;
    return packed_data;
}
inline void testRefUnpack(uvmVideoUserSt &x, const sc_bv<uvmVideoUserSt::_bitWidth> &packed_data)
{
    x.sof = (uvmVideoBitT) packed_data.range(0+1-1, 0).to_uint64();
}
} // namespace uvmVideo_ns
export namespace uvmVideo_test_ns {
class test_uvmVideo_structs {
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
} // namespace uvmVideo_test_ns

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
export namespace uvmVideo_test_ns {
using namespace uvmVideo_ns;
std::string test_uvmVideo_structs::name(void) { return "test_uvmVideo_structs"; }
void test_uvmVideo_structs::test(void) {
    std::vector<uint8_t> patterns{0x6a, 0xa6};
    std::vector<uint8_t> signedPatterns{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF};
    cout << "Running " << name() << endl;
    roundTrip<uvmVideoRawSt>("uvmVideoRawSt", patterns);
    roundTrip<uvmVideoBeatSt>("uvmVideoBeatSt", patterns);
    roundTrip<uvmVideoIdSt>("uvmVideoIdSt", patterns);
    roundTrip<uvmVideoUserSt>("uvmVideoUserSt", patterns);
}
} // namespace uvmVideo_test_ns

// GENERATED_CODE_END
