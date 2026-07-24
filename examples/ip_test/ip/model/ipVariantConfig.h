
#ifndef IPVARIANTCONFIG_H_CONFIG_H
#define IPVARIANTCONFIG_H_CONFIG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

// GENERATED_CODE_PARAM --context=../../ip/yaml/ip.yaml
// GENERATED_CODE_BEGIN --template=config
#include "clog2.h"

struct ipDefaultConfig {
    static constexpr uint32_t IP_DATA_WIDTH = 70;
    static constexpr uint32_t IP_MEM_DEPTH = 16;
    static constexpr uint32_t IP_NONCONST_DEPTH = 24;
    static constexpr uint32_t IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;
    static constexpr uint32_t IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;
    static constexpr uint32_t IP_MEM_DEPTH_X2 = IP_MEM_DEPTH * 2;
    static constexpr uint32_t IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2;
};

struct ipVariant0Config {
    static constexpr uint32_t IP_DATA_WIDTH = 8;
    static constexpr uint32_t IP_MEM_DEPTH = 16;
    static constexpr uint32_t IP_NONCONST_DEPTH = 24;
    static constexpr uint32_t IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;
    static constexpr uint32_t IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;
    static constexpr uint32_t IP_MEM_DEPTH_X2 = IP_MEM_DEPTH * 2;
    static constexpr uint32_t IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2;
};

// GENERATED_CODE_END

#endif //IPVARIANTCONFIG_H_CONFIG_H
