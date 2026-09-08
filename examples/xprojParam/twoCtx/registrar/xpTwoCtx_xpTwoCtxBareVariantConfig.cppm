//

// GENERATED_CODE_PARAM --block=xpTwoCtxBare --parent=xpTwoCtxWrap/../../yaml/xpTwoCtx.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xpTwoCtx.xpTwoCtxBare.config;

export struct xpTwoCtx_xpTwoCtxBareDefaultConfig {
    static constexpr uint32_t TC_GAIN = 2;
    static constexpr uint32_t DP_WIDTH = 8;
};

export struct xpTwoCtx_xpTwoCtxBareTwoctxConfig {
    static constexpr uint32_t TC_GAIN = 5;
    static constexpr uint32_t DP_WIDTH = 12;
};

// GENERATED_CODE_END
