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
    return n + 1;
}
extern uint64_t findNextPowerOf2(uint64_t n);
extern uint16_t log2ofPowerOf2(uint64_t n);
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t srcPos, uint16_t bits); // by ptr any alignment
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t bits); // by ptr aligned to start of src
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t src, uint16_t bits); // by value
#endif //BITTWIDDLING_H
