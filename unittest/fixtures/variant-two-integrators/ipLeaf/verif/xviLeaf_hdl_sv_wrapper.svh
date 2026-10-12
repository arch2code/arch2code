`ifndef _XVILEAF_HDL_SV_WRAPPER_SVH_GUARD_
`define _XVILEAF_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=xviLeaf
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

`include "hdlBoundary.svh"

module xviLeaf_hdl_sv_wrapper
    // Generated Import package statement(s)
    import xviLeaf_package::*;
#(
    parameter XVI_WIDTH,
    parameter XVI_GAIN
) (
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
    typedef logic[XVI_WIDTH-1:0] xviPixelT; //Parameterizable pixel word
    typedef struct packed {
        xviTagT tag; //Sample sequence tag
        xviPixelT data; //Parameterizable pixel payload
    } xviSt;

    // push_ack_if.dst
    push_ack_if #(.data_t(xviSt)) in();

    assign `A2C_HDL_BOUNDARY_DLY in.push = in_push;
    assign `A2C_HDL_BOUNDARY_DLY in.data = in_data;
    assign `A2C_HDL_BOUNDARY_DLY in_ack = in.ack;

    // push_ack_if.src
    push_ack_if #(.data_t(xviSt)) out();

    assign `A2C_HDL_BOUNDARY_DLY out_push = out.push;
    assign `A2C_HDL_BOUNDARY_DLY out_data = out.data;
    assign `A2C_HDL_BOUNDARY_DLY out.ack = out_ack;

    xviLeaf #(.XVI_WIDTH(XVI_WIDTH), .XVI_GAIN(XVI_GAIN)) dut (
        .in(in), // push_ack_if.dst
        .out(out), // push_ack_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : xviLeaf_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _XVILEAF_HDL_SV_WRAPPER_SVH_GUARD_
