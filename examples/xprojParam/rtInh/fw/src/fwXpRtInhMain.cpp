// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "fwXpRtInhMain.h"
#include "regRdWr.h"

namespace fw_ns {

// Pattern written to uLeaf's cfg register. Uses all 32 bits of the
// RT_WIDTH=32-bound payload, so a default-width (8-bit) register handler
// would fail this compare.
static constexpr uint32_t XPRTINH_CFG_PATTERN = 0xA5C3F00F;

bool fwCheckULeaf(void)
{
    // Every level's base address on the dispatch path, plus the register offset.
    uint32_t addr = BASE_ADDR_UWRAP + BASE_ADDR_ULEAF + REG_XPRTLEAF_CFG;

    regWrite32(addr, XPRTINH_CFG_PATTERN);
    uint32_t readback = regRead32(addr);
    return readback == XPRTINH_CFG_PATTERN;
}

} // namespace fw_ns
