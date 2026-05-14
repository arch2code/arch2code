// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "bitTwiddling.h"
#include <algorithm>

// Internal generated-code support only.
//
// User model code should not call pack_bits(), unpack_bits(), or
// copy_packed_bits() directly. These helpers implement the generated
// structure/thunker representation contract; user code should move typed
// structures through the generated channels, ports, pack()/unpack() methods,
// and register/memory APIs instead.
//
// Agent/maintainer warning: if you are about to modify this file, first read
// STRUCTURES_AND_DATA_TYPES_REFERENCE.md. The masking differences
// below are deliberate and are part of the SystemC/RTL equivalence contract.
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
// pack_bits / unpack_bits implementation notes (shared across the overloads).
//
// pack_bits intentionally does NOT mask the source word to `consume` bits per
// iteration. The modeling platform tolerates oversized native C storage for
// declared HW-width fields (e.g. an 8-bit field stored in a uint8_t, a 70-bit
// field stored in uint64_t[2]); when a writer leaves bits set above the
// declared width — uninitialized storage, or a true algorithm overflow —
// those bits flow through pack() into the packed form at adjacent fields'
// positions, and the generated test_ip_structs roundtrip canary surfaces
// the mismatch noisily. That noise is the canonical fail-fast surface;
// adding a source mask here would silently sanitize the overflow and hide
// the underlying algorithm bug. Do not change that behavior without first
// relocating the detection surface elsewhere (e.g. a per-field range assert
// at the call site of the offending writer).
//
// unpack_bits DOES mask the source word to `consume` bits per iteration.
// When extracting one field out of a packed form, the source word
// legitimately carries adjacent fields' bits beyond the field being
// extracted; those bits must not propagate into the destination field's
// storage. Stage 8.2 of plan-variant-config-unification.md added the
// helper, and templates/systemc/structures.py routes the templated
// array-backed unpack codegen through it.
//
// Both functions require the caller to pre-clear the destination. pack()
// emits memset(&_ret, 0, _byteWidth) at the top; the templated unpack()
// emits memset(&field, 0, sizeof(field)) before each unpack_bits call.
//
// This overload (dest, destPos, src, srcPos, bits) supports arbitrary bit
// offsets within both source and destination.
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
// pack_bits — overload where the source pointer is known to be aligned to a
// 64-bit word boundary at bit 0 (srcPos is implicitly 0). See the
// implementation-notes block above the first overload for the shared
// overflow-propagation rationale.
void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t bits)
{
    uint16_t srcPos = 0; // note starts at 0 ie aligned to the start of src
    while (bits > 0) {
        uint16_t left_shift = destPos & 63; // Bit offset within destination word (0-63)        
        uint16_t right_shift = srcPos & 63; // Bit offset within source word (0-63)
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
// pack_bits — overload where the source is a single 64-bit value passed by
// value rather than by pointer. See the implementation-notes block above
// the first overload for the shared overflow-propagation rationale.
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

// unpack_bits — see the implementation-notes block above the first pack_bits
// overload for the shared rationale: pack_bits propagates source bits above
// `consume` so overflow surfaces noisily through the test_ip_structs canary,
// while unpack_bits masks them so adjacent packed-form fields' bits do not
// leak into the destination field's storage.
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
