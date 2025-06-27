// GENERATED_CODE_PARAM --block=blockC
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockC
module blockC
// Generated Import package statement(s)
import hierInclude_package::*;
import hierIncludeC_package::*;
(
    rdy_vld_if.dst eh2c,
    req_ack_if.dst b2C,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    rdy_vld_if #(.data_t(cSt)) cx2y();
    rdy_vld_if #(.data_t(cSt)) cx2z();

// Instances
blockCX uBlockCX (
    .anInterface (eh2c),
    .b2C (b2C),
    .cx2y (cx2y),
    .cx2z (cx2z),
    .clk (clk),
    .rst_n (rst_n)
);

blockCY uBlockCY (
    .x (cx2y),
    .clk (clk),
    .rst_n (rst_n)
);

blockCZ uBlockCZ (
    .x (cx2z),
    .clk (clk),
    .rst_n (rst_n)
);


// GENERATED_CODE_END

endmodule: blockC