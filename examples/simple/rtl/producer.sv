//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: simple_producer
module simple_producer
// Generated Import package statement(s)
import simple_package::*;
(
    push_ack_if.src tag0,
    push_ack_if.src tag1,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // One burst per channel, tag ids wrapping at NUM_TAGS, matching the sequence
    // the consumer checks.
    localparam int unsigned TAG_BURST = 256;

    // push comes from state and reset only: the destination acks combinationally
    // off push, so deriving push where ack is read closes a comb loop.
    `DFF_INST(logic [$clog2(TAG_BURST+1)-1:0], tag0_sent)
    `DFF_INST(tag, tag0_tagId)
    logic tag0_active;

    assign tag0_active = rst_n && (32'(tag0_sent) < TAG_BURST);
    assign tag0.push = tag0_active;
    assign tag0.data.tagId = tag0_tagId;

    always_comb begin
        n_tag0_sent = tag0_sent;
        n_tag0_tagId = tag0_tagId;
        if (tag0_active && tag0.ack) begin
            n_tag0_sent = tag0_sent + 1'b1;
            n_tag0_tagId = tag0_tagId + 1'b1;
        end
    end

    `DFF_INST(logic [$clog2(TAG_BURST+1)-1:0], tag1_sent)
    `DFF_INST(tag, tag1_tagId)
    logic tag1_active;

    assign tag1_active = rst_n && (32'(tag1_sent) < TAG_BURST);
    assign tag1.push = tag1_active;
    assign tag1.data.tagId = tag1_tagId;

    always_comb begin
        n_tag1_sent = tag1_sent;
        n_tag1_tagId = tag1_tagId;
        if (tag1_active && tag1.ack) begin
            n_tag1_sent = tag1_sent + 1'b1;
            n_tag1_tagId = tag1_tagId + 1'b1;
        end
    end

endmodule: simple_producer
