//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: src
module src
// Generated Import package statement(s)
import ip_package::*;
(
    push_ack_if.src out0,
    push_ack_if.src out1,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // One-shot stimulus: after reset, push a fixed value on each output
    // exactly once, then idle. Each output is independent so they can ack
    // in any order.
    `DFF_INST(logic, out0_done)
    `DFF_INST(logic, out1_done)

    always_comb begin
        n_out0_done = out0_done;
        out0.push = 1'b0;
        out0.data = '0;
        if (!out0_done) begin
            out0.push = 1'b1;
            out0.data.data = ipDataT'('hA5);
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
            out1.data.data = ipDataT'('h5A);
            if (out1.ack) begin
                n_out1_done = 1'b1;
            end
        end
    end

endmodule: src
