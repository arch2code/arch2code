//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSlowTick
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: twoClk_twoClkSlowTick
module twoClk_twoClkSlowTick
// Generated Import package statement(s)
import twoClkIp_package::*;
(
    push_ack_if.src out,
    input clkSlow, rstSlow_n
);

    // Default-domain aliases: the bare flop macros expand to clk / rst_n
    wire clk = clkSlow;
    wire rst_n = rstSlow_n;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    import twoClk_package::*;

    // cyc is free-running and never stalled by the handshake, so the push
    // cadence is exactly TWO_CLK_TICK_DIV clkSlow cycles as long as the ack
    // returns within that many cycles; a slower ack drops a slot, which the
    // model sink's cadence assert reports.
    `DFF_INST(logic [$clog2(TWO_CLK_TICK_DIV)-1:0], cyc)
    `DFF_INST(twoClkDataT, tick)
    `DFF_INST(logic, pending)

    always_comb begin
        n_cyc = cyc + 1'b1;
        n_pending = pending;
        n_tick = tick;

        if (32'(cyc) == (TWO_CLK_TICK_DIV - 1)) begin
            n_cyc = '0;
            n_pending = 1'b1;
        end

        out.push = pending;
        out.data.data = tick;
        if (out.push && out.ack) begin
            n_pending = 1'b0;
            n_tick = tick + 1'b1;
        end
    end

endmodule: twoClk_twoClkSlowTick
