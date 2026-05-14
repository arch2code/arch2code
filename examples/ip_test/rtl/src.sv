//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: src
module src
// Generated Import package statement(s)
import ipLeaf_package::*;
import src_package::*;
#(
    parameter OUT0_DATA_WIDTH,
    parameter OUT1_DATA_WIDTH
)
(
    push_ack_if.src out0,
    push_ack_if.src out1,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
ipLeaf #(.LEAF_DATA_WIDTH(4), .LEAF_MEM_DEPTH(4)) uLeaf (
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

    // One-shot stimulus: after reset, push a fixed value on each output
    // exactly once, then idle. The marker bit is asserted on both pushes
    // so the consumer can verify per-variant pack/unpack preserves the
    // bit positioned above the variant's data field. For out1 (70-bit
    // payload feeding IP_DATA_WIDTH=70) the upper-word constant 0x2A is
    // driven into bits [68:64] to prove the wide-packed bridge in the
    // model side preserves bits above 64 — at RTL this just exercises a
    // value that crosses the 64-bit boundary.
    `DFF_INST(logic, out0_done)
    `DFF_INST(logic, out1_done)

    always_comb begin
        n_out0_done = out0_done;
        out0.push = 1'b0;
        out0.data = '0;
        if (!out0_done) begin
            out0.push = 1'b1;
            out0.data.marker = 1'b1;
            out0.data.data = srcOut0DataT'('hA5);
            if (out0.ack) begin
                n_out0_done = 1'b1;
            end
        end
    end

    always_comb begin
        n_out1_done = out1_done;
        out1.push = 1'b0;
        out1.data = '0;
        if (!out1_done) begin
            out1.push = 1'b1;
            out1.data.marker = 1'b1;
            out1.data.data = (srcOut1DataT'('h2A) << 64) | srcOut1DataT'('h5A);
            if (out1.ack) begin
                n_out1_done = 1'b1;
            end
        end
    end

endmodule: src
