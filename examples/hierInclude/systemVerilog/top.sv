// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: top
module top
// Generated Import package statement(s)
import hierInclude_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    rdy_vld_if #(.data_t(aSt)) anInterfaceB();
    rdy_vld_if #(.data_t(aSt)) anInterfaceC();
    req_ack_if #(.data_t(anotherSt), .rdata_t(yetAnotherSt)) b2C();

// Instances
blockA uBlockA (
    .anInterfaceB (anInterfaceB),
    .anInterfaceC (anInterfaceC),
    .clk (clk),
    .rst_n (rst_n)
);

blockB uBlockB (
    .eh2b (anInterfaceB),
    .b2C (b2C),
    .clk (clk),
    .rst_n (rst_n)
);

blockC uBlockC (
    .eh2c (anInterfaceC),
    .b2C (b2C),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: top