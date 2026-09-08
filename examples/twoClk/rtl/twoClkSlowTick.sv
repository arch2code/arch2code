//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSlowTick
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: twoClk_twoClkSlowTick
module twoClk_twoClkSlowTick

(
    input clkSlow, rstSlow_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // This block's clock port is clkSlow, not clk, so the bare `DFF_INST
    // (which expands to the literal clk) cannot be used here.
    `DFF_INST_CLK(clkSlow, logic [7:0], tick)

    always_comb begin
        n_tick = tick + 1'b1;
    end

endmodule: twoClk_twoClkSlowTick
