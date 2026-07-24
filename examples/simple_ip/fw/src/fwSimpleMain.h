#ifndef FW_SIMPLE_MAIN_H
#define FW_SIMPLE_MAIN_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

#include "ipIncludesFW.h"   // fw_ns generated constants (e.g. IP_FIXED_WORD_COUNT)
#include "regAddresses.h"   // BASE_ADDR_UIP + REG_IP_* register offsets

namespace fw_ns {

// Firmware register program for the simple_ip top.
//
// The firmware runs on a worker thread and reaches the APB register bus through
// the BSP transport (regRdWr.h global regRead32 / regWrite32): each access is
// marshalled over a cross-thread queue the common 'cpu' block drains onto the
// apb bus. fwCheckUIp exercises the reused ip's register set and returns true on
// success so the worker can assert through the model test framework. It consumes
// the generated ipIncludesFW.h constant and the generated register addresses,
// making the firmware a real consumer of the per-context FW header.
bool fwCheckUIp(void);

} // namespace fw_ns

#endif // FW_SIMPLE_MAIN_H
