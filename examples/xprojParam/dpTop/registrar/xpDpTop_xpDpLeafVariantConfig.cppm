//

// GENERATED_CODE_PARAM --block=xpDpLeaf --parent=xpDpWrap
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xpDpTop.xpDpLeaf.config;

export template<typename ContainerConfig>
struct xpDpTop_xpDpLeafLeafXConfig {
    static constexpr uint32_t DP_ALGO = ContainerConfig::CUST_ALGO;
    static constexpr uint32_t DP_WIDTH = 8;
};

// GENERATED_CODE_END
