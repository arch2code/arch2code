//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkConsumer
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: clkGen_clkConsumer
module clkGen_clkConsumer

(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

// Free-running counter on the clock it is handed (clkDiv, at the container):
// a stopped clkDiv leaves it unchanged, and held at 0 while rst_n is
// asserted, both observable in a waveform (R23).
typedef logic [7:0] count_t;
`DFFR_INST(count_t, count, '0)

always_comb begin
    n_count = count + 1'b1;
end

endmodule: clkGen_clkConsumer
