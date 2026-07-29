
#ifndef XIFVARIANTCONFIG_H_CONFIG_H
#define XIFVARIANTCONFIG_H_CONFIG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

// GENERATED_CODE_PARAM --project=xif --context=xif.yaml
// GENERATED_CODE_BEGIN --template=config
#include "clog2.h"

struct xifDefaultConfig {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};

// GENERATED_CODE_END

#endif //XIFVARIANTCONFIG_H_CONFIG_H
