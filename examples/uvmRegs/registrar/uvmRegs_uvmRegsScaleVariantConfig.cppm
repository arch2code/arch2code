//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsScale --parent=uvmRegs/../../yaml/uvmRegs.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module uvmRegs.uvmRegsScale.config;

export struct uvmRegs_uvmRegsScaleDefaultConfig {
    static constexpr uint32_t UVM_REGS_SCALE_W = 4;
};

export struct uvmRegs_uvmRegsScaleV0Config {
    static constexpr uint32_t UVM_REGS_SCALE_W = 4;
};

export struct uvmRegs_uvmRegsScaleV1Config {
    static constexpr uint32_t UVM_REGS_SCALE_W = 8;
};

// GENERATED_CODE_END
