// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Packed-form harness for the five AXI envelope structs in
// interfaces/axi_read/axi_read_channel.h and interfaces/axi_write/axi_write_channel.h.
//
// The oracle places each field bit by bit, so a field shifted, dropped or
// polluted by stack bytes fails. The fast-fail group requires bits above a
// payload's declared width to reach the neighbouring field, because pack
// deliberately does not mask.

#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstring>

#include "axi_read_channel.h"
#include "axi_write_channel.h"

static uint64_t checks = 0;
static uint64_t failures = 0;

static void expect(bool ok, const char *what)
{
    checks++;
    if (!ok) {
        failures++;
        printf("FAIL %s\n", what);
    }
}

template <size_t N>
static void expectWords(const uint64_t (&got)[N], const uint64_t (&want)[N], const char *what)
{
    for (size_t i = 0; i < N; i++) {
        checks++;
        if (got[i] != want[i]) {
            failures++;
            printf("FAIL %s: word %zu got 0x%016" PRIx64 " want 0x%016" PRIx64 "\n", what, i, got[i], want[i]);
        }
    }
}

// Scalar payloads in the generator's form: pack assigns the field without
// masking, unpack masks to the declared width.
template <typename Storage, unsigned W>
struct scalarPayload {
    Storage v{0};
    static constexpr uint16_t _bitWidth = W;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef Storage _packedSt;
    bool operator == (const scalarPayload & rhs) const { return v == rhs.v; }
    void pack(_packedSt &_ret) const { _ret = v; }
    void unpack(const _packedSt &_src) { v = (Storage)(_src & ((1ULL << W) - 1)); }
};
using narrow8 = scalarPayload<uint8_t, 5>;
using narrow32 = scalarPayload<uint32_t, 20>;
// Widths that make the scalar field after the payload straddle bit 63/64.
using cross48 = scalarPayload<uint64_t, 48>;
using cross50 = scalarPayload<uint64_t, 50>;
using cross51 = scalarPayload<uint64_t, 51>;
using cross56 = scalarPayload<uint64_t, 56>;
using cross59 = scalarPayload<uint64_t, 59>;

// 100-bit payload held in the generator's uint64_t[2] packed form.
struct widePayload {
    uint64_t lo{0};
    uint64_t hi{0};
    static constexpr uint16_t _bitWidth = 100;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    bool operator == (const widePayload & rhs) const { return lo == rhs.lo && hi == rhs.hi; }
    void pack(_packedSt &_ret) const { _ret[0] = lo; _ret[1] = hi; }
    void unpack(const _packedSt &_src) { lo = _src[0]; hi = _src[1] & ((1ULL << 36) - 1); }
};

// Oracle: builds the expected packed words one bit at a time, field by field.
template <size_t N>
struct layout {
    uint64_t words[N]{};
    unsigned pos{0};
    void put(uint64_t value, unsigned width)
    {
        for (unsigned b = 0; b < width; b++, pos++) {
            if (b < 64 && ((value >> b) & 1)) {
                words[pos >> 6] |= 1ULL << (pos & 63);
            }
        }
    }
    template <typename S, unsigned W>
    void put(const scalarPayload<S, W> &p) { put(p.v, W); }
    void put(const widePayload &p)
    {
        put(p.lo, 64);
        put(p.hi, widePayload::_bitWidth - 64);
    }
    void put(const std::monostate &) {}
};

static narrow8 make8(uint8_t v) { narrow8 p; p.v = v; return p; }
static narrow32 make32(uint32_t v) { narrow32 p; p.v = v; return p; }
template <typename P> static P makeCross() { P p; p.v = 0xD3C2B1A0F9E8D7C6ULL & ((1ULL << P::_bitWidth) - 1); return p; }
static widePayload makeWide(uint64_t lo, uint64_t hi) { widePayload p; p.lo = lo; p.hi = hi; return p; }

template <typename P> P sample();
template <> narrow8 sample<narrow8>() { return make8(0x15); }
template <> narrow32 sample<narrow32>() { return make32(0xA5C3E); }
template <> widePayload sample<widePayload>() { return makeWide(0xF00DFACECAFEBEEFULL, 0xB1E55C0DEULL); }
template <> cross48 sample<cross48>() { return makeCross<cross48>(); }
template <> cross50 sample<cross50>() { return makeCross<cross50>(); }
template <> cross51 sample<cross51>() { return makeCross<cross51>(); }
template <> cross56 sample<cross56>() { return makeCross<cross56>(); }
template <> cross59 sample<cross59>() { return makeCross<cross59>(); }
template <> std::monostate sample<std::monostate>() { return {}; }

// A second sample for user fields, distinct from the payload sample, so a user
// field unpacked from the payload's position fails.
template <typename P> P userSample();
template <> narrow8 userSample<narrow8>() { return make8(0x0B); }
template <> narrow32 userSample<narrow32>() { return make32(0x5F1A3); }
template <> widePayload userSample<widePayload>() { return makeWide(0x0123456789ABCDEFULL, 0x9876543AULL); }
template <> std::monostate userSample<std::monostate>() { return {}; }

