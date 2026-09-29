#ifndef BITTWIDDLING_H
#define BITTWIDDLING_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <bit>
#include <cassert>
#include <cstdint>
#include <type_traits>
#include "clog2.h"
// https://www.techiedelight.com/round-next-highest-power-2/
// Least power of two >= `n`. Domain is n <= 2^63; 2^64 is not representable, so
// a larger input asserts rather than wrapping to 0. In a constant expression
// that assert is a compile error.
constexpr uint64_t findNextPowerOf2Constexpr(uint64_t n) {
    assert(n <= (1ULL << 63));
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
// Runtime form of findNextPowerOf2Constexpr above; same contract and domain.
extern uint64_t findNextPowerOf2(uint64_t n);
// Index of the single set bit; asserts unless `n` is a power of two.
extern uint16_t log2ofPowerOf2(uint64_t n);
// pack_bits — OR `bits` bits from src@srcPos into dest@destPos. Caller must
// pre-clear the destination. Source words are NOT masked, so any bits set above
// the width being consumed OR into the destination alongside it.
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t srcPos, uint16_t bits); // by ptr any alignment
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t bits); // by ptr aligned to start of src
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t src, uint16_t bits); // by value

// unpack_bits — the reverse; caller must pre-clear the destination. Each source
// word IS masked to the width being consumed, so adjacent fields in a packed
// form are dropped rather than propagated into the destination.
extern void unpack_bits(uint64_t* dest, uint16_t destPos, const uint64_t* src, uint16_t srcPos, uint16_t bits);

template <typename OutPacked, typename InPacked>
inline void copy_packed_bits(OutPacked& out, const InPacked& in, uint16_t bits)
{
    using Out = std::remove_reference_t<OutPacked>;
    using In = std::remove_reference_t<InPacked>;

    if constexpr (!std::is_array_v<Out> && !std::is_array_v<In>) {
        out = static_cast<Out>(in);
    } else if constexpr (std::is_array_v<Out>) {
        for (auto& word : out) {
            word = 0;
        }
        if constexpr (std::is_array_v<In>) {
            uint64_t* src = const_cast<uint64_t*>(reinterpret_cast<const uint64_t*>(&in));
            pack_bits(reinterpret_cast<uint64_t*>(&out), 0, src, 0, bits);
        } else {
            uint64_t src = static_cast<uint64_t>(in);
            pack_bits(reinterpret_cast<uint64_t*>(&out), 0, src, bits);
        }
    } else {
        uint64_t tmp = 0;
        uint64_t* src = const_cast<uint64_t*>(reinterpret_cast<const uint64_t*>(&in));
        pack_bits(&tmp, 0, src, 0, bits);
        out = static_cast<Out>(tmp);
    }
}

// copyPayload — transfer a payload onto the differently-declared payload on the
// other side of a cross-interface adapter. `Direct` is the generator's verdict
// that the two declarations emit identical member storage; C++ cannot decide
// that itself, as the two sides are unrelated class types, so the adapter's
// class template carries one flag per payload pair. The verdict covers the
// payload alone, not the protocol envelope around it: sideband members sized
// from the payload's declared width (axi4_stream's tstrb/tkeep) are not
// compared.
//
// std::bit_cast does not check the verdict — equal-sized types with different
// member layout satisfy it, so a wrong verdict compiles and silently
// reinterprets one layout as the other. The sizeof static_assert at each call
// site only catches a wrong verdict that also changes size.
//
// The arms diverge on a field holding a value wider than it declares: the packed
// arm masks each field to its declared _bitWidth on unpack, while the assign and
// bit_cast arms transfer the storage as it stands.
template <bool Direct, typename To, typename From>
inline void copyPayload(To& out, const From& in)
{
    if constexpr (std::is_same_v<To, From>) {
        out = in;
    } else if constexpr (Direct) {
        out = std::bit_cast<To>(in);
    } else {
        typename From::_packedSt inPacked;
        typename To::_packedSt outPacked;
        in.pack( inPacked );
        copy_packed_bits( outPacked, inPacked, To::_bitWidth );
        out.unpack( outPacked );
    }
}
#endif //BITTWIDDLING_H
