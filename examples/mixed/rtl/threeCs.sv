// GENERATED_CODE_PARAM --block=threeCs
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
module threeCs
    import mixedBlockC_package::*;
(
    rdy_vld_if.dst see0,
    rdy_vld_if.dst see1,
    rdy_vld_if.dst see2,
    input logic clk,
    input logic rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Instances

    blockC uBlockC0 (.see(see0), .clk(clk), .rst_n(rst_n));
    blockC uBlockC1 (.see(see1), .clk(clk), .rst_n(rst_n));
    blockC uBlockC2 (.see(see2), .clk(clk), .rst_n(rst_n));

// GENERATED_CODE_END

endmodule: threeCs