#ifndef AXI4S_DEMO_UTILS_H
#define AXI4S_DEMO_UTILS_H

#include "axi4sDemo_tbIncludes.h"

inline bv16_t calc_parity_t1(bv256_t data) {
    bv16_t parity = 0;
    uint16_t* data_ptr = reinterpret_cast<uint16_t*>(&data.word[0]);
    uint8_t p = 0;
    for (int i = 0; i < 16; i++) {
        p = __builtin_parity(data_ptr[i]);
        parity |= (p << (i % 16));

    }
    return parity;
}

inline bool check_parity_t1(bv256_t data, bv16_t parity) {
    return calc_parity_t1(data) == parity;
}

inline bv4_t calc_parity_t2(bv64_t data) {
    bv4_t parity = 0;
    uint16_t* data_ptr = reinterpret_cast<uint16_t*>(&data);
    uint8_t p = 0;
    for (int i = 0; i < 4; i++) {
        p = __builtin_parity(data_ptr[i]);
        parity |= (p << (i % 4));
    }
    return parity;
}

inline bool check_parity_t2(bv64_t data, bv4_t parity) {
    return calc_parity_t2(data) == parity;
}

#endif // AXI4S_DEMO_UTILS_H