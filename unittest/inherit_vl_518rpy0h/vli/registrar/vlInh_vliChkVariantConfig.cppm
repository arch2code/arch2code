//

// GENERATED_CODE_PARAM --block=vliChk --parent=vliWrap/../../yaml/vliCont.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module vlInh.vliChk.config;

export struct vlInh_vliChkDefaultConfig {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 8;
};

export struct vlInh_vliChkChkAltConfig {
    static constexpr uint32_t VLI_ALGO = 6;
    static constexpr uint32_t VLI_WIDTH = 10;
};

export struct vlInh_vliChkChkDefConfig {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 8;
};

export struct vlInh_vliChkChkSoloConfig {
    static constexpr uint32_t VLI_ALGO = 3;
    static constexpr uint32_t VLI_WIDTH = 8;
};

// GENERATED_CODE_END
