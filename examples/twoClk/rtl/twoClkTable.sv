//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkTable
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: twoClkTable
module twoClkTable
// Generated Import package statement(s)
import twoClk_package::*;
(
    apb_if.dst twoClkReg,
    input clk, clkSlow, rst_n, rstSlow_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Memory Interfaces
    memory_if #(.data_t(twoClkTblSt), .addr_t(twoClkTblAddrSt)) tbl();
    memory_if #(.data_t(twoClkTblSt), .addr_t(twoClkTblAddrSt)) tbl_reg();
    memory_if #(.data_t(twoClkLutSt), .addr_t(twoClkLutAddrSt)) lut();
    memory_if #(.data_t(twoClkLutSt), .addr_t(twoClkLutAddrSt)) lut_reg();
    memory_if #(.data_t(twoClkStatsSt), .addr_t(twoClkLutAddrSt)) stats_reg();
    memory_if #(.data_t(twoClkStatsSt), .addr_t(twoClkLutAddrSt)) stats();

// Instances
twoClkTableRegs uTwoClkTableRegs (
    .twoClkReg (twoClkReg),
    .tbl (tbl_reg),
    .lut (lut_reg),
    .stats (stats_reg),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
memory_dp_2clk #(.DEPTH(TWO_CLK_TBL_WORDS), .data_t(twoClkTblSt), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b0)) uTbl (
    .mem_portA (tbl),
    .mem_portB (tbl_reg),
    .clkA (clkSlow),
    .clkB (clk)
);

memory_dp_2clk #(.DEPTH(TWO_CLK_LUT_WORDS), .data_t(twoClkLutSt), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uLut (
    .mem_portA (lut),
    .mem_portB (lut_reg),
    .clkA (clkSlow),
    .clkB (clk)
);

memory_dp_2clk #(.DEPTH(TWO_CLK_LUT_WORDS), .data_t(twoClkStatsSt), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uStats (
    .mem_portA (stats_reg),
    .mem_portB (stats),
    .clkA (clk),
    .clkB (clkSlow)
);

// GENERATED_CODE_END

// Firmware reaches tbl through port B only; the block-side read port is unused.
assign tbl.enable     = 1'b0;
assign tbl.wr_en      = 1'b0;
assign tbl.addr       = '0;
assign tbl.write_data = '0;

// Sweep lut and stats on clkSlow: read lut[i] on port A, and one cycle later,
// when the read data arrives, write stats[i] = lut[i] + 1 on port B.
`DFF_INST_DOM(clkSlow, rstSlow_n, twoClkLutAddrBitsT, sweepAddr)
`DFF_INST_DOM(clkSlow, rstSlow_n, twoClkLutAddrBitsT, statsAddr)
`DFF_INST_DOM(clkSlow, rstSlow_n, logic, statsValid)

always_comb begin
    n_sweepAddr  = sweepAddr + 1'b1;
    n_statsAddr  = sweepAddr;
    n_statsValid = 1'b1;
end

assign lut.enable     = 1'b1;
assign lut.wr_en      = 1'b0;
assign lut.addr       = '{address: sweepAddr};
assign lut.write_data = '0;

assign stats.enable         = statsValid;
assign stats.wr_en          = statsValid;
assign stats.addr           = '{address: statsAddr};
assign stats.write_data.val = lut.read_data.val + 1'b1;

endmodule: twoClkTable
