//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --parent=ip_top/../../top/yaml/ip_top.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module ip_test.src.config;

export struct ip_test_srcDefaultConfig {
    static constexpr uint32_t OUT0_DATA_WIDTH = 8;
    static constexpr uint32_t OUT1_DATA_WIDTH = 70;
};

export struct ip_test_srcVariantSrc0Config {
    static constexpr uint32_t OUT0_DATA_WIDTH = 8;
    static constexpr uint32_t OUT1_DATA_WIDTH = 70;
};

// GENERATED_CODE_END
