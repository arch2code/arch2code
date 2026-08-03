// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: hierInclude_blockB
module hierInclude_blockB
// Generated Import package statement(s)
import hierInclude_hierIncludeB_package::*;
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
hierInclude_blockBX uBlockBX (
    .anInterface (eh2b),
    .b2C (b2C),
    .bx2y (bx2y),
    .bx2z (bx2z),
    .clk (clk),
    .rst_n (rst_n)
);

hierInclude_blockBY uBlockBY (
    .x (bx2y),
    .clk (clk),
    .rst_n (rst_n)
);

hierInclude_blockBZ uBlockBZ (
    .x (bx2z),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: hierInclude_blockB