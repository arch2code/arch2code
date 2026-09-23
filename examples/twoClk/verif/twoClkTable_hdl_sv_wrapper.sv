`ifndef _TWOCLKTABLE_HDL_SV_WRAPPER_SV_GUARD_
`define _TWOCLKTABLE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=twoClkTable
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module twoClkTable_hdl_sv_wrapper
    // Generated Import package statement(s)
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

    assign #0 twoClkReg.paddr = twoClkReg_paddr;
    assign #0 twoClkReg.psel = twoClkReg_psel;
    assign #0 twoClkReg.penable = twoClkReg_penable;
    assign #0 twoClkReg.pwrite = twoClkReg_pwrite;
    assign #0 twoClkReg.pwdata = twoClkReg_pwdata;
    assign #0 twoClkReg_pready = twoClkReg.pready;
    assign #0 twoClkReg_prdata = twoClkReg.prdata;
    assign #0 twoClkReg_pslverr = twoClkReg.pslverr;

    twoClk_twoClkTable dut (
        .twoClkReg(twoClkReg), // apb_if.dst
        .clk(clk),
        .clkSlow(clkSlow),
        .rst_n(rst_n),
        .rstSlow_n(rstSlow_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : twoClkTable_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _TWOCLKTABLE_HDL_SV_WRAPPER_SV_GUARD_
