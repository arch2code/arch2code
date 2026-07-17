#ifndef FW_IP_MAIN_H
#define FW_IP_MAIN_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

#include "ipIncludesFW.h"   // fw_ns generated constants / types (e.g. IP_FIXED_WORD_COUNT)
#include "regAddresses.h"   // BASE_ADDR_* instance bases and REG_IP_* register offsets

namespace fw_ns {

// Firmware register program for the ip_test top.
//
// The firmware runs on a worker thread and reaches the APB register bus through
// the BSP transport (bsp/regRdWr.h global regRead32 / regWrite32): each access
// is marshalled over a cross-thread lock-free queue that the common 'cpu'
// block's regWriteListener drains onto the apb bus. This mirrors the pro
// gold-standard firmware path (fwLmmiDemoMain). The earlier std::function
// ipRegBus seam has been retired now that the BSP register-access code is
// compiled into every base build.
//
// fwCheckUIp0 / fwCheckUIp1 exercise the ip register set and each return true on
// success so the worker can assert and report through the model test framework.
// They consume the generated ipIncludesFW.h constants and the generated register
// addresses, making the firmware a real consumer of the per-context FW header.
bool fwCheckUIp0(void);
bool fwCheckUIp1(void);

} // namespace fw_ns

#endif // FW_IP_MAIN_H
