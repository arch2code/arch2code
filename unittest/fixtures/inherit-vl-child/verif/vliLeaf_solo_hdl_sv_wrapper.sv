`ifndef _VLILEAF_SOLO_HDL_SV_WRAPPER_SV_GUARD_
`define _VLILEAF_SOLO_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=vliLeaf --variant=solo
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "vliLeaf_hdl_sv_wrapper.svh"

module vliLeaf_solo_hdl_sv_wrapper
    // Generated Import package statement(s)
    import vlInh_vliCont_package::*;
#(
    localparam VLI_ALGO = 3,
    localparam VLI_WIDTH = 8
)(
    // push_ack_if.src
    output bit out_push,
    output bit [(8 + VLI_WIDTH + 8 + 8 + 8)-1:0] out_data,
    input bit out_ack,

    // push_ack_if.dst
    input bit in_push,
    input bit [(8 + VLI_WIDTH + 8 + 8 + 8)-1:0] in_data,
    output bit in_ack,

    input clk,
    input rst_n
);
    vliLeaf_hdl_sv_wrapper #(
        .VLI_ALGO(VLI_ALGO),
        .VLI_WIDTH(VLI_WIDTH)
    ) u_wrapper (
        .out_push(out_push),
        .out_data(out_data),
        .out_ack(out_ack),
        .in_push(in_push),
        .in_data(in_data),
        .in_ack(in_ack),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : vliLeaf_solo_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _VLILEAF_SOLO_HDL_SV_WRAPPER_SV_GUARD_
