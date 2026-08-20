// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Contract harness for the power-of-two helpers in common/systemc/bitTwiddling.
// Every result is judged against an independent oracle rather than a second
// copy of the algorithm, because re-deriving the expected answer the same way
// passes for any width and proves nothing. findNextPowerOf2 is judged by the
// defining properties of its result: a power of two, at or above the input, and
// the least such. log2ofPowerOf2 is judged against an exponent the harness
// already holds, by building each input from it.
//
// The runtime-versus-constexpr comparison is the one exception: it is a tripwire,
// not an oracle. It holds trivially while the .cpp delegates to the header, and
// fails if that body is ever open-coded again.
//
// Run with no argument to check the contract. The abort-* arguments each drive
// one input the contract excludes, so the caller can confirm it aborts.

#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <set>

#include "bitTwiddling.h"

static uint64_t checks = 0;
static uint64_t failures = 0;

static void expect(bool ok, const char *what, uint64_t n, uint64_t got)
{
    checks++;
    if (!ok) {
        failures++;
        printf("FAIL %s: n=%" PRIu64 " got=%" PRIu64 "\n", what, n, got);
    }
}

// 2^64 is not representable, so 2^63 is the largest input with a defined answer.
static constexpr uint64_t domainMax = 1ULL << 63;

static bool isPowerOfTwo(uint64_t v)
{
    return v != 0 && (v & (v - 1)) == 0;
}

static std::set<uint64_t> buildInputs()
{
    std::set<uint64_t> inputs;
    // Dense low range: every carry position below 2^10.
    for (uint64_t n = 0; n <= 1024; n++) {
        inputs.insert(n);
    }
    // Every binade edge. The +1 entries are the ones that bite; see the note in
    // the suite docstring.
    for (unsigned k = 0; k < 64; k++) {
        uint64_t p = 1ULL << k;
        inputs.insert(p - 1);
        inputs.insert(p);
        if (p <= domainMax - 1) {
            inputs.insert(p + 1);
        }
    }
    // Wide values whose low bits do not fill the smear gap on their own.
    inputs.insert(0x0000000123456789ULL);
    inputs.insert((1ULL << 52) + 12345);
    inputs.insert((1ULL << 40) + (1ULL << 3));

    return inputs;
}

// Compile-time pins for the constexpr twin, independent of the runtime symbol.
static_assert(findNextPowerOf2Constexpr(0) == 1);
static_assert(findNextPowerOf2Constexpr(1) == 1);
static_assert(findNextPowerOf2Constexpr(2) == 2);
static_assert(findNextPowerOf2Constexpr(3) == 4);
static_assert(findNextPowerOf2Constexpr(5) == 8);
static_assert(findNextPowerOf2Constexpr(0xFFFFFFFFULL) == 0x100000000ULL);
static_assert(findNextPowerOf2Constexpr(0x100000000ULL) == 0x100000000ULL);
static_assert(findNextPowerOf2Constexpr(0x100000001ULL) == 0x200000000ULL);
static_assert(findNextPowerOf2Constexpr(1ULL << 40) == 1ULL << 40);
static_assert(findNextPowerOf2Constexpr((1ULL << 40) + 1) == 1ULL << 41);
static_assert(findNextPowerOf2Constexpr((1ULL << 62) + 1) == 1ULL << 63);
static_assert(findNextPowerOf2Constexpr(1ULL << 63) == 1ULL << 63);

static void checkFindNextPowerOf2(const std::set<uint64_t> &inputs)
{
    for (uint64_t n : inputs) {
        uint64_t r = findNextPowerOf2(n);
        expect(r == findNextPowerOf2Constexpr(n), "runtime disagrees with constexpr", n, r);
        expect(isPowerOfTwo(r), "result is not a power of two", n, r);
        expect(r >= n, "result is below the input", n, r);
        // r==1 is the floor of the domain: nothing smaller is a power of two.
        expect(r == 1 || (r >> 1) < n, "result is not the least power of two", n, r);
    }
}

static void checkLog2OfPowerOf2(const std::set<uint64_t> &inputs)
{
    // Each input is built from k, so the expected answer is known independently
    // of anything the implementation computes.
    for (unsigned k = 0; k < 64; k++) {
        uint64_t v = 1ULL << k;
        expect(log2ofPowerOf2(v) == k, "exponent of a power of two is wrong", v, log2ofPowerOf2(v));
    }
    // The 32-bit boundary, named explicitly so it survives any future trim of
    // the sweep above. Redundant while that sweep is whole.
    const unsigned boundary[] = {31, 32, 33, 34};
    for (unsigned k : boundary) {
        uint64_t v = 1ULL << k;
        expect(log2ofPowerOf2(v) == k, "exponent is wrong at the 32-bit boundary", v, log2ofPowerOf2(v));
    }
    // Round trip over the shared input set: findNextPowerOf2 yields a power of
    // two, so raising two to its exponent must return it unchanged.
    for (uint64_t n : inputs) {
        uint64_t p = findNextPowerOf2(n);
        // Passing a non-power would violate log2ofPowerOf2's precondition and
        // abort the run; the group above already reports that case.
        if (!isPowerOfTwo(p)) {
            continue;
        }
        uint16_t e = log2ofPowerOf2(p);
        expect(e < 64 && (1ULL << e) == p, "exponent does not invert findNextPowerOf2", n, e);
    }
}

// Each of these is excluded by a precondition assert. Returning normally means
// the assert did not fire, so the caller fails the case on a clean exit.
static int driveExcludedInput(const char *which)
{
    if (strcmp(which, "abort-domain") == 0) {
        // 2^63 + 1 would need 2^64, which uint64_t cannot hold.
        printf("returned:%" PRIu64 "\n", findNextPowerOf2(domainMax + 1));
    } else if (strcmp(which, "abort-log2-zero") == 0) {
        printf("returned:%u\n", log2ofPowerOf2(0));
    } else if (strcmp(which, "abort-log2-nonpower") == 0) {
        printf("returned:%u\n", log2ofPowerOf2(3));
    } else {
        printf("unknown argument %s\n", which);
        return 2;
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc > 1) {
        return driveExcludedInput(argv[1]);
    }
    const std::set<uint64_t> inputs = buildInputs();
    checkFindNextPowerOf2(inputs);
    checkLog2OfPowerOf2(inputs);
    printf("inputs:%zu\n", inputs.size());
    printf("checks:%" PRIu64 " failures:%" PRIu64 "\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