template <typename A, typename U>
static void checkReadAddress(const char *what)
{
    using St = axiReadAddressSt<A, U>;
    St in;
    in.arid = 0xA;
    in.araddr = sample<A>();
    in.arlen = 0xC7;
    in.arsize = 5;
    in.arburst = AXIBURST_WRAP;
    in.user = userSample<U>();

    layout<St::_packedSize> want;
    want.put(in.arid, St::idWidth);
    want.put(in.araddr);
    want.put(in.arlen, St::lenWidth);
    want.put(in.arsize, St::sizeWidth);
    want.put(in.arburst, St::burstWidth);
    want.put(in.user);
    expect(want.pos == St::_bitWidth, what);

    typename St::_packedSt packed{};
    in.pack(packed);
    expectWords(packed, want.words, what);

    St out;
    out.unpack(packed);
    expect(out == in, what);
}

template <typename A, typename U>
static void checkWriteAddress(const char *what)
{
    using St = axiWriteAddressSt<A, U>;
    St in;
    in.awid = 0x6;
    in.awaddr = sample<A>();
    in.awlen = 0x3B;
    in.awsize = 3;
    in.awburst = AXIBURST_INCR;
    in.user = userSample<U>();

    layout<St::_packedSize> want;
    want.put(in.awid, St::idWidth);
    want.put(in.awaddr);
    want.put(in.awlen, St::lenWidth);
    want.put(in.awsize, St::sizeWidth);
    want.put(in.awburst, St::burstWidth);
    want.put(in.user);
    expect(want.pos == St::_bitWidth, what);

    typename St::_packedSt packed{};
    in.pack(packed);
    expectWords(packed, want.words, what);

    St out;
    out.unpack(packed);
    expect(out == in, what);
}

template <typename D, typename U>
static void checkReadResp(const char *what)
{
    using St = axiReadRespSt<D, U>;
    St in;
    in.rid = 0x9;
    in.rdata = sample<D>();
    in.rresp = AXIRESP_DECERR;
    in.rlast = true;
    in.user = userSample<U>();

    layout<St::_packedSize> want;
    want.put(in.rid, St::idWidth);
    want.put(in.rdata);
    want.put(in.rresp, St::respWidth);
    want.put(in.rlast, St::lastWidth);
    want.put(in.user);
    expect(want.pos == St::_bitWidth, what);

    typename St::_packedSt packed{};
    in.pack(packed);
    expectWords(packed, want.words, what);

    St out;
    out.unpack(packed);
    expect(out == in, what);
}

template <typename D, typename S, typename U>
static void checkWriteData(const char *what)
{
    using St = axiWriteDataSt<D, S, U>;
    St in;
    in.wid = 0x5;
    in.wdata = sample<D>();
    in.wstrb = make8(0x1D);
    in.wlast = true;
    in.user = userSample<U>();

    layout<St::_packedSize> want;
    want.put(in.wid, St::idWidth);
    want.put(in.wdata);
    want.put(in.wstrb);
    want.put(in.wlast, St::lastWidth);
    want.put(in.user);
    expect(want.pos == St::_bitWidth, what);

    typename St::_packedSt packed{};
    in.pack(packed);
    expectWords(packed, want.words, what);

    St out;
    out.unpack(packed);
    expect(out == in, what);
}

template <typename U>
static void checkWriteResp(const char *what)
{
    using St = axiWriteRespSt<U>;
    St in;
    in.bid = 0xE;
    in.bresp = AXIRESP_SLVERR;
    in.user = userSample<U>();

    layout<St::_packedSize> want;
    want.put(in.bid, St::idWidth);
    want.put(in.bresp, St::respWidth);
    want.put(in.user);
    expect(want.pos == St::_bitWidth, what);

    typename St::_packedSt packed{};
    in.pack(packed);
    expectWords(packed, want.words, what);

    St out;
    out.unpack(packed);
    expect(out == in, what);
}

