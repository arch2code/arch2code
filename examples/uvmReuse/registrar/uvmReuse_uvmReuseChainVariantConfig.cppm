//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain --parent=uvmReuse_tb/../../yaml/uvmReuse.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module uvmReuse.uvmReuseChain.config;

export struct uvmReuse_uvmReuseChainDefaultConfig {
    static constexpr uint32_t UVM_REUSE_B_W = 8;
};

export struct uvmReuse_uvmReuseChainV4Config {
    static constexpr uint32_t UVM_REUSE_B_W = 4;
};

export struct uvmReuse_uvmReuseChainV8Config {
    static constexpr uint32_t UVM_REUSE_B_W = 8;
};

// GENERATED_CODE_END
