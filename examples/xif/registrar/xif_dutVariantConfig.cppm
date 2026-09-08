//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dut --parent=xif_tb/xif.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xif.dut.config;

export struct xif_dutDefaultConfig {
    static constexpr uint32_t DATA_WIDTH = 16;
};

export struct xif_dutDutV0Config {
    static constexpr uint32_t DATA_WIDTH = 16;
};

// GENERATED_CODE_END
