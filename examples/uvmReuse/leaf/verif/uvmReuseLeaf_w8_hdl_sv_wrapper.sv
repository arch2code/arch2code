`ifndef _UVMREUSELEAF_W8_HDL_SV_WRAPPER_SV_GUARD_
`define _UVMREUSELEAF_W8_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --variant=w8
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "uvmReuseLeaf_hdl_sv_wrapper.svh"

module uvmReuseLeaf_w8_hdl_sv_wrapper
    // Generated Import package statement(s)
    import uvmReuseLeaf_package::*;
#(
    localparam UVM_REUSE_OFF_W = 8
)(
    // rdy_vld_if.dst
    input bit in_vld,
    input bit [18:0] in_data,
    output bit in_rdy,

    // rdy_vld_if.src
    output bit out_vld,
    output bit [18:0] out_data,
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
    uvmReuseLeaf_hdl_sv_wrapper #(
        .UVM_REUSE_OFF_W(UVM_REUSE_OFF_W)
    ) u_wrapper (
        .in_vld(in_vld),
        .in_data(in_data),
        .in_rdy(in_rdy),
        .out_vld(out_vld),
        .out_data(out_data),
        .out_rdy(out_rdy),
        .apbReg_paddr(apbReg_paddr),
        .apbReg_psel(apbReg_psel),
        .apbReg_penable(apbReg_penable),
        .apbReg_pwrite(apbReg_pwrite),
        .apbReg_pwdata(apbReg_pwdata),
        .apbReg_pready(apbReg_pready),
        .apbReg_prdata(apbReg_prdata),
        .apbReg_pslverr(apbReg_pslverr),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : uvmReuseLeaf_w8_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _UVMREUSELEAF_W8_HDL_SV_WRAPPER_SV_GUARD_
