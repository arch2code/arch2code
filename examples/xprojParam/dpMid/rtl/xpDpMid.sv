//

// GENERATED_CODE_PARAM --block=xpDpMid
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xpDpMid
module xpDpMid
// Generated Import package statement(s)
import xpDpLeaf_package::*;
#(
    parameter DP_WIDTH,
    parameter MID_ALGO
)
(
    push_ack_if.dst midIn,
    push_ack_if.src midOut,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    typedef logic[DP_WIDTH-1:0] dpPixelT; //Parameterizable pixel word
    typedef struct packed {
        dpTagT tag; //Sample sequence tag
        dpAlgoT algo; //DP_ALGO the leaf instance resolved
        dpPixelT data; //Parameterizable pixel payload
        dpMarkT mark; //Trailing marker
    } dpSt;

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(dpSt)) out();

// Instances
xpDpLeaf #(.DP_ALGO(MID_ALGO), .DP_WIDTH(DP_WIDTH)) uLeafA (
    .in (midIn),
    .out (out),
    .clk (clk),
    .rst_n (rst_n)
);

xpDpLeaf #(.DP_ALGO(MID_ALGO), .DP_WIDTH(DP_WIDTH)) uLeafB (
    .out (midOut),
    .in (out),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: xpDpMid
