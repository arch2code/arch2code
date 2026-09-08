//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkIpSrc
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: twoClkIp_twoClkIpSrc
module twoClkIp_twoClkIpSrc
// Generated Import package statement(s)
import twoClkIp_package::*;
(
    push_ack_if.src out,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // One-shot burst mirroring the model, then idle. The sequence is the
    // fixture's stimulus contract, declared once in twoClkIp.yaml constants:.
    `DFF_INST(logic[$clog2(TWO_CLK_BURST_WORDS+1)-1:0], sent)

    always_comb begin
        n_sent = sent;
        out.push = 1'b0;
        out.data = '0;
        if (32'(sent) < TWO_CLK_BURST_WORDS) begin
            out.push = 1'b1;
            out.data.data = twoClkDataT'(TWO_CLK_BURST_BASE + 32'(sent));
            if (out.ack) begin
                n_sent = sent + 1'b1;
            end
        end
    end

endmodule: twoClkIp_twoClkIpSrc
