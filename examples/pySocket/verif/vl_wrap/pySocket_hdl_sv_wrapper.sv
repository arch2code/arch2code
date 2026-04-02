`ifndef _PYSOCKET_HDL_SV_WRAPPER_SV_GUARD_
`define _PYSOCKET_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module pySocket_hdl_sv_wrapper
    // Generated Import package statement(s)
    import pySocket_package::*;
(
    // req_ack_if.src
    output bit test_req_ack_req,
    output bit [63:0] test_req_ack_data,
    input bit test_req_ack_ack,
    input bit [31:0] test_req_ack_rdata,

    input clk,
    input rst_n
);
    // req_ack_if.src
    req_ack_if #(.data_t(p2s_message_st), .rdata_t(p2s_response_st)) test_req_ack();

    assign #0 test_req_ack_req = test_req_ack.req;
    assign #0 test_req_ack_data = test_req_ack.data;
    assign #0 test_req_ack.ack = test_req_ack_ack;
    assign #0 test_req_ack.rdata = test_req_ack_rdata;

    pySocket dut (
        .test_req_ack(test_req_ack), // req_ack_if.src
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
