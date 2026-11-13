`ifndef _UVMREGS_HDL_SV_WRAPPER_SV_GUARD_
`define _UVMREGS_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=uvmRegs
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module uvmRegs_hdl_sv_wrapper
    // Generated Import package statement(s)
    import uvmRegs_package::*;
(
    // rdy_vld_if.dst
    input bit in_vld,
    input bit [15:0] in_data,
    output bit in_rdy,

    // rdy_vld_if.src
    output bit out_vld,
    output bit [15:0] out_data,
    input bit out_rdy,

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
    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(uvmRegsWordSt)) in();

    assign `A2C_HDL_BOUNDARY_DLY in.vld = in_vld;
    assign `A2C_HDL_BOUNDARY_DLY in.data = in_data;
    assign `A2C_HDL_BOUNDARY_DLY in_rdy = in.rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(uvmRegsWordSt)) out();

    assign `A2C_HDL_BOUNDARY_DLY out_vld = out.vld;
    assign `A2C_HDL_BOUNDARY_DLY out_data = out.data;
    assign `A2C_HDL_BOUNDARY_DLY out.rdy = out_rdy;

    // apb_if.dst
    apb_if #(.addr_t(uvmRegsAddrSt), .data_t(uvmRegsDataSt)) apbReg();

    assign `A2C_HDL_BOUNDARY_DLY apbReg.paddr = apbReg_paddr;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.psel = apbReg_psel;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.penable = apbReg_penable;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.pwrite = apbReg_pwrite;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.pwdata = apbReg_pwdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_pready = apbReg.pready;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_prdata = apbReg.prdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_pslverr = apbReg.pslverr;

    uvmRegs dut (
        .in(in), // rdy_vld_if.dst
        .out(out), // rdy_vld_if.src
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

    `ifndef VERILATOR
    rdy_vld_xcheck in_xcheck (.clk(clk), .rst_n(rst_n), .intf(in));
    rdy_vld_xcheck out_xcheck (.clk(clk), .rst_n(rst_n), .intf(out));
    apb_xcheck apbReg_xcheck (.clk(clk), .rst_n(rst_n), .intf(apbReg));
    `endif

endmodule : uvmRegs_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _UVMREGS_HDL_SV_WRAPPER_SV_GUARD_
