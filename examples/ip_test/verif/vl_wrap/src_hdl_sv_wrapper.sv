`ifndef _SRC_HDL_SV_WRAPPER_SV_GUARD_
`define _SRC_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module src_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ipLeaf_package::*;
    import src_package::*;
(
    // push_ack_if.src
    output bit out0_push,
    output bit [8:0] out0_data,
    input bit out0_ack,

    // push_ack_if.src
    output bit out1_push,
    output bit [70:0] out1_data,
    input bit out1_ack,

    input clk,
    input rst_n
);
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

    src dut (
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

endmodule : src_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _SRC_HDL_SV_WRAPPER_SV_GUARD_
