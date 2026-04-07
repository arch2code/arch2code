`ifndef _DUT_HDL_SV_WRAPPER_SV_GUARD_
`define _DUT_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module dut_hdl_sv_wrapper
    // Generated Import package statement(s)
    import pySocket_package::*;
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

    dut dut (
        .test_req_ack(test_req_ack), // req_ack_if.dst
        .test2Python_req_ack(test2Python_req_ack), // req_ack_if.dst
        .dut2Python_req_ack(dut2Python_req_ack), // req_ack_if.src
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
