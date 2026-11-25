//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --parent=uvmReuseChain/../../yaml/uvmReuse.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module uvmReuse.uvmReuseLeaf.config;

export template<typename ContainerConfig>
struct uvmReuse_uvmReuseLeafFromChainConfig {
    static constexpr uint32_t UVM_REUSE_OFF_W = ContainerConfig::UVM_REUSE_B_W;
};

// GENERATED_CODE_END
