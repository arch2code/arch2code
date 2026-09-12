//

// GENERATED_CODE_PARAM --block=xpCpLeaf --parent=xpCpWrap/../../yaml/xpCpLayoutTop.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xpCpLayout.xpCpLeaf.config;

export struct xpCpLayout_xpCpLeafDefaultConfig {
    static constexpr uint32_t CP_WIDTH = 8;
};

export template<typename ContainerConfig>
struct xpCpLayout_xpCpLeafUseConfig {
    static constexpr uint32_t CP_WIDTH = ContainerConfig::CP_BUS_W;
};

// GENERATED_CODE_END
