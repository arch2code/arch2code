`ifndef _SRC_VARIANTSRC0_HDL_SV_WRAPPER_SV_GUARD_
`define _SRC_VARIANTSRC0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=src --variant=variantSrc0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module src_variantSrc0_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ipLeaf_package::*;
    import src_package::*;
(
    // push_ack_if.src
    output bit out0_push,
    output bit [(OUT0_DATA_WIDTH + 1)-1:0] out0_data,
    input bit out0_ack,

    // push_ack_if.src
    output bit out1_push,
    output bit [(OUT1_DATA_WIDTH + 1)-1:0] out1_data,
    input bit out1_ack,

    input clk,
    input rst_n
);
    localparam OUT0_DATA_WIDTH = 8;
    localparam OUT1_DATA_WIDTH = 70;
    typedef logic[OUT0_DATA_WIDTH-1:0] srcOut0DataT; //src out0 data word, parameterizable
    typedef logic[OUT1_DATA_WIDTH-1:0] srcOut1DataT; //src out1 data word, parameterizable
    typedef struct packed {
        srcMarkerT marker; //marker bit copied through the thunker
        srcOut0DataT data; //src out0 payload
    } srcOut0St;
    typedef struct packed {
        srcMarkerT marker; //marker bit above bit 64 for the 70-bit variant
        srcOut1DataT data; //src out1 payload
    } srcOut1St;

    // push_ack_if.src
    push_ack_if #(.data_t(srcOut0St)) out0();

    assign #0 out0_push = out0.push;
    assign #0 out0_data = out0.data;
    assign #0 out0.ack = out0_ack;

    // push_ack_if.src
    push_ack_if #(.data_t(srcOut1St)) out1();

    assign #0 out1_push = out1.push;
    assign #0 out1_data = out1.data;
    assign #0 out1.ack = out1_ack;

    src #(.OUT0_DATA_WIDTH(8), .OUT1_DATA_WIDTH(70)) dut (
        .out0(out0), // push_ack_if.src
        .out1(out1), // push_ack_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : src_variantSrc0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _SRC_VARIANTSRC0_HDL_SV_WRAPPER_SV_GUARD_
