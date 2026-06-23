#ifndef FW_IP_MAIN_H
#define FW_IP_MAIN_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>
#include <functional>

#include "ipIncludesFW.h"   // fw_ns generated constants / types (e.g. IP_FIXED_WORD_COUNT)
#include "regAddresses.h"   // BASE_ADDR_* instance bases and REG_IP_* register offsets

namespace fw_ns {

// Register access seam supplied by the SystemC cpu model.
//
// builder/base examples do not link the firmware BSP, so this firmware reaches
// the APB register bus through a minimal synchronous seam: the cpu binds these
// callables to its apb master port and invokes the firmware from its own
// SystemC thread.
//
// PRO/A2CPRO DIFFERENCE: with the firmware BSP linked, firmware instead calls
// the global regRead32()/regWrite32() (regRdWr.h), which marshal accesses over
// a cross-thread lock-free queue that a cpu listener thread drains onto the apb
// bus, with the firmware running on its own worker thread. Do not pull that BSP
// transport into a base example (it cannot link it), and do not carry this
// synchronous seam into a BSP-enabled project; use the BSP path there instead.
struct ipRegBus
{
    std::function<void(uint64_t address, uint32_t value)> write32;
    std::function<uint32_t(uint64_t address)>             read32;
};

// Firmware routines that exercise the ip register set through the bus seam.
// Each returns true on success so the caller can report through the model's
// test framework. They consume the generated ipIncludesFW.h constants and the
// generated register addresses, making the firmware a real consumer of the
// per-context FW header.
bool fwCheckUIp0(ipRegBus &bus);
bool fwCheckUIp1(ipRegBus &bus);

} // namespace fw_ns

#endif // FW_IP_MAIN_H
