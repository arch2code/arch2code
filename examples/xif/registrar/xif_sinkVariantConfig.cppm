//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=sink --parent=xif_tb/xif.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xif.sink.config;

export struct xif_sinkDefaultConfig {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};

export struct xif_sinkSinkV0Config {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};

// GENERATED_CODE_END
