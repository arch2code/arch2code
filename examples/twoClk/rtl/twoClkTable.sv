//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkTable
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: twoClk_twoClkTable
module twoClk_twoClkTable
// Generated Import package statement(s)
import twoClk_package::*;
(
    apb_if.dst twoClkReg,
    input clk, clkSlow, rst_n, rstSlow_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Memory Interfaces
    memory_if #(.data_t(twoClkTblSt), .addr_t(twoClkTblAddrSt)) tbl_reg();

// Instances
twoClk_twoClkTableRegs uTwoClkTableRegs (
    .twoClkReg (twoClkReg),
    .tbl (tbl_reg),
    .clk (clk),
    .clkSlow (clkSlow),
    .rst_n (rst_n),
    .rstSlow_n (rstSlow_n)
);

// Memory Instances
memory_sp #(.DEPTH(TWO_CLK_TBL_WORDS), .data_t(twoClkTblSt)) uTbl (
    .mem_port (tbl_reg),
    .clk (clkSlow)
);

// GENERATED_CODE_END

endmodule: twoClk_twoClkTable
