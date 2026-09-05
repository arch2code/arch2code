//

// GENERATED_CODE_PARAM --block=xviLeaf
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xviLeaf
module xviLeaf
// Generated Import package statement(s)
import xviLeaf_package::*;
#(
    parameter XVI_WIDTH,
    parameter XVI_GAIN
)
(
    push_ack_if.dst in,
    push_ack_if.src out,
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

    xviSt inSample;
    xviSt outSample;

    // Combinational gain stage: scale the payload, pass the tag and the
    // push/ack handshake straight through.
    always_comb begin
        inSample = xviSt'(in.data);
        outSample.tag = inSample.tag;
        outSample.data = xviPixelT'(inSample.data * XVI_GAIN);
    end

    assign out.push = in.push;
    assign out.data = outSample;
    assign in.ack = out.ack;

endmodule: xviLeaf
