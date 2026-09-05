//

// GENERATED_CODE_PARAM --block=xviSnk
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xviMid_xviSnk
module xviMid_xviSnk
// Generated Import package statement(s)
import xviLeaf_package::*;
#(
    parameter XVI_WIDTH
)
(
    push_ack_if.dst in,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    typedef logic[XVI_WIDTH-1:0] xviPixelT; //Parameterizable pixel word
    typedef struct packed {
        xviTagT tag; //Sample sequence tag
        xviPixelT data; //Parameterizable pixel payload
    } xviSt;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

endmodule: xviMid_xviSnk
