//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --parent=ipStdTop/../../yaml/ipTop.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module ip.ip.config;

export struct ip_ipDefaultConfig {
    static constexpr uint32_t IP_DATA_WIDTH = 70;
    static constexpr uint32_t IP_MEM_DEPTH = 16;
    static constexpr uint32_t IP_NONCONST_DEPTH = 24;
};

export struct ip_ipVariant0Config {
    static constexpr uint32_t IP_DATA_WIDTH = 8;
    static constexpr uint32_t IP_MEM_DEPTH = 16;
    static constexpr uint32_t IP_NONCONST_DEPTH = 24;
};

// GENERATED_CODE_END
