`ifndef _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_
`define _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module consumer_hdl_sv_wrapper
    // Generated Import package statement(s)
    import simple_package::*;
(
    // push_ack_if.dst
    input bit tag0_push,
    input bit [4:0] tag0_data,
    output bit tag0_ack,

    // push_ack_if.dst
    input bit tag1_push,
    input bit [4:0] tag1_data,
    output bit tag1_ack,

    input clk,
    input rst_n
);
    // push_ack_if.dst
    push_ack_if #(.data_t(tag_st)) tag0();

    assign `A2C_HDL_BOUNDARY_DLY tag0.push = tag0_push;
    assign `A2C_HDL_BOUNDARY_DLY tag0.data = tag0_data;
    assign `A2C_HDL_BOUNDARY_DLY tag0_ack = tag0.ack;

    // push_ack_if.dst
    push_ack_if #(.data_t(tag_st)) tag1();

    assign `A2C_HDL_BOUNDARY_DLY tag1.push = tag1_push;
    assign `A2C_HDL_BOUNDARY_DLY tag1.data = tag1_data;
    assign `A2C_HDL_BOUNDARY_DLY tag1_ack = tag1.ack;

    consumer dut (
        .tag0(tag0), // push_ack_if.dst
        .tag1(tag1), // push_ack_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

    `ifndef VERILATOR
    push_ack_xcheck tag0_xcheck (.clk(clk), .rst_n(rst_n), .intf(tag0));
    push_ack_xcheck tag1_xcheck (.clk(clk), .rst_n(rst_n), .intf(tag1));
    `endif

endmodule : consumer_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_
