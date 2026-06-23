// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "fwIpMain.h"

namespace fw_ns {

// Marker payload the src block drives into uIp0.
static constexpr uint32_t IP_LAST_DATA_MARKER = 0xA5;

bool fwCheckUIp0(ipRegBus &bus)
{
    // Read the last data word captured by uIp0 and verify the marker payload.
    uint32_t lastData = bus.read32(BASE_ADDR_UIP0 + REG_IP_IPLASTDATA);
    if ((lastData & 0xFF) != IP_LAST_DATA_MARKER)
    {
        return false;
    }

    // Exercise the rw ipCfg register: write a known pattern to the low word and
    // read it back. The pattern uses a generated firmware constant from
    // ipIncludesFW.h so this firmware is a real consumer of the per-context FW
    // header's constants section.
    uint32_t pattern = IP_FIXED_WORD_COUNT;
    bus.write32(BASE_ADDR_UIP0 + REG_IP_IPCFG, pattern);
    uint32_t readback = bus.read32(BASE_ADDR_UIP0 + REG_IP_IPCFG);
    return (readback & 0xFF) == (pattern & 0xFF);
}

bool fwCheckUIp1(ipRegBus &bus)
{
    // uIp1 receives the 70-bit boundary payload. Issue the ipLastData read to
    // exercise the path; the captured value is not asserted on here.
    (void)bus.read32(BASE_ADDR_UIP1 + REG_IP_IPLASTDATA);

    // Consume a parameterizable eval-derived FW constant: IP_DATA_WIDTH_X2 is
    // generated symbolically (IP_DATA_WIDTH * 2) into ipIncludesFW.h, so this
    // firmware is a real consumer of the FW header's parameterizable constants
    // section. Write its low byte to ipCfg and read it back.
    uint32_t pattern = IP_DATA_WIDTH_X2;
    bus.write32(BASE_ADDR_UIP1 + REG_IP_IPCFG, pattern);
    uint32_t readback = bus.read32(BASE_ADDR_UIP1 + REG_IP_IPCFG);
    return (readback & 0xFF) == (pattern & 0xFF);
}

} // namespace fw_ns
