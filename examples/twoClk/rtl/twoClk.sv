//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: twoClk
module twoClk
// Generated Import package statement(s)
import twoClkIp_package::*;
(
    input clk, clkSlow, rst_n, rstSlow_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(twoClkDataSt)) out_0();
    push_ack_if #(.data_t(twoClkDataSt)) out_1();

// Instances
twoClkIp_twoClkIpSrc uIpSrc (
    .out (out_0),
    .clk (clk),
    .rst_n (rst_n)
);

twoClk_twoClkSink uSink (
    .in (out_0),
    .clk (clk),
    .rst_n (rst_n)
);

twoClk_twoClkSlowTick uSlowTick (
    .out (out_1),
    .clkSlow (clkSlow),
    .rstSlow_n (rstSlow_n)
);

twoClk_twoClkSlowSink uSlowSink (
    .in (out_1),
    .clkSlow (clkSlow),
    .rstSlow_n (rstSlow_n)
);

// GENERATED_CODE_END

endmodule: twoClk
