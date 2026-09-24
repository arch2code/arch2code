//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=rstSync
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: clkGen_rstSync
module clkGen_rstSync

(
    input clk, rstIn_n, output rstOut_n
);

    // Default-domain aliases: the bare flop macros expand to clk / rst_n
    wire rst_n = rstOut_n;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

// Reset synchroniser: asynchronous assert on rstIn_n, synchronous release
// into the clk domain, so the domain resets even while clk is stopped.
// Explicitly asynchronous flops written outside the macro library, since the
// macro-selected reset style is not what this block's own output reset is -
// it IS the reset, produced here rather than consumed.
logic rstSync1_n, rstSync2_n;
always_ff @(posedge clk or negedge rstIn_n) begin
    if (!rstIn_n) begin
        rstSync1_n <= 1'b0;
        rstSync2_n <= 1'b0;
    end else begin
        rstSync1_n <= 1'b1;
        rstSync2_n <= rstSync1_n;
    end
end

assign rstOut_n = rstSync2_n;

endmodule: clkGen_rstSync
