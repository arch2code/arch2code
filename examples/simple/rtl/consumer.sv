//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: simple_consumer
module simple_consumer
// Generated Import package statement(s)
import simple_package::*;
(
    push_ack_if.dst tag0,
    push_ack_if.dst tag1,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // Accept every pushed tag in a single cycle and check its id against the
    // wrapping sequence the producer drives.
    `DFF_INST(tag, tag0_expected)
    `DFF_INST(tag, tag1_expected)

    assign tag0.ack = tag0.push;
    assign tag1.ack = tag1.push;

    always_comb begin
        n_tag0_expected = tag0_expected;
        if (tag0.push) begin
            n_tag0_expected = tag0_expected + 1'b1;
        end
    end

    always_comb begin
        n_tag1_expected = tag1_expected;
        if (tag1.push) begin
            n_tag1_expected = tag1_expected + 1'b1;
        end
    end

    // Checks are clock-sampled, not combinational. An always_comb assertion
    // re-evaluates on every settle, so it fires on the transient where the
    // expected counter has already advanced past a source-held data value -
    // which is what an SC push_ack BFM drives when this block is verilated on
    // its own. Sampling at the edge sees only consistent, pre-edge values.
    always_ff @(posedge clk) begin
        if (tag0.push) begin
            `qAssertFatal(tag0.data.tagId == tag0_expected, "tag0 data mismatch")
        end
        if (tag1.push) begin
            `qAssertFatal(tag1.data.tagId == tag1_expected, "tag1 data mismatch")
        end
    end

endmodule: simple_consumer
