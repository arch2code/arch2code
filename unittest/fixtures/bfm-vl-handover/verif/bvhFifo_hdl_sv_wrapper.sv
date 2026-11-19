`ifndef _BVHFIFO_HDL_SV_WRAPPER_SV_GUARD_
`define _BVHFIFO_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=bvhFifo
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module bvhFifo_hdl_sv_wrapper
    // Generated Import package statement(s)
    import bvh_package::*;
(
    // rdy_vld_if.dst
    input bit in_vld,
    input bit [15:0] in_data,
    output bit in_rdy,

    // rdy_vld_if.src
    output bit out_vld,
    output bit [15:0] out_data,
    input bit out_rdy,

    input clk,
    input rst_n
);
    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(bvhBeat)) in();

    assign `A2C_HDL_BOUNDARY_DLY in.vld = in_vld;
    assign `A2C_HDL_BOUNDARY_DLY in.data = in_data;
    assign `A2C_HDL_BOUNDARY_DLY in_rdy = in.rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(bvhBeat)) out();

    assign `A2C_HDL_BOUNDARY_DLY out_vld = out.vld;
    assign `A2C_HDL_BOUNDARY_DLY out_data = out.data;
    assign `A2C_HDL_BOUNDARY_DLY out.rdy = out_rdy;

    bvhFifo dut (
        .in(in), // rdy_vld_if.dst
        .out(out), // rdy_vld_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : bvhFifo_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BVHFIFO_HDL_SV_WRAPPER_SV_GUARD_
