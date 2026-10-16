// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "bitTwiddling.h"
#include <algorithm>
#include <bit>
#include <cassert>

// Out-of-line symbol for the header's constexpr implementation, so both
// spellings share one implementation.
uint64_t findNextPowerOf2(uint64_t n)
{
    return findNextPowerOf2Constexpr(n);
}
uint16_t log2ofPowerOf2(uint64_t v)
{
    assert(std::has_single_bit(v));
    return static_cast<uint16_t>(std::countr_zero(v));
}
