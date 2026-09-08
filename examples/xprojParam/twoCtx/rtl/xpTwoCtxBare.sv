//

// GENERATED_CODE_PARAM --block=xpTwoCtxBare
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xpTwoCtx_xpTwoCtxBare
module xpTwoCtx_xpTwoCtxBare
// Generated Import package statement(s)
import xpDpLeaf_package::*;
import xpTwoCtx_package::*;
#(
    parameter TC_GAIN,
    parameter DP_WIDTH
)
(
    push_ack_if.dst litIn,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    localparam TC_GAIN_X2 = TC_GAIN * 2; //Derived from this context's own knob
    localparam DP_WIDTH_X2 = DP_WIDTH * 2; //Derived from the included file's knob
    typedef logic[DP_WIDTH-1:0] dpPixelT; //Parameterizable pixel word
    typedef logic[TC_GAIN-1:0] tcValT; //Parameterizable value word sized by this file's knob
    typedef struct packed {
        dpTagT tag; //Sample sequence tag
        dpAlgoT algo; //DP_ALGO the leaf instance resolved
        dpPixelT data; //Parameterizable pixel payload
        dpMarkT mark; //Trailing marker
    } dpSt;
    typedef struct packed {
        tcTagT tag; //Sample tag
        tcValT val; //Parameterizable payload sized by TC_GAIN
    } tcSt;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

endmodule: xpTwoCtx_xpTwoCtxBare
