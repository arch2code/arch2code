`ifndef _PRODUCER_HDL_SV_WRAPPER_SV_GUARD_
`define _PRODUCER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module producer_hdl_sv_wrapper
    // Generated Import package statement(s)
    import simple_package::*;
(
    // push_ack_if.src
    output bit tag0_push,
    output bit [4:0] tag0_data,
    input bit tag0_ack,

    // push_ack_if.src
    output bit tag1_push,
    output bit [4:0] tag1_data,
    input bit tag1_ack,

    input clk,
    input rst_n
);
    // push_ack_if.src
    push_ack_if #(.data_t(tag_st)) tag0();

    assign #0 tag0_push = tag0.push;
    assign #0 tag0_data = tag0.data;
    assign #0 tag0.ack = tag0_ack;

    // push_ack_if.src
    push_ack_if #(.data_t(tag_st)) tag1();

    assign #0 tag1_push = tag1.push;
    assign #0 tag1_data = tag1.data;
    assign #0 tag1.ack = tag1_ack;

    simple_producer dut (
        .tag0(tag0), // push_ack_if.src
        .tag1(tag1), // push_ack_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : producer_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _PRODUCER_HDL_SV_WRAPPER_SV_GUARD_
