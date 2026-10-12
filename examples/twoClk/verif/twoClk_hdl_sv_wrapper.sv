`ifndef _TWOCLK_HDL_SV_WRAPPER_SV_GUARD_
`define _TWOCLK_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module twoClk_hdl_sv_wrapper
    // Generated Import package statement(s)
    import twoClkIp_package::*;
    import twoClk_package::*;
(
    // apb_if.dst
    input bit [31:0] twoClkReg_paddr,
    input bit twoClkReg_psel,
    input bit twoClkReg_penable,
    input bit twoClkReg_pwrite,
    input bit [31:0] twoClkReg_pwdata,
    output bit twoClkReg_pready,
    output bit [31:0] twoClkReg_prdata,
    output bit twoClkReg_pslverr,

    input clk,
    input clkSlow,
    input rst_n,
    input rstSlow_n
);
    // apb_if.dst
    apb_if #(.addr_t(twoClkRegAddrSt), .data_t(twoClkRegDataSt)) twoClkReg();

    assign `A2C_HDL_BOUNDARY_DLY twoClkReg.paddr = twoClkReg_paddr;
    assign `A2C_HDL_BOUNDARY_DLY twoClkReg.psel = twoClkReg_psel;
    assign `A2C_HDL_BOUNDARY_DLY twoClkReg.penable = twoClkReg_penable;
    assign `A2C_HDL_BOUNDARY_DLY twoClkReg.pwrite = twoClkReg_pwrite;
    assign `A2C_HDL_BOUNDARY_DLY twoClkReg.pwdata = twoClkReg_pwdata;
    assign `A2C_HDL_BOUNDARY_DLY twoClkReg_pready = twoClkReg.pready;
    assign `A2C_HDL_BOUNDARY_DLY twoClkReg_prdata = twoClkReg.prdata;
    assign `A2C_HDL_BOUNDARY_DLY twoClkReg_pslverr = twoClkReg.pslverr;

    twoClk dut (
        .twoClkReg(twoClkReg), // apb_if.dst
        .clk(clk),
        .clkSlow(clkSlow),
        .rst_n(rst_n),
        .rstSlow_n(rstSlow_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : twoClk_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _TWOCLK_HDL_SV_WRAPPER_SV_GUARD_
