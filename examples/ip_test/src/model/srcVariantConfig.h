
#ifndef SRCVARIANTCONFIG_H_CONFIG_H
#define SRCVARIANTCONFIG_H_CONFIG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

// GENERATED_CODE_PARAM --project=ip_test --context=../../src/yaml/src.yaml
// GENERATED_CODE_BEGIN --template=config
#include "clog2.h"

struct srcDefaultConfig {
    static constexpr uint32_t OUT0_DATA_WIDTH = 8;
    static constexpr uint32_t OUT1_DATA_WIDTH = 70;
};

struct srcVariantSrc0Config {
    static constexpr uint32_t OUT0_DATA_WIDTH = 8;
    static constexpr uint32_t OUT1_DATA_WIDTH = 70;
};

// GENERATED_CODE_END

#endif //SRCVARIANTCONFIG_H_CONFIG_H
