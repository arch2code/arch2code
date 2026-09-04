
#ifndef VLICONTVARIANTCONFIG_H_
#define VLICONTVARIANTCONFIG_H_
// 

// GENERATED_CODE_PARAM --project=vlInh --context=../../yaml/vliCont.yaml
// GENERATED_CODE_BEGIN --template=config
#include <cstdint>
#include "clog2.h"

struct vliContDefaultConfig {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 8;
};

struct vliContAltConfig {
    static constexpr uint32_t VLI_ALGO = 6;
    static constexpr uint32_t VLI_WIDTH = 10;
};

struct vliLeafSoloConfig {
    static constexpr uint32_t VLI_ALGO = 3;
    static constexpr uint32_t VLI_WIDTH = 8;
};

template<typename ContainerConfig>
struct vliLeafSourcedConfig {
    static constexpr uint32_t VLI_ALGO = ContainerConfig::VLI_ALGO;
    static constexpr uint32_t VLI_WIDTH = ContainerConfig::VLI_WIDTH;
};

struct vliDrvDrvAltConfig {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 10;
};

struct vliDrvDrvDefConfig {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 8;
};

struct vliDrvDrvSoloConfig {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 8;
};

struct vliChkChkAltConfig {
    static constexpr uint32_t VLI_ALGO = 6;
    static constexpr uint32_t VLI_WIDTH = 10;
};

struct vliChkChkDefConfig {
    static constexpr uint32_t VLI_ALGO = 1;
    static constexpr uint32_t VLI_WIDTH = 8;
};

struct vliChkChkSoloConfig {
    static constexpr uint32_t VLI_ALGO = 3;
    static constexpr uint32_t VLI_WIDTH = 8;
};

// GENERATED_CODE_END

#endif //VLICONTVARIANTCONFIG_H_
