`ifndef _PYSOCKET_HDL_SV_WRAPPER_SV_GUARD_
`define _PYSOCKET_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module pySocket_hdl_sv_wrapper
    // Generated Import package statement(s)
    import pySocket_tb_package::*;
(
    // req_ack_if.src
    output bit test_req_ack_req,
    output bit [63:0] test_req_ack_data,
    input bit test_req_ack_ack,
    input bit [31:0] test_req_ack_rdata,

    // req_ack_if.src
    output bit test2Python_req_ack_req,
    output bit [63:0] test2Python_req_ack_data,
    input bit test2Python_req_ack_ack,
    input bit [31:0] test2Python_req_ack_rdata,

    // req_ack_if.dst
    input bit dut2Python_req_ack_req,
    input bit [63:0] dut2Python_req_ack_data,
    output bit dut2Python_req_ack_ack,
    output bit [31:0] dut2Python_req_ack_rdata,

    // push_ack_if.src
    output bit test_push_ack_push,
    output bit [63:0] test_push_ack_data,
    input bit test_push_ack_ack,

    // pop_ack_if.src
    output bit test_pop_ack_pop,
    input bit test_pop_ack_ack,
    input bit [31:0] test_pop_ack_rdata,

    // push_ack_if.dst
    input bit dut2Python_push_ack_push,
    input bit [63:0] dut2Python_push_ack_data,
    output bit dut2Python_push_ack_ack,

    // pop_ack_if.dst
    input bit dut2Python_pop_ack_pop,
    output bit dut2Python_pop_ack_ack,
    output bit [31:0] dut2Python_pop_ack_rdata,

    // notify_ack_if.src
    output bit test_notify_ack_notify,
    input bit test_notify_ack_ack,

    // notify_ack_if.dst
    input bit dut2Python_notify_ack_notify,
    output bit dut2Python_notify_ack_ack,

    // rdy_vld_if.src
    output bit test_rdy_vld_vld,
    output bit [63:0] test_rdy_vld_data,
    input bit test_rdy_vld_rdy,

    // rdy_vld_if.dst
    input bit dut2Python_rdy_vld_vld,
    input bit [63:0] dut2Python_rdy_vld_data,
    output bit dut2Python_rdy_vld_rdy,

    input clk,
    input rst_n
);
    // req_ack_if.src
    req_ack_if #(.data_t(p2s_message_st), .rdata_t(p2s_response_st)) test_req_ack();

    assign #0 test_req_ack_req = test_req_ack.req;
    assign #0 test_req_ack_data = test_req_ack.data;
    assign #0 test_req_ack.ack = test_req_ack_ack;
    assign #0 test_req_ack.rdata = test_req_ack_rdata;

    // req_ack_if.src
    req_ack_if #(.data_t(p2s_message_st), .rdata_t(p2s_response_st)) test2Python_req_ack();

    assign #0 test2Python_req_ack_req = test2Python_req_ack.req;
    assign #0 test2Python_req_ack_data = test2Python_req_ack.data;
    assign #0 test2Python_req_ack.ack = test2Python_req_ack_ack;
    assign #0 test2Python_req_ack.rdata = test2Python_req_ack_rdata;

    // req_ack_if.dst
    req_ack_if #(.data_t(p2s_message_st), .rdata_t(p2s_response_st)) dut2Python_req_ack();

    assign #0 dut2Python_req_ack.req = dut2Python_req_ack_req;
    assign #0 dut2Python_req_ack.data = dut2Python_req_ack_data;
    assign #0 dut2Python_req_ack_ack = dut2Python_req_ack.ack;
    assign #0 dut2Python_req_ack_rdata = dut2Python_req_ack.rdata;

    // push_ack_if.src
    push_ack_if #(.data_t(p2s_message_st)) test_push_ack();

    assign #0 test_push_ack_push = test_push_ack.push;
    assign #0 test_push_ack_data = test_push_ack.data;
    assign #0 test_push_ack.ack = test_push_ack_ack;

    // pop_ack_if.src
    pop_ack_if #(.rdata_t(p2s_response_st)) test_pop_ack();

    assign #0 test_pop_ack_pop = test_pop_ack.pop;
    assign #0 test_pop_ack.ack = test_pop_ack_ack;
    assign #0 test_pop_ack.rdata = test_pop_ack_rdata;

    // push_ack_if.dst
    push_ack_if #(.data_t(p2s_message_st)) dut2Python_push_ack();

    assign #0 dut2Python_push_ack.push = dut2Python_push_ack_push;
    assign #0 dut2Python_push_ack.data = dut2Python_push_ack_data;
    assign #0 dut2Python_push_ack_ack = dut2Python_push_ack.ack;

    // pop_ack_if.dst
    pop_ack_if #(.rdata_t(p2s_response_st)) dut2Python_pop_ack();

    assign #0 dut2Python_pop_ack.pop = dut2Python_pop_ack_pop;
    assign #0 dut2Python_pop_ack_ack = dut2Python_pop_ack.ack;
    assign #0 dut2Python_pop_ack_rdata = dut2Python_pop_ack.rdata;

    // notify_ack_if.src
    notify_ack_if #() test_notify_ack();

    assign #0 test_notify_ack_notify = test_notify_ack.notify;
    assign #0 test_notify_ack.ack = test_notify_ack_ack;

    // notify_ack_if.dst
    notify_ack_if #() dut2Python_notify_ack();

    assign #0 dut2Python_notify_ack.notify = dut2Python_notify_ack_notify;
    assign #0 dut2Python_notify_ack_ack = dut2Python_notify_ack.ack;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(p2s_message_st)) test_rdy_vld();

    assign #0 test_rdy_vld_vld = test_rdy_vld.vld;
    assign #0 test_rdy_vld_data = test_rdy_vld.data;
    assign #0 test_rdy_vld.rdy = test_rdy_vld_rdy;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(p2s_message_st)) dut2Python_rdy_vld();

    assign #0 dut2Python_rdy_vld.vld = dut2Python_rdy_vld_vld;
    assign #0 dut2Python_rdy_vld.data = dut2Python_rdy_vld_data;
    assign #0 dut2Python_rdy_vld_rdy = dut2Python_rdy_vld.rdy;

    pySocket dut (
        .test_req_ack(test_req_ack), // req_ack_if.src
        .test2Python_req_ack(test2Python_req_ack), // req_ack_if.src
        .dut2Python_req_ack(dut2Python_req_ack), // req_ack_if.dst
        .test_push_ack(test_push_ack), // push_ack_if.src
        .test_pop_ack(test_pop_ack), // pop_ack_if.src
        .dut2Python_push_ack(dut2Python_push_ack), // push_ack_if.dst
        .dut2Python_pop_ack(dut2Python_pop_ack), // pop_ack_if.dst
        .test_notify_ack(test_notify_ack), // notify_ack_if.src
        .dut2Python_notify_ack(dut2Python_notify_ack), // notify_ack_if.dst
        .test_rdy_vld(test_rdy_vld), // rdy_vld_if.src
        .dut2Python_rdy_vld(dut2Python_rdy_vld), // rdy_vld_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : pySocket_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _PYSOCKET_HDL_SV_WRAPPER_SV_GUARD_
