// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockB
module blockB
// Generated Import package statement(s)
import hierIncludeB_package::*;
import hierInclude_package::*;
(
    rdy_vld_if.dst eh2b,
    req_ack_if.src b2C,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    rdy_vld_if #(.data_t(bSt)) bx2y();
    rdy_vld_if #(.data_t(bSt)) bx2z();

// Instances
blockBX uBlockBX (
    .anInterface (eh2b),
    .b2C (b2C),
    .bx2y (bx2y),
    .bx2z (bx2z),
    .clk (clk),
    .rst_n (rst_n)
);

blockBY uBlockBY (
    .x (bx2y),
    .clk (clk),
    .rst_n (rst_n)
);

blockBZ uBlockBZ (
    .x (bx2z),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: blockB