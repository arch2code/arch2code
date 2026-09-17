//

// GENERATED_CODE_PARAM --block=vliLeaf --parent=vliCont/../../yaml/vliCont.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module vlInh.vliLeaf.config;

export struct vlInh_vliLeafDefaultConfig {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 8;
};

export struct vlInh_vliLeafSoloConfig {
    static constexpr uint32_t VLI_ALGO = 3;
    static constexpr uint32_t VLI_WIDTH = 8;
};

export template<typename ContainerConfig>
struct vlInh_vliLeafSourcedConfig {
    static constexpr uint32_t VLI_ALGO = ContainerConfig::VLI_ALGO;
    static constexpr uint32_t VLI_WIDTH = ContainerConfig::VLI_WIDTH;
};

// GENERATED_CODE_END
