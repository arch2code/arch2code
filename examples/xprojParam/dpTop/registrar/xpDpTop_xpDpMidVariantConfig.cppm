//

// GENERATED_CODE_PARAM --block=xpDpMid --parent=xpDpWrap
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xpDpTop.xpDpMid.config;

export template<typename ContainerConfig>
struct xpDpTop_xpDpMidCustomerConfig {
    static constexpr uint32_t DP_WIDTH = 8;
    static constexpr uint32_t MID_ALGO = ContainerConfig::CUST_ALGO;
};

export struct xpDpTop_xpDpMidCustomer2Config {
    static constexpr uint32_t DP_WIDTH = 8;
    static constexpr uint32_t MID_ALGO = 6;
};

export struct xpDpTop_xpDpMidCustomer3Config {
    static constexpr uint32_t DP_WIDTH = 8;
    static constexpr uint32_t MID_ALGO = 7;
};

// GENERATED_CODE_END
