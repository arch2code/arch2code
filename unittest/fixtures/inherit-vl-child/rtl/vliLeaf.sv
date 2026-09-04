//

// GENERATED_CODE_PARAM --block=vliLeaf
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: vlInh_vliLeaf
module vlInh_vliLeaf
// Generated Import package statement(s)
import vlInh_vliCont_package::*;
#(
    parameter VLI_ALGO,
    parameter VLI_WIDTH
)
(
    push_ack_if.src out,
    push_ack_if.dst in,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    typedef logic[VLI_WIDTH-1:0] vliPixelT; //Parameterizable pixel word
    typedef struct packed {
        vliTagT tag; //Sample sequence tag
        vliAlgoT algo; //VLI_ALGO the leaf instance resolved
        vliWidT wid; //VLI_WIDTH the leaf instance resolved
        vliPixelT data; //Parameterizable pixel payload
        vliMarkT mark; //Trailing marker
    } vliSt;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // Combinational forwarder. The payload passes straight through with `algo`
    // and `wid` replaced by the parameters this instance elaborated at, which is
    // what the checker reads back. The handshake is a wire, so the leaf adds no
    // latency and both BFMs see the protocol they drove.
    vliSt inSt;
    vliSt fwd;

    always_comb begin
        inSt     = vliSt'(in.data);
        fwd      = inSt;
        fwd.algo = vliAlgoT'(VLI_ALGO);
        fwd.wid  = vliWidT'(VLI_WIDTH);
        // Arithmetic on the whole payload, wrapping at VLI_WIDTH. The driver
        // sets the top payload bit, so a module elaborated at a narrower width
        // has already lost it and wraps sooner; the checker's absolute
        // expectation then misses. A pass-through would carry the loss unseen.
        fwd.data = vliPixelT'(inSt.data + (1 << (VLI_WIDTH - 3)));
    end

    assign out.push = in.push;
    assign out.data = fwd;
    assign in.ack   = out.ack;

endmodule: vlInh_vliLeaf
