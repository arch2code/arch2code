`ifndef _SRC_VARIANTSRC0_HDL_SV_WRAPPER_SV_GUARD_
`define _SRC_VARIANTSRC0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=src --variant=variantSrc0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "src_hdl_sv_wrapper.svh"

module src_variantSrc0_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ipLeaf_package::*;
    import src_package::*;
#(
    localparam OUT0_DATA_WIDTH = 8,
    localparam OUT1_DATA_WIDTH = 70
)(
    // push_ack_if.src
    output bit out0_push,
    output bit [(OUT0_DATA_WIDTH + 1)-1:0] out0_data,
    input bit out0_ack,

    // push_ack_if.src
    output bit out1_push,
    output bit [(OUT1_DATA_WIDTH + 1)-1:0] out1_data,
    input bit out1_ack,

    // push_ack_if.src
    output bit out2_push,
    output bit [(OUT0_DATA_WIDTH + 1)-1:0] out2_data,
    input bit out2_ack,

    // push_ack_if.src
    output bit out3_push,
    output bit [(OUT1_DATA_WIDTH + 1)-1:0] out3_data,
    input bit out3_ack,

    input clk,
    input rst_n
);
    src_hdl_sv_wrapper #(
        .OUT0_DATA_WIDTH(OUT0_DATA_WIDTH),
        .OUT1_DATA_WIDTH(OUT1_DATA_WIDTH)
    ) u_wrapper (
        .out0_push(out0_push),
        .out0_data(out0_data),
        .out0_ack(out0_ack),
        .out1_push(out1_push),
        .out1_data(out1_data),
        .out1_ack(out1_ack),
        .out2_push(out2_push),
        .out2_data(out2_data),
        .out2_ack(out2_ack),
        .out3_push(out3_push),
        .out3_data(out3_data),
        .out3_ack(out3_ack),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : src_variantSrc0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _SRC_VARIANTSRC0_HDL_SV_WRAPPER_SV_GUARD_
