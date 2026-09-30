//

// GENERATED_CODE_PARAM --block=xpDpChk --parent=xpDpWrap
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xpDpTop.xpDpChk.config;

export struct xpDpTop_xpDpChkDefaultConfig {
    static constexpr uint32_t DP_ALGO = 1;
    static constexpr uint32_t DP_WIDTH = 8;
};

export struct xpDpTop_xpDpChkCustomerConfig {
    static constexpr uint32_t DP_ALGO = 5;
    static constexpr uint32_t DP_WIDTH = 8;
};

export struct xpDpTop_xpDpChkCustomer2Config {
    static constexpr uint32_t DP_ALGO = 6;
    static constexpr uint32_t DP_WIDTH = 8;
};

export struct xpDpTop_xpDpChkCustomer3Config {
    static constexpr uint32_t DP_ALGO = 7;
    static constexpr uint32_t DP_WIDTH = 8;
};

export struct xpDpTop_xpDpChkLeafXConfig {
    static constexpr uint32_t DP_ALGO = 5;
    static constexpr uint32_t DP_WIDTH = 8;
};

// GENERATED_CODE_END
