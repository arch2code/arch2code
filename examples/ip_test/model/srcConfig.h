
#ifndef SRCCONFIG_H_CONFIG_H
#define SRCCONFIG_H_CONFIG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

// GENERATED_CODE_PARAM --context=src.yaml
// GENERATED_CODE_BEGIN --template=includes --section=config
struct srcDefaultConfig {
    static constexpr uint32_t OUT0_DATA_WIDTH = 8;
    static constexpr uint32_t OUT1_DATA_WIDTH = 12;
};

struct srcVariantSrc0Config {
    static constexpr uint32_t OUT0_DATA_WIDTH = 8;
    static constexpr uint32_t OUT1_DATA_WIDTH = 12;
};

// GENERATED_CODE_END

#endif //SRCCONFIG_H_CONFIG_H
