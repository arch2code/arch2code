// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "bitTwiddling.h"
#include <algorithm>
uint64_t findNextPowerOf2(uint64_t n)
{
    if (n == 0) return 1;
    // decrement `n` (to handle the case when `n` itself is a power of 2)
    n--;

    // set all bits after the last set bit
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;

    // increment `n` and return
    return ++n;
}
// https://graphics.stanford.edu/~seander/bithacks.html#IntegerLogObvious
uint16_t log2ofPowerOf2(uint64_t v)
{
    static const uint64_t b[] = {0xAAAAAAAA, 0xCCCCCCCC, 0xF0F0F0F0, 0xFF00FF00, 0xFFFF0000, 0xFFFFFFFF00000000};
    uint64_t r = (v & b[0]) != 0;
    for (uint64_t i = 5; i > 0; i--) // unroll for speed...
    {
        r |= ((v & b[i]) != 0) << i;
    }
    return r;
}

void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t srcPos, uint16_t bits)
{
    while (bits > 0) {
        uint16_t left_shift = destPos & 63;
        uint16_t right_shift = srcPos & 63;
        uint16_t consume = std::min(bits, (uint16_t)(64-(left_shift)));
        consume = std::min(consume, (uint16_t)(64-(right_shift)));
        if (left_shift > right_shift) {
            dest[ destPos >> 6 ] |= src[srcPos >> 6] << (left_shift - right_shift);
        } else {
            dest[ destPos >> 6 ] |= src[srcPos >> 6] >> (right_shift - left_shift);
        }
        destPos += consume;
        srcPos += consume;
        bits -= consume;
    }
}
void pack_bits(uint64_t* dest, uint16_t pos, uint64_t* src, uint16_t bits)
{
    uint16_t srcPos = 0;
    while (bits > 0) {
        uint16_t left_shift = pos & 63;
        uint16_t right_shift = srcPos & 63;
        uint16_t consume = std::min(bits, (uint16_t)(64-(left_shift)));
        consume = std::min(consume, (uint16_t)(64-(right_shift)));
        if (left_shift > right_shift) {
            dest[ pos >> 6 ] |= src[srcPos >> 6] << (left_shift - right_shift);
        } else {
            dest[ pos >> 6 ] |= src[srcPos >> 6] >> (right_shift - left_shift);
        }
        pos += consume;
        srcPos += consume;
        bits -= consume;
    }
}
void pack_bits(uint64_t* dest, uint16_t pos, uint64_t src, uint16_t bits)
{
    uint16_t srcPos = 0;
    while (bits > 0) {
        uint16_t left_shift = pos & 63;
        uint16_t right_shift = srcPos & 63;
        uint16_t consume = std::min(bits, (uint16_t)(64-(left_shift)));
        consume = std::min(consume, (uint16_t)(64-(right_shift)));
        if (left_shift > right_shift) {
            dest[ pos >> 6 ] |= src << (left_shift - right_shift);
        } else {
            dest[ pos >> 6 ] |= src >> (right_shift - left_shift);
        }
        pos += consume;
        srcPos += consume;
        bits -= consume;
    }
}
