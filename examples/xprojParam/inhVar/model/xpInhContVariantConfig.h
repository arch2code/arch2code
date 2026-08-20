
#ifndef XPINHCONTVARIANTCONFIG_H_
#define XPINHCONTVARIANTCONFIG_H_
// 

// GENERATED_CODE_PARAM --project=xpInhVar --context=../../yaml/xpInhCont.yaml
// GENERATED_CODE_BEGIN --template=config
#include <cstdint>
#include "clog2.h"

struct xpInhContDefaultConfig {
    static constexpr uint32_t INH_ALGO = 1;
    static constexpr uint32_t INH_WIDTH = 8;
};

struct xpInhContAltConfig {
    static constexpr uint32_t INH_ALGO = 6;
    static constexpr uint32_t INH_WIDTH = 8;
};

struct xpInhDrvDrvConfig {
    static constexpr uint32_t INH_ALGO = 1;
    static constexpr uint32_t INH_WIDTH = 8;
};

struct xpInhChkChkAltConfig {
    static constexpr uint32_t INH_ALGO = 6;
    static constexpr uint32_t INH_WIDTH = 8;
};

struct xpInhChkChkDefConfig {
    static constexpr uint32_t INH_ALGO = 1;
    static constexpr uint32_t INH_WIDTH = 8;
};

// GENERATED_CODE_END

#endif //XPINHCONTVARIANTCONFIG_H_
