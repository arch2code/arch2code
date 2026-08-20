// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "bitTwiddling.h"
#include <algorithm>
#include <bit>
#include <cassert>

// Internal generated-code support: user model code moves typed structures
// through the generated channels, ports, pack()/unpack() and register/memory
// APIs, and should not call these helpers directly.
//
// The masking difference between pack_bits and unpack_bits below is deliberate
// and part of the SystemC/RTL equivalence contract; read
// STRUCTURES_AND_DATA_TYPES_REFERENCE.md before changing it.

// Out-of-line symbol for the header's constexpr implementation. Delegating
// keeps one implementation: an open-coded copy here once drifted, losing the
// `>> 32` step and returning non-powers of two above 2^32.
uint64_t findNextPowerOf2(uint64_t n)
{
    return findNextPowerOf2Constexpr(n);
}
uint16_t log2ofPowerOf2(uint64_t v)
{
    assert(std::has_single_bit(v));
    return static_cast<uint16_t>(std::countr_zero(v));
}
// pack_bits deliberately does NOT mask the source word to `consume` bits. The
// modeling platform tolerates oversized native storage for declared HW-width
// fields (a 70-bit field stored in uint64_t[2], say); when a writer leaves bits
// set above the declared width — uninitialized storage, or a true algorithm
// overflow — those bits flow into the packed form at adjacent fields' positions
// and the generated test_ip_structs roundtrip canary reports the mismatch.
// Masking here would silently sanitize the overflow and hide the algorithm bug,
// so do not add one without first relocating that detection surface.
//
// unpack_bits DOES mask, because when extracting one field out of a packed form
// the source word legitimately carries adjacent fields' bits, which must not
// propagate into the destination field's storage.
//
// Both accumulate by OR, so the caller must pre-clear the destination.
//
// This overload takes arbitrary bit offsets in both source and destination.
void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t srcPos, uint16_t bits)
{
    while (bits > 0) {
        uint16_t left_shift = destPos & 63; // Bit offset within destination word (0-63)
        uint16_t right_shift = srcPos & 63; // Bit offset within source word (0-63)
        uint16_t consume = std::min(bits, (uint16_t)(64-(left_shift))); // How many bits to consume from src without overflowing dest
        consume = std::min(consume, (uint16_t)(64-(right_shift))); // How many bits to consume from src without overflowing src word
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
// pack_bits — source aligned to bit 0 of src, so srcPos is implicitly 0.
void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t bits)
{
    uint16_t srcPos = 0;
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
void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t src, uint16_t bits)
{
    uint16_t srcPos = 0;
    while (bits > 0) {
        uint16_t left_shift = destPos & 63;
        uint16_t right_shift = srcPos & 63;
        uint16_t consume = std::min(bits, (uint16_t)(64-(left_shift)));
        consume = std::min(consume, (uint16_t)(64-(right_shift)));
        if (left_shift > right_shift) {
            dest[ destPos >> 6 ] |= src << (left_shift - right_shift);
        } else {
            dest[ destPos >> 6 ] |= src >> (right_shift - left_shift);
        }
        destPos += consume;
        srcPos += consume;
        bits -= consume;
    }
}

void unpack_bits(uint64_t* dest, uint16_t destPos, const uint64_t* src, uint16_t srcPos, uint16_t bits)
{
    while (bits > 0) {
        uint16_t left_shift  = destPos & 63;
        uint16_t right_shift = srcPos  & 63;
        uint16_t consume = std::min(bits, (uint16_t)(64 - left_shift));
        consume = std::min(consume, (uint16_t)(64 - right_shift));
        uint64_t mask = (consume >= 64) ? ~0ULL : ((1ULL << consume) - 1);
        uint64_t bits_to_write = (src[srcPos >> 6] >> right_shift) & mask;
        dest[destPos >> 6] |= bits_to_write << left_shift;
        destPos += consume;
        srcPos  += consume;
        bits    -= consume;
    }
}
