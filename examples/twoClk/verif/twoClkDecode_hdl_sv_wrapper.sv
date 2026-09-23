`ifndef _TWOCLKDECODE_HDL_SV_WRAPPER_SV_GUARD_
`define _TWOCLKDECODE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=twoClkDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module twoClkDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import twoClk_package::*;
(
    // apb_if.src
    output bit [31:0] twoClkReg_uTable_paddr,
    output bit twoClkReg_uTable_psel,
    output bit twoClkReg_uTable_penable,
    output bit twoClkReg_uTable_pwrite,
    output bit [31:0] twoClkReg_uTable_pwdata,
    input bit twoClkReg_uTable_pready,
    input bit [31:0] twoClkReg_uTable_prdata,
    input bit twoClkReg_uTable_pslverr,

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
    input rst_n
);
    // apb_if.src
    apb_if #(.addr_t(twoClkRegAddrSt), .data_t(twoClkRegDataSt)) twoClkReg_uTable();

    assign #0 twoClkReg_uTable_paddr = twoClkReg_uTable.paddr;
    assign #0 twoClkReg_uTable_psel = twoClkReg_uTable.psel;
    assign #0 twoClkReg_uTable_penable = twoClkReg_uTable.penable;
    assign #0 twoClkReg_uTable_pwrite = twoClkReg_uTable.pwrite;
    assign #0 twoClkReg_uTable_pwdata = twoClkReg_uTable.pwdata;
    assign #0 twoClkReg_uTable.pready = twoClkReg_uTable_pready;
    assign #0 twoClkReg_uTable.prdata = twoClkReg_uTable_prdata;
    assign #0 twoClkReg_uTable.pslverr = twoClkReg_uTable_pslverr;

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

    twoClk_twoClkDecode dut (
        .twoClkReg_uTable(twoClkReg_uTable), // apb_if.src
        .twoClkReg(twoClkReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : twoClkDecode_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _TWOCLKDECODE_HDL_SV_WRAPPER_SV_GUARD_
