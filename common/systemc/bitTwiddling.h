#ifndef BITTWIDDLING_H
#define BITTWIDDLING_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <cstdint>
#include <type_traits>
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
// pack_bits — append `bits` bits from src@srcPos to dest@destPos via
// bitwise OR. Caller must pre-clear the destination. Source words are NOT
// masked: any bits set above `consume` in a source word OR into the
// destination at the matching position. For the unpack direction, where
// source bits above `consume` must be discarded, use unpack_bits.
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t srcPos, uint16_t bits); // by ptr any alignment
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t* src, uint16_t bits); // by ptr aligned to start of src
extern void pack_bits(uint64_t* dest, uint16_t destPos, uint64_t src, uint16_t bits); // by value

// unpack_bits — extract `bits` bits from src@srcPos to dest@destPos via
// bitwise OR. Caller must pre-clear the destination. Each iteration's
// source word is masked to exactly `consume` bits before OR-ing, so bits
// above `consume` (adjacent fields in a packed form) are dropped. For the
// pack direction, where bits above `consume` must propagate, use pack_bits.
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
#endif //BITTWIDDLING_H
