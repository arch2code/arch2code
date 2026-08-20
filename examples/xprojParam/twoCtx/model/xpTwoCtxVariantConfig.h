
#ifndef XPTWOCTXVARIANTCONFIG_H_
#define XPTWOCTXVARIANTCONFIG_H_
// 

// GENERATED_CODE_PARAM --project=xpTwoCtx --context=../../yaml/xpTwoCtx.yaml
// GENERATED_CODE_BEGIN --template=config
#include <cstdint>
#include "clog2.h"

struct xpTwoCtxDefaultConfig {
    static constexpr uint32_t TC_GAIN = 2;
    static constexpr uint32_t TC_GAIN_X2 = TC_GAIN * 2;
};

struct xpTwoCtxBareTwoctxConfig {
    static constexpr uint32_t TC_GAIN = 5;
    static constexpr uint32_t TC_GAIN_X2 = TC_GAIN * 2;
    static constexpr uint32_t DP_WIDTH = 12;
};

struct xpTwoCtxSnkTwoctxConfig {
    static constexpr uint32_t TC_GAIN = 5;
    static constexpr uint32_t TC_GAIN_X2 = TC_GAIN * 2;
};

// GENERATED_CODE_END

#endif //XPTWOCTXVARIANTCONFIG_H_
