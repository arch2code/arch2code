//

// GENERATED_CODE_PARAM --block=xpDpLeaf
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xpDpLeaf
module xpDpLeaf
// Generated Import package statement(s)
import xpDpLeaf_package::*;
#(
    parameter DP_ALGO,
    parameter DP_WIDTH
)
(
    push_ack_if.dst in,
    push_ack_if.src out,
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

// Instances
// GENERATED_CODE_END

endmodule: xpDpLeaf
