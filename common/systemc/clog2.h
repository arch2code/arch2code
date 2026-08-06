#ifndef CLOG2_H
#define CLOG2_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <cstdint>
// Constexpr ceiling log2 - matches SystemVerilog $clog2 semantics
// clog2(0) = 0, clog2(1) = 0, clog2(2) = 1, clog2(3) = 2, clog2(4) = 2, clog2(5) = 3, ...
constexpr uint16_t clog2(uint64_t n) {
    if (n <= 1) return 0;
    uint16_t result = 0;
    n--;
    while (n > 0) { n >>= 1; result++; }
    return result;
}
#endif //CLOG2_H
