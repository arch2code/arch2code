#ifndef BITTWIDDLING_H
#define BITTWIDDLING_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <cstdint>
// https://www.techiedelight.com/round-next-highest-power-2/
// Compute power of two greater than or equal to `n`
constexpr uint64_t findNextPowerOf2Constexpr(uint64_t n) {
    if (n == 0) return 1;
    n--;
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    n |= n >> 32;
    return n + 1;
}
// Constexpr ceiling log2 - matches SystemVerilog $clog2 semantics
// clog2(0) = 0, clog2(1) = 0, clog2(2) = 1, clog2(3) = 2, clog2(4) = 2, clog2(5) = 3, ...
constexpr uint16_t clog2(uint64_t n) {
    if (n <= 1) return 0;
    uint16_t result = 0;
    n--;
    while (n > 0) { n >>= 1; result++; }
    return result;
}
extern uint64_t findNextPowerOf2(uint64_t n);
extern uint16_t log2ofPowerOf2(uint64_t n);
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t srcPos, uint16_t bits); // by ptr any alignment
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t bits); // by ptr aligned to start of src
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t src, uint16_t bits); // by value
#endif //BITTWIDDLING_H
