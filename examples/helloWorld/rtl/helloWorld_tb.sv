//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: helloWorld
module helloWorld
// Generated Import package statement(s)
import helloWorldTop_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    rdy_vld_if #(.data_t(data_st)) test_rdy_vld();
    req_ack_if #(.data_t(data_st), .rdata_t(data_st)) test_req_ack();
    push_ack_if #(.data_t(data_st)) test_push_ack();
    pop_ack_if #(.rdata_t(data_st)) test_pop_ack();

// Instances
producer uProducer (
    .test_rdy_vld (test_rdy_vld),
    .test_req_ack (test_req_ack),
    .test_push_ack (test_push_ack),
    .test_pop_ack (test_pop_ack),
    .clk (clk),
    .rst_n (rst_n)
);

consumer uConsumer (
    .test_rdy_vld (test_rdy_vld),
    .test_req_ack (test_req_ack),
    .test_push_ack (test_push_ack),
    .test_pop_ack (test_pop_ack),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: helloWorld
