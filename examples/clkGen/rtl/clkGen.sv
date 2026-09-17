//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: clkGen
module clkGen

(
    input clkRef, output clkDiv, input rstRef_n
);

    // Default-domain aliases: the bare flop macros expand to clk / rst_n
    wire clk = clkRef;
    wire rst_n = rstRef_n;

    // Local clock/reset nets, driven by a child instance's output
    wire rstDivRaw_n;
    wire rstDivInt_n;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
clkGen_clkDivider uDivider (
    .clkRef (clkRef),
    .clkDiv (clkDiv),
    .clkDivBy2 (),
    .rstRef_n (rstRef_n),
    .rstDivRaw_n (rstDivRaw_n)
);

clkGen_rstSync uRstSync (
    .clk (clkDiv),
    .rstIn_n (rstDivRaw_n),
    .rstOut_n (rstDivInt_n)
);

clkGen_clkConsumer uConsumer (
    .clk (clkDiv),
    .rst_n (rstDivInt_n)
);

// GENERATED_CODE_END

endmodule: clkGen
