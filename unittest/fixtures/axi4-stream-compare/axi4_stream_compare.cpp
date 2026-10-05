// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Equality harness for axi4StreamInfoSt in interfaces/axi4_stream/axi4_stream_channel.h,
// the compare a tandem tee uses to decide pass or fail.
//
// The payloads take the generator's forms for getStructValue(): -1 for a
// struct with no tracker field, and the tracker field alone for a struct that
// has one. Neither reflects the whole payload, so only the payload's own
// operator == can tell two values apart.

#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <format>
#include <string>

#include "axi4_stream_channel.h"

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

template <unsigned WORDS>
struct untrackedPayload {
    uint64_t word[WORDS]{};
    static constexpr uint16_t _bitWidth = 64 * WORDS;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[WORDS];
    inline bool operator == (const untrackedPayload & rhs) const {
        bool ret = true;
        for (unsigned i = 0; i < WORDS; i++) { ret = ret && (word[i] == rhs.word[i]); }
        return ( ret );
    }
    std::string prt(bool all=false) const { (void)all; return std::format("word0:0x{:016x}", word[0]); }
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
};
using wide256 = untrackedPayload<4>;
using wide128 = untrackedPayload<2>;
using narrow64 = untrackedPayload<1>;

struct trackedPayload {
    uint64_t cmdid = 0;
    uint64_t data = 0;
    static constexpr uint16_t _bitWidth = 128;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    typedef uint64_t _packedSt[2];
    inline bool operator == (const trackedPayload & rhs) const {
        return ( (cmdid == rhs.cmdid) && (data == rhs.data) );
    }
    std::string prt(bool all=false) const { (void)all; return std::format("cmdid:0x{:x} data:0x{:x}", cmdid, data); }
    static const char* getValueType(void) { return( "tracker:cmdid" );}
    inline uint64_t getStructValue(void) const { return( cmdid );}
};

template <typename St>
static St sample()
{
    St s;
    for (unsigned i = 0; i < 4; i++) { s.tdata.word[i] = 0x1111111111111111ULL * (i + 1); }
    for (unsigned i = 0; i < St::tdataWidth / 8; i++) { s.tstrb[i] = Q_TRUE; s.tkeep[i] = Q_TRUE; }
    s.tid.word[0] = 0x3;
    s.tlast = true;
    s.tdest.word[0] = 0x5;
    return s;
}

static void checkWithoutTuser()
{
    using St = axi4StreamInfoSt<wide256, narrow64, narrow64>;
    St a = sample<St>();
    St b = a;
    expect(a == b, "no tuser: identical 256-bit tdata compares equal");

    for (unsigned w = 1; w < 4; w++) {
        b = a;
        b.tdata.word[w] ^= 1ULL << 7;
        expect(!(a == b), std::format("no tuser: tdata differing in word {} compares unequal", w).c_str());
    }

    b = a;
    b.tdata.word[0] ^= 1;
    expect(!(a == b), "no tuser: tdata differing in word 0 compares unequal");

    b = a;
    b.tid.word[0] ^= 1;
    expect(!(a == b), "no tuser: tid difference compares unequal");

    b = a;
    b.tdest.word[0] ^= 1;
    expect(!(a == b), "no tuser: tdest difference compares unequal");
}

static void checkWithWideTuser()
{
    using St = axi4StreamInfoSt<wide256, narrow64, narrow64, wide128>;
    St a = sample<St>();
    a.tuser.word[0] = 0xAAAAAAAAAAAAAAAAULL;
    a.tuser.word[1] = 0x5555555555555555ULL;
    St b = a;
    expect(a == b, "wide tuser: identical values compare equal");

    b = a;
    b.tuser.word[1] ^= 1ULL << 40;
    expect(!(a == b), "wide tuser: tuser differing above bit 64 compares unequal");

    b = a;
    b.tdata.word[3] ^= 1ULL << 63;
    expect(!(a == b), "wide tuser: tdata differing above bit 64 compares unequal");
}

static void checkTrackedTdata()
{
    using St = axi4StreamInfoSt<trackedPayload, narrow64, narrow64>;
    St a;
    a.tdata.cmdid = 0x7;
    a.tdata.data = 0x1234;
    for (unsigned i = 0; i < St::tdataWidth / 8; i++) { a.tstrb[i] = Q_TRUE; a.tkeep[i] = Q_TRUE; }
    a.tlast = true;
    St b = a;
    expect(a == b, "tracked tdata: identical values compare equal");

    b.tdata.data ^= 1;
    expect(!(a == b), "tracked tdata: same tracker, different data compares unequal");
}

int sc_main(int, char **)
{
    checkWithoutTuser();
    checkWithWideTuser();
    checkTrackedTdata();
    printf("checks:%" PRIu64 " failures:%" PRIu64 "\n", checks, failures);
    return failures ? 1 : 0;
}