// Bits above a payload's declared width reach the packed envelope unmasked,
// ORed over the fields that follow it.
static void checkFastFail()
{
    {
        // narrow32 is 20 bits; bits 20..27 land on arlen at offset 24.
        using St = axiReadAddressSt<narrow32>;
        St in;
        in.arid = 0x1;
        in.araddr = make32(0x0FF00001);
        in.arlen = 0;
        in.arsize = 0;
        in.arburst = AXIBURST_FIXED;
        typename St::_packedSt packed{};
        in.pack(packed);
        uint64_t want[St::_packedSize] = { 0x1ULL | (0x0FF00001ULL << St::idWidth) };
        expectWords(packed, want, "fast-fail axiReadAddressSt<narrow32> addr bits above width");
    }
    {
        // narrow8 strobe is 5 bits; bits 5..7 land on wlast and the user field.
        using St = axiWriteDataSt<narrow32, narrow8, narrow8>;
        St in;
        in.wid = 0;
        in.wdata = make32(0);
        in.wstrb = make8(0xE0);
        in.wlast = false;
        in.user = make8(0);
        typename St::_packedSt packed{};
        in.pack(packed);
        uint64_t want[St::_packedSize] = { 0xE0ULL << (St::idWidth + St::dataWidth) };
        expectWords(packed, want, "fast-fail axiWriteDataSt<narrow32,narrow8> strobe bits above width");
    }
    {
        // narrow8 user on the write response is the last field; its excess
        // bits sit above _bitWidth inside the packed word.
        using St = axiWriteRespSt<narrow8>;
        St in;
        in.bid = 0;
        in.bresp = AXIRESP_OKAY;
        in.user = make8(0xFF);
        typename St::_packedSt packed{};
        in.pack(packed);
        uint64_t want[St::_packedSize] = { 0xFFULL << (St::idWidth + St::respWidth) };
        expectWords(packed, want, "fast-fail axiWriteRespSt<narrow8> user bits above width");
    }
    {
        // widePayload is 100 bits; hi bits 36..39 land on rresp and rlast.
        using St = axiReadRespSt<widePayload>;
        St in;
        in.rid = 0;
        in.rdata = makeWide(0, 0xF000000000ULL);
        in.rresp = AXIRESP_OKAY;
        in.rlast = false;
        typename St::_packedSt packed{};
        in.pack(packed);
        uint64_t want[St::_packedSize] = { 0, 0xF000000000ULL << St::idWidth };
        expectWords(packed, want, "fast-fail axiReadRespSt<wide> data bits above width");
    }
}

int sc_main(int, char **)
{
    checkReadAddress<narrow8, std::monostate>("axiReadAddressSt<narrow8>");
    checkReadAddress<narrow32, std::monostate>("axiReadAddressSt<narrow32>");
    checkReadAddress<widePayload, std::monostate>("axiReadAddressSt<wide>");
    checkReadAddress<narrow32, narrow8>("axiReadAddressSt<narrow32,narrow8>");
    checkReadAddress<widePayload, narrow32>("axiReadAddressSt<wide,narrow32>");
    checkReadAddress<cross56, std::monostate>("axiReadAddressSt<cross56> arlen crosses word");
    checkReadAddress<cross50, std::monostate>("axiReadAddressSt<cross50> arsize crosses word");
    checkReadAddress<cross48, narrow8>("axiReadAddressSt<cross48,narrow8> arburst crosses word");

    checkWriteAddress<narrow8, std::monostate>("axiWriteAddressSt<narrow8>");
    checkWriteAddress<narrow32, std::monostate>("axiWriteAddressSt<narrow32>");
    checkWriteAddress<widePayload, std::monostate>("axiWriteAddressSt<wide>");
    checkWriteAddress<narrow32, narrow32>("axiWriteAddressSt<narrow32,narrow32>");
    checkWriteAddress<widePayload, narrow8>("axiWriteAddressSt<wide,narrow8>");
    checkWriteAddress<cross56, std::monostate>("axiWriteAddressSt<cross56> awlen crosses word");
    checkWriteAddress<cross51, narrow8>("axiWriteAddressSt<cross51,narrow8> awsize crosses word");

    checkReadResp<narrow8, std::monostate>("axiReadRespSt<narrow8>");
    checkReadResp<narrow32, std::monostate>("axiReadRespSt<narrow32>");
    checkReadResp<widePayload, std::monostate>("axiReadRespSt<wide>");
    checkReadResp<narrow32, narrow8>("axiReadRespSt<narrow32,narrow8>");
    checkReadResp<widePayload, widePayload>("axiReadRespSt<wide,wide>");
    checkReadResp<cross59, std::monostate>("axiReadRespSt<cross59> rresp crosses word");
    checkReadResp<cross59, narrow8>("axiReadRespSt<cross59,narrow8> rresp crosses word");

    checkWriteData<narrow8, narrow8, std::monostate>("axiWriteDataSt<narrow8,narrow8>");
    checkWriteData<narrow32, narrow8, std::monostate>("axiWriteDataSt<narrow32,narrow8>");
    checkWriteData<widePayload, narrow8, std::monostate>("axiWriteDataSt<wide,narrow8>");
    checkWriteData<narrow32, narrow8, narrow32>("axiWriteDataSt<narrow32,narrow8,narrow32>");
    checkWriteData<widePayload, narrow8, narrow32>("axiWriteDataSt<wide,narrow8,narrow32>");

    checkWriteResp<std::monostate>("axiWriteRespSt");
    checkWriteResp<narrow8>("axiWriteRespSt<narrow8>");
    checkWriteResp<narrow32>("axiWriteRespSt<narrow32>");
    checkWriteResp<widePayload>("axiWriteRespSt<wide>");

    checkFastFail();

    printf("checks:%" PRIu64 " failures:%" PRIu64 "\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
