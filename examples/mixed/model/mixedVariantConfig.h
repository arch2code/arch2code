
#ifndef MIXEDVARIANTCONFIG_H_
#define MIXEDVARIANTCONFIG_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=mixed --context=mixed.yaml
// GENERATED_CODE_BEGIN --template=config
#include <cstdint>
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

#endif //MIXEDVARIANTCONFIG_H_
