//

// GENERATED_CODE_PARAM --block=xpDpLeaf --parent=xpDpMid
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xpDpMid.xpDpLeaf.config;

export template<typename ContainerConfig>
struct xpDpMid_xpDpLeafCustomerConfig {
    static constexpr uint32_t DP_ALGO = ContainerConfig::MID_ALGO;
    static constexpr uint32_t DP_WIDTH = ContainerConfig::DP_WIDTH;
};

// GENERATED_CODE_END
