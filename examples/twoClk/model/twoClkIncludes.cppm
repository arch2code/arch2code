
// GENERATED_CODE_PARAM --project=twoClk --context=../../yaml/twoClk.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module twoClk;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import twoClkIp;
using namespace twoClkIp_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace twoClk_ns {
//constants
inline constexpr uint32_t TWO_CLK_TICK_DIV = 4;  // clkSlow cycles between consecutive tick words
inline constexpr uint32_t TWO_CLK_TICK_WORDS = 4;  // Tick words the slow sink checks before voting end-of-test
inline constexpr uint32_t TWO_CLK_SLOW_PERIOD_NS = 3;  // clkSlow period in ns; must equal clocks.clkSlow.period in prj/yaml/project.yaml

} // namespace twoClk_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace twoClk_ns {
// types

} // namespace twoClk_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace twoClk_ns {
// enums

} // namespace twoClk_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP

// GENERATED_CODE_END
