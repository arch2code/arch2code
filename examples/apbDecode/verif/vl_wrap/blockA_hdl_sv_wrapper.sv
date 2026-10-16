`ifndef _BLOCKA_HDL_SV_WRAPPER_SV_GUARD_
`define _BLOCKA_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module blockA_hdl_sv_wrapper
    // Generated Import package statement(s)
    import apbDecode_package::*;
(
    // apb_if.dst
    input bit [31:0] apbReg_paddr,
    input bit apbReg_psel,
    input bit apbReg_penable,
    input bit apbReg_pwrite,
    input bit [31:0] apbReg_pwdata,
    output bit apbReg_pready,
    output bit [31:0] apbReg_prdata,
    output bit apbReg_pslverr,

    input clk,
    input rst_n
);
    // apb_if.dst
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg();

    assign `A2C_HDL_BOUNDARY_DLY apbReg.paddr = apbReg_paddr;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.psel = apbReg_psel;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.penable = apbReg_penable;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.pwrite = apbReg_pwrite;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.pwdata = apbReg_pwdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_pready = apbReg.pready;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_prdata = apbReg.prdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_pslverr = apbReg.pslverr;

    blockA dut (
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : blockA_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BLOCKA_HDL_SV_WRAPPER_SV_GUARD_
