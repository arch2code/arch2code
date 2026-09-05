`ifndef XVIMID_XVILEAF_V0_HDL_SV_WRAPPER_SV_GUARD_
`define XVIMID_XVILEAF_V0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=xviLeaf --parent=xviMid/../../yaml/xviMid.yaml --variant=v0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "xviLeaf_hdl_sv_wrapper.svh"

module xviMid_xviLeaf_v0_hdl_sv_wrapper
    // Generated Import package statement(s)
    import xviLeaf_package::*;
#(
    localparam XVI_WIDTH = 8,
    localparam XVI_GAIN = 7
)(
    // push_ack_if.dst
    input bit in_push,
    input bit [(XVI_WIDTH + 8)-1:0] in_data,
    output bit in_ack,

    // push_ack_if.src
    output bit out_push,
    output bit [(XVI_WIDTH + 8)-1:0] out_data,
    input bit out_ack,

    input clk,
    input rst_n
);
    xviLeaf_hdl_sv_wrapper #(
        .XVI_WIDTH(XVI_WIDTH),
        .XVI_GAIN(XVI_GAIN)
    ) u_wrapper (
        .in_push(in_push),
        .in_data(in_data),
        .in_ack(in_ack),
        .out_push(out_push),
        .out_data(out_data),
        .out_ack(out_ack),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : xviMid_xviLeaf_v0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // XVIMID_XVILEAF_V0_HDL_SV_WRAPPER_SV_GUARD_
