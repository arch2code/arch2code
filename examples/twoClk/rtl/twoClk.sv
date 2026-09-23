//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: twoClk
module twoClk
// Generated Import package statement(s)
import twoClkIp_package::*;
import twoClk_package::*;
(
    apb_if.dst twoClkReg,
    input clk, clkSlow, rst_n, rstSlow_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(twoClkDataSt)) out_0();
    push_ack_if #(.data_t(twoClkDataSt)) out_1();
    apb_if #(.addr_t(twoClkRegAddrSt), .data_t(twoClkRegDataSt)) twoClkReg_uTable();

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
    .clkTick (clkSlow),
    .rstTick_n (rstSlow_n)
);

twoClk_twoClkSlowSink uSlowSink (
    .in (out_1),
    .clkSlow (clkSlow),
    .rstSlow_n (rstSlow_n)
);

twoClk_twoClkDecode uDecode (
    .twoClkReg (twoClkReg),
    .twoClkReg_uTable (twoClkReg_uTable),
    .clk (clk),
    .rst_n (rst_n)
);

twoClk_twoClkTable uTable (
    .twoClkReg (twoClkReg_uTable),
    .clk (clk),
    .clkSlow (clkSlow),
    .rst_n (rst_n),
    .rstSlow_n (rstSlow_n)
);

// GENERATED_CODE_END

endmodule: twoClk
