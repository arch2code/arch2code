
#ifndef MIXEDCONFIG_H_CONFIG_H
#define MIXEDCONFIG_H_CONFIG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

// GENERATED_CODE_PARAM --context=mixed.yaml
// GENERATED_CODE_BEGIN --template=includes --section=config
struct mixedDefaultConfig {
};

struct blockFVariant0Config {
    static constexpr uint32_t bob = 16;
    static constexpr uint32_t fred = 0;
};

struct blockFVariant1Config {
    static constexpr uint32_t bob = 15;
    static constexpr uint32_t fred = 1;
};

// GENERATED_CODE_END

#endif //MIXEDCONFIG_H_CONFIG_H
