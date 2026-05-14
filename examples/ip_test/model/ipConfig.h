
#ifndef IPCONFIG_H_CONFIG_H
#define IPCONFIG_H_CONFIG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

// GENERATED_CODE_PARAM --context=ip.yaml
// GENERATED_CODE_BEGIN --template=includes --section=config
struct ipDefaultConfig {
    static constexpr uint32_t IP_DATA_WIDTH = 70;
    static constexpr uint32_t IP_MEM_DEPTH = 16;
    static constexpr uint32_t IP_DATA_WIDTH_X2 = 140;
};

struct ipVariant0Config {
    static constexpr uint32_t IP_DATA_WIDTH = 8;
    static constexpr uint32_t IP_MEM_DEPTH = 16;
    static constexpr uint32_t IP_DATA_WIDTH_X2 = 140;
    static constexpr uint32_t IP_NONCONST_DEPTH = 24;
};

struct ipVariant1Config {
    static constexpr uint32_t IP_DATA_WIDTH = 70;
    static constexpr uint32_t IP_MEM_DEPTH = 8;
    static constexpr uint32_t IP_DATA_WIDTH_X2 = 140;
    static constexpr uint32_t IP_NONCONST_DEPTH = 12;
};

// GENERATED_CODE_END

#endif //IPCONFIG_H_CONFIG_H
