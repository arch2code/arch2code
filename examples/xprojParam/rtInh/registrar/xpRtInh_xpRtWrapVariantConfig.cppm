//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtWrap --parent=xpRtInhTop/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xpRtInh.xpRtWrap.config;

export struct xpRtInh_xpRtWrapDefaultConfig {
    static constexpr uint32_t RT_WIDTH = 8;
};

export struct xpRtInh_xpRtWrapUseConfig {
    static constexpr uint32_t RT_WIDTH = 32;
};

// GENERATED_CODE_END
