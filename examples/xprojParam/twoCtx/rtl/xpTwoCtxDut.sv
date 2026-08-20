//

// GENERATED_CODE_PARAM --block=xpTwoCtxDut
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xpTwoCtx_xpTwoCtxDut
module xpTwoCtx_xpTwoCtxDut
// Generated Import package statement(s)
import xpTwoCtx_package::*;
import xpDpLeaf_package::*;
#(
    parameter DP_WIDTH,
    parameter TC_GAIN
)
(
    push_ack_if.dst in,
    push_ack_if.src valOut,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    localparam TC_GAIN_X2 = TC_GAIN * 2; //Derived from this context's own knob
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

endmodule: xpTwoCtx_xpTwoCtxDut
