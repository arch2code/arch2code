`ifndef _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_
`define _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

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

    assign #0 tag0.push = tag0_push;
    assign #0 tag0.data = tag0_data;
    assign #0 tag0_ack = tag0.ack;

    // push_ack_if.dst
    push_ack_if #(.data_t(tag_st)) tag1();

    assign #0 tag1.push = tag1_push;
    assign #0 tag1.data = tag1_data;
    assign #0 tag1_ack = tag1.ack;

    simple_consumer dut (
        .tag0(tag0), // push_ack_if.dst
        .tag1(tag1), // push_ack_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : consumer_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_
