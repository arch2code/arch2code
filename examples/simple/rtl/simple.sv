//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: simple
module simple
// Generated Import package statement(s)
import simple_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(tag_st)) tag0();
    push_ack_if #(.data_t(tag_st)) tag1();

// Instances
producer u_producer (
    .tag0 (tag0),
    .tag1 (tag1),
    .clk (clk),
    .rst_n (rst_n)
);

consumer u_consumer (
    .tag0 (tag0),
    .tag1 (tag1),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: simple
