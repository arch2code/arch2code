
#ifndef XIFVARIANTCONFIG_H_
#define XIFVARIANTCONFIG_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=xif --context=xif.yaml
// GENERATED_CODE_BEGIN --template=config
#include <cstdint>
#include "clog2.h"

struct xifDefaultConfig {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};

struct dutDutV0Config {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};

struct srcSrcV0Config {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};

struct sinkSinkV0Config {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};

// GENERATED_CODE_END

#endif //XIFVARIANTCONFIG_H_
