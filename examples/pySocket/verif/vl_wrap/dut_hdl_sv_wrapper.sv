`ifndef _DUT_HDL_SV_WRAPPER_SV_GUARD_
`define _DUT_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module dut_hdl_sv_wrapper
    // Generated Import package statement(s)
    import pySocket_tb_package::*;
(
    // req_ack_if.dst
    input bit test_req_ack_req,
    input bit [63:0] test_req_ack_data,
    output bit test_req_ack_ack,
    output bit [31:0] test_req_ack_rdata,

    // req_ack_if.dst
    input bit test2Python_req_ack_req,
    input bit [63:0] test2Python_req_ack_data,
    output bit test2Python_req_ack_ack,
    output bit [31:0] test2Python_req_ack_rdata,

    // req_ack_if.src
    output bit dut2Python_req_ack_req,
    output bit [63:0] dut2Python_req_ack_data,
    input bit dut2Python_req_ack_ack,
    input bit [31:0] dut2Python_req_ack_rdata,

    // push_ack_if.dst
    input bit test_push_ack_push,
    input bit [63:0] test_push_ack_data,
    output bit test_push_ack_ack,

    // pop_ack_if.dst
    input bit test_pop_ack_pop,
    output bit test_pop_ack_ack,
    output bit [31:0] test_pop_ack_rdata,

    // push_ack_if.src
    output bit dut2Python_push_ack_push,
    output bit [63:0] dut2Python_push_ack_data,
    input bit dut2Python_push_ack_ack,

    // pop_ack_if.src
    output bit dut2Python_pop_ack_pop,
    input bit dut2Python_pop_ack_ack,
    input bit [31:0] dut2Python_pop_ack_rdata,

    // notify_ack_if.dst
    input bit test_notify_ack_notify,
    output bit test_notify_ack_ack,

    // notify_ack_if.src
    output bit dut2Python_notify_ack_notify,
    input bit dut2Python_notify_ack_ack,

    // rdy_vld_if.dst
    input bit test_rdy_vld_vld,
    input bit [63:0] test_rdy_vld_data,
    output bit test_rdy_vld_rdy,

    // rdy_vld_if.src
    output bit dut2Python_rdy_vld_vld,
    output bit [63:0] dut2Python_rdy_vld_data,
    input bit dut2Python_rdy_vld_rdy,

    input clk,
    input rst_n
);
    // req_ack_if.dst
    req_ack_if #(.data_t(p2s_message_st), .rdata_t(p2s_response_st)) test_req_ack();

    assign #0 test_req_ack.req = test_req_ack_req;
    assign #0 test_req_ack.data = test_req_ack_data;
    assign #0 test_req_ack_ack = test_req_ack.ack;
    assign #0 test_req_ack_rdata = test_req_ack.rdata;

    // req_ack_if.dst
    req_ack_if #(.data_t(p2s_message_st), .rdata_t(p2s_response_st)) test2Python_req_ack();

    assign #0 test2Python_req_ack.req = test2Python_req_ack_req;
    assign #0 test2Python_req_ack.data = test2Python_req_ack_data;
    assign #0 test2Python_req_ack_ack = test2Python_req_ack.ack;
    assign #0 test2Python_req_ack_rdata = test2Python_req_ack.rdata;

    // req_ack_if.src
    req_ack_if #(.data_t(p2s_message_st), .rdata_t(p2s_response_st)) dut2Python_req_ack();

    assign #0 dut2Python_req_ack_req = dut2Python_req_ack.req;
    assign #0 dut2Python_req_ack_data = dut2Python_req_ack.data;
    assign #0 dut2Python_req_ack.ack = dut2Python_req_ack_ack;
    assign #0 dut2Python_req_ack.rdata = dut2Python_req_ack_rdata;

    // push_ack_if.dst
    push_ack_if #(.data_t(p2s_message_st)) test_push_ack();

    assign #0 test_push_ack.push = test_push_ack_push;
    assign #0 test_push_ack.data = test_push_ack_data;
    assign #0 test_push_ack_ack = test_push_ack.ack;

    // pop_ack_if.dst
    pop_ack_if #(.rdata_t(p2s_response_st)) test_pop_ack();

    assign #0 test_pop_ack.pop = test_pop_ack_pop;
    assign #0 test_pop_ack_ack = test_pop_ack.ack;
    assign #0 test_pop_ack_rdata = test_pop_ack.rdata;

    // push_ack_if.src
    push_ack_if #(.data_t(p2s_message_st)) dut2Python_push_ack();

    assign #0 dut2Python_push_ack_push = dut2Python_push_ack.push;
    assign #0 dut2Python_push_ack_data = dut2Python_push_ack.data;
    assign #0 dut2Python_push_ack.ack = dut2Python_push_ack_ack;

    // pop_ack_if.src
    pop_ack_if #(.rdata_t(p2s_response_st)) dut2Python_pop_ack();

    assign #0 dut2Python_pop_ack_pop = dut2Python_pop_ack.pop;
    assign #0 dut2Python_pop_ack.ack = dut2Python_pop_ack_ack;
    assign #0 dut2Python_pop_ack.rdata = dut2Python_pop_ack_rdata;

    // notify_ack_if.dst
    notify_ack_if #() test_notify_ack();

    assign #0 test_notify_ack.notify = test_notify_ack_notify;
    assign #0 test_notify_ack_ack = test_notify_ack.ack;

    // notify_ack_if.src
    notify_ack_if #() dut2Python_notify_ack();

    assign #0 dut2Python_notify_ack_notify = dut2Python_notify_ack.notify;
    assign #0 dut2Python_notify_ack.ack = dut2Python_notify_ack_ack;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(p2s_message_st)) test_rdy_vld();

    assign #0 test_rdy_vld.vld = test_rdy_vld_vld;
    assign #0 test_rdy_vld.data = test_rdy_vld_data;
    assign #0 test_rdy_vld_rdy = test_rdy_vld.rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(p2s_message_st)) dut2Python_rdy_vld();

    assign #0 dut2Python_rdy_vld_vld = dut2Python_rdy_vld.vld;
    assign #0 dut2Python_rdy_vld_data = dut2Python_rdy_vld.data;
    assign #0 dut2Python_rdy_vld.rdy = dut2Python_rdy_vld_rdy;

    pySocket_dut dut (
        .test_req_ack(test_req_ack), // req_ack_if.dst
        .test2Python_req_ack(test2Python_req_ack), // req_ack_if.dst
        .dut2Python_req_ack(dut2Python_req_ack), // req_ack_if.src
        .test_push_ack(test_push_ack), // push_ack_if.dst
        .test_pop_ack(test_pop_ack), // pop_ack_if.dst
        .dut2Python_push_ack(dut2Python_push_ack), // push_ack_if.src
        .dut2Python_pop_ack(dut2Python_pop_ack), // pop_ack_if.src
        .test_notify_ack(test_notify_ack), // notify_ack_if.dst
        .dut2Python_notify_ack(dut2Python_notify_ack), // notify_ack_if.src
        .test_rdy_vld(test_rdy_vld), // rdy_vld_if.dst
        .dut2Python_rdy_vld(dut2Python_rdy_vld), // rdy_vld_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : dut_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _DUT_HDL_SV_WRAPPER_SV_GUARD_
