`ifndef _SRC_HDL_SV_WRAPPER_SVH_GUARD_
`define _SRC_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

module src_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_test_ipLeaf_package::*;
    import ip_test_src_package::*;
#(
    parameter OUT0_DATA_WIDTH,
    parameter OUT1_DATA_WIDTH
) (
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

    // push_ack_if.src
    push_ack_if #(.data_t(srcOut0St)) out2();

    assign #0 out2_push = out2.push;
    assign #0 out2_data = out2.data;
    assign #0 out2.ack = out2_ack;

    // push_ack_if.src
    push_ack_if #(.data_t(srcOut1St)) out3();

    assign #0 out3_push = out3.push;
    assign #0 out3_data = out3.data;
    assign #0 out3.ack = out3_ack;

    ip_test_src #(.OUT0_DATA_WIDTH(OUT0_DATA_WIDTH), .OUT1_DATA_WIDTH(OUT1_DATA_WIDTH)) dut (
        .out0(out0), // push_ack_if.src
        .out1(out1), // push_ack_if.src
        .out2(out2), // push_ack_if.src
        .out3(out3), // push_ack_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : src_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _SRC_HDL_SV_WRAPPER_SVH_GUARD_
