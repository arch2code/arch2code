#ifndef FW_XPRTINH_MAIN_H
#define FW_XPRTINH_MAIN_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

#include "regAddresses.h"   // BASE_ADDR_* + REG_XPRTLEAF_CFG generated address defines

namespace fw_ns {

// Writes a pattern to uLeaf's cfg register through both routers and reads it back.
bool fwCheckULeaf(void);

} // namespace fw_ns

#endif // FW_XPRTINH_MAIN_H
