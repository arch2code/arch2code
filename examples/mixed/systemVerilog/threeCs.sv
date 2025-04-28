// GENERATED_CODE_PARAM --block=threeCs --parentModule
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: threeCs
module threeCs
// Generated Import package statement(s)
import mixedBlockC_package::*;
(
    rdy_vld_if.dst see0,
    rdy_vld_if.dst see1,
    rdy_vld_if.dst see2,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
blockC uBlockC0 (
    .see (see0),
    .clk (clk),
    .rst_n (rst_n)
);

blockC uBlockC1 (
    .see (see1),
    .clk (clk),
    .rst_n (rst_n)
);

blockC uBlockC2 (
    .see (see2),
    .clk (clk),
    .rst_n (rst_n)
);

endmodule // threeCs
// GENERATED_CODE_END
