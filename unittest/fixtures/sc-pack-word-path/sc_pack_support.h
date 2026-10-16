// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Struct-independent helpers for the sc_pack()/sc_unpack() harness. The oracle
// writes each field with its own range() assignment at the position the
// generator documents (first YAML field at the MSB, array element i above
// element i-1), so it is independent of pack().

#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <type_traits>

static uint64_t checks = 0;
static uint64_t failures = 0;

static void check(bool ok, const char *flavour, const char *what, const char *name)
{
    checks++;
    if (!ok) {
        failures++;
        printf("FAIL %s %s: %s\n", flavour, name, what);
    }
}

// Stands in for the simulator's q_assert_body: a Q_ASSERT the harness does not
// expect counts as a failure, and execution continues either way.
static bool assertExpected = false;
static uint64_t assertsSeen = 0;

void q_assert_body(bool, const char *file, int line, std::string ctx, std::string msg, std::string)
{
    assertsSeen++;
    if (!assertExpected) {
        failures++;
        printf("FAIL unexpected Q_ASSERT [%s] %s (%s:%d)\n", ctx.c_str(), msg.c_str(), file, line);
    }
}

template <typename F>
static void expectAssert(const char *flavour, const char *what, const char *name, F &&body)
{
    uint64_t before = assertsSeen;
    assertExpected = true;
    body();
    assertExpected = false;
    check(assertsSeen == before + 1, flavour, what, name);
}

static uint64_t rngState = 0x9e3779b97f4a7c15ULL;

static uint64_t rnd64()
{
    rngState ^= rngState << 13;
    rngState ^= rngState >> 7;
    rngState ^= rngState << 17;
    return rngState;
}

// An in-range unsigned value of w bits, w <= 64.
static uint64_t rnd(unsigned w)
{
    return w >= 64 ? rnd64() : rnd64() & ((1ULL << w) - 1);
}

// An in-range signed value of w bits, sign-extended to 64, w <= 64.
static int64_t srnd(unsigned w)
{
    uint64_t v = rnd(w);
    if (w < 64 && (v >> (w - 1)) & 1) {
        v |= ~((1ULL << w) - 1);
    }
    return (int64_t)v;
}

// An in-range value for a w-bit field held as uint64_t word[].
template <typename T>
static void rndWide(T &t, unsigned w)
{
    for (unsigned i = 0; i < sizeof(t.word) / sizeof(t.word[0]); i++) {
        unsigned bits = w > i * 64 ? std::min(64u, w - i * 64) : 0;
        t.word[i] = bits ? rnd(bits) : 0;
    }
}

static void put(sc_bv_base &bv, unsigned lo, unsigned w, uint64_t v)
{
    if (w < 64) {
        v &= (1ULL << w) - 1;
    }
    bv.range(lo + w - 1, lo) = v;
}

template <typename T>
static void putWide(sc_bv_base &bv, unsigned lo, unsigned w, const T &t)
{
    for (unsigned i = 0; i * 64 < w; i++) {
        put(bv, lo + i * 64, std::min(64u, w - i * 64), t.word[i]);
    }
}

template <typename P>
static uint64_t packedWord(const P &p, unsigned i)
{
    if constexpr (std::is_array_v<P>) {
        return p[i];
    } else {
        return i == 0 ? (uint64_t)p : 0;
    }
}

// The word count reaches packWords/unpackWords through a volatile, so the
// optimizer compiles their loops for an unknown count, as it does for a
// caller's own word loop.
static volatile int wordCountSink;

static int runtimeWords(int n)
{
    wordCountSink = n;
    return wordCountSink;
}

// pack() and a 32-bit word read of its result, in one out-of-line function.
template <typename T>
__attribute__((noinline)) static void packWords(const T &x, uint32_t *out, int n)
{
    typename T::_packedSt p;
    x.pack(p);
    for (int i = 0; i < n; i++) {
        out[i] = (uint32_t)(packedWord(p, i >> 1) >> ((i & 1) * 32));
    }
}

// 32-bit word stores at a variable index, then unpack(), in one out-of-line
// function.
template <typename T>
__attribute__((noinline)) static void unpackWords(T &x, const uint32_t *in, int n)
{
    using P = typename T::_packedSt;
    P p{};
    for (int i = 0; i < n; i++) {
        if constexpr (std::is_array_v<P>) {
            p[i >> 1] |= (uint64_t)in[i] << ((i & 1) * 32);
        } else {
            p |= (P)((uint64_t)in[i] << (i * 32));
        }
    }
    x.unpack(p);
}

static const unsigned ITERATIONS = 16;
