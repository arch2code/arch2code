
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=twoClk --context=../../yaml/twoClk.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package twoClk_package;
// Generated Import package statement(s)
import twoClkIp_package::*;
localparam int unsigned TWO_CLK_TICK_DIV = 32'h0000_0004;  // clkSlow cycles between consecutive tick words
localparam int unsigned TWO_CLK_TICK_WORDS = 32'h0000_0004;  // Tick words the slow sink checks before voting end-of-test
localparam int unsigned TWO_CLK_SLOW_PERIOD_NS = 32'h0000_0003;  // clkSlow period in ns; must equal clocks.clkSlow.period in prj/yaml/project.yaml

// types

// enums

// structures
endpackage : twoClk_package
// GENERATED_CODE_END
