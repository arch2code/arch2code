//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --parent=uvmReuseLeaf_tb/../../yaml/uvmReuseLeaf_tb.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module uvmReuseLeaf.config;

export struct uvmReuseLeafDefaultConfig {
    static constexpr uint32_t UVM_REUSE_OFF_W = 4;
};

export struct uvmReuseLeafW4Config {
    static constexpr uint32_t UVM_REUSE_OFF_W = 4;
};

export struct uvmReuseLeafW8Config {
    static constexpr uint32_t UVM_REUSE_OFF_W = 8;
};

// GENERATED_CODE_END
