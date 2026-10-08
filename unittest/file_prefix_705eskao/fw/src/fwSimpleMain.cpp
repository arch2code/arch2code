// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "fwSimpleMain.h"
#include "regRdWr.h"

namespace fw_ns {

// Marker payload dataGen drives into uIp.
static constexpr uint32_t IP_LAST_DATA_MARKER = 0xA5;

bool fwCheckUIp(void)
{
    // Read the last data word captured by uIp and verify the marker payload
    // dataGen pushed on ipDataIf.
    uint32_t lastData = regRead32(BASE_ADDR_UIP + REG_IP_IPLASTDATA);
    if ((lastData & 0xFF) != IP_LAST_DATA_MARKER)
    {
        return false;
    }

    // Exercise the rw ipCfg register: write a known pattern to the low word and
    // read it back. The pattern uses a generated firmware constant from
    // ipIncludesFW.h, so this firmware is a real consumer of the per-context FW
    // header's constants section.
    uint32_t pattern = IP_FIXED_WORD_COUNT;
    regWrite32(BASE_ADDR_UIP + REG_IP_IPCFG, pattern);
    uint32_t readback = regRead32(BASE_ADDR_UIP + REG_IP_IPCFG);
    return (readback & 0xFF) == (pattern & 0xFF);
}

} // namespace fw_ns
