//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSink
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: twoClk_twoClkSink
module twoClk_twoClkSink
// Generated Import package statement(s)
import twoClkIp_package::*;
(
    push_ack_if.dst in,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // Mirrors the model: accept every pushed word in one cycle. lastData and
    // received are kept only so the handshake is observable in a waveform.
    `DFF_INST(logic[$clog2(TWO_CLK_BURST_WORDS+1)-1:0], received)
    `DFF_INST(twoClkDataT, lastData)

    always_comb begin
        n_received = received;
        n_lastData = lastData;
        in.ack = 1'b0;
        if (in.push) begin
            in.ack = 1'b1;
            n_lastData = in.data.data;
            if (32'(received) < TWO_CLK_BURST_WORDS) begin
                n_received = received + 1'b1;
            end
        end
    end

endmodule: twoClk_twoClkSink
