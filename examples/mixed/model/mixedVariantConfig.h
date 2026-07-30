
#ifndef MIXEDVARIANTCONFIG_H_CONFIG_H
#define MIXEDVARIANTCONFIG_H_CONFIG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

// GENERATED_CODE_PARAM --project=mixed --context=mixed.yaml
// GENERATED_CODE_BEGIN --template=config
#include "clog2.h"

struct mixedDefaultConfig {
    static constexpr uint32_t bob = 16;
    static constexpr uint32_t fred = 0;
};

struct blockFVariant0Config {
    static constexpr uint32_t bob = 16;
    static constexpr uint32_t fred = 0;
};

struct blockFVariant1Config {
    static constexpr uint32_t bob = 15;
    static constexpr uint32_t fred = 1;
};

struct blockGGvariant0Config {
    static constexpr uint32_t bob = 16;
    static constexpr uint32_t fred = 0;
};

// GENERATED_CODE_END

#endif //MIXEDVARIANTCONFIG_H_CONFIG_H
