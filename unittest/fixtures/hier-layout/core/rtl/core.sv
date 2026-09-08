//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=core
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: hier_core
module hier_core
// Generated Import package statement(s)
import hier_core_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(dat_st)) dOut_0();
    push_ack_if #(.data_t(dat_st)) dOut_1();
    push_ack_if #(.data_t(dat_st)) dOut_2();

// Instances
hier_gen u_gen (
    .dOut (dOut_0),
    .dIn (dOut_2),
    .clk (clk),
    .rst_n (rst_n)
);

hier_leaf u_leaf0 (
    .dIn (dOut_0),
    .dOut (dOut_1),
    .clk (clk),
    .rst_n (rst_n)
);

hier_leaf u_leaf1 (
    .dIn (dOut_1),
    .dOut (dOut_2),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: core
