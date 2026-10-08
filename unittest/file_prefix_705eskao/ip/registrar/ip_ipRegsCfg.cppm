//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipRegs --parent=ip/../../yaml/ip.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module ip.ipRegs.config;

export struct ip_ipRegsDefaultConfig {
    static constexpr uint32_t IP_DATA_WIDTH = 70;
    static constexpr uint32_t IP_MEM_DEPTH = 16;
    static constexpr uint32_t IP_NONCONST_DEPTH = 24;
};

// GENERATED_CODE_END
