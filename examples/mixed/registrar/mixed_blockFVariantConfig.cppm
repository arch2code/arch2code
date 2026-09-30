//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF --parent=blockB/mixed.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module mixed.blockF.config;

export struct mixed_blockFDefaultConfig {
    static constexpr uint32_t bob = 16;
    static constexpr uint32_t fred = 0;
};

export struct mixed_blockFVariant0Config {
    static constexpr uint32_t bob = 16;
    static constexpr uint32_t fred = 0;
};

export struct mixed_blockFVariant1Config {
    static constexpr uint32_t bob = 15;
    static constexpr uint32_t fred = 1;
};

// GENERATED_CODE_END
