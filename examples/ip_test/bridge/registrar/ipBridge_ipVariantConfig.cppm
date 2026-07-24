//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --parent=ipBridge
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module ipBridge.ip.config;

export struct ipBridge_ipVariant1Config {
    static constexpr uint32_t IP_DATA_WIDTH = 70;
    static constexpr uint32_t IP_MEM_DEPTH = 8;
    static constexpr uint32_t IP_NONCONST_DEPTH = 12;
    static constexpr uint32_t IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;
    static constexpr uint32_t IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;
    static constexpr uint32_t IP_MEM_DEPTH_X2 = IP_MEM_DEPTH * 2;
    static constexpr uint32_t IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2;
};

// GENERATED_CODE_END
