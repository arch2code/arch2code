//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: clkGen
module clkGen

(
    input clkRef, output clkDiv, input rstRef_n
);

    // Local clock/reset nets, driven by a child instance's output
    wire rstDivRaw_n;
    wire rstDivInt_n;

    // Default-domain aliases: the bare flop macros expand to clk / rst_n
    wire clk = clkRef;
    wire rst_n = rstRef_n;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
clkDivider uDivider (
    .clkRef (clkRef),
    .clkDiv (clkDiv),
    .clkDivBy2 (),
    .rstRef_n (rstRef_n),
    .rstDivRaw_n (rstDivRaw_n)
);

rstSync uRstSync (
    .clk (clkDiv),
    .rstIn_n (rstDivRaw_n),
    .rstOut_n (rstDivInt_n)
);

clkConsumer uConsumer (
    .clk (clkDiv),
    .rst_n (rstDivInt_n)
);

// GENERATED_CODE_END

// Checks on clkGen's internal reset and consumer, sampled on clkRef so they
// still fire if clkDiv stops.
`ifndef SYNTHESIS
import clkGen_package::*;
localparam int unsigned DIV_PERIOD = 2 * CLK_GEN_DIV_HALF_COUNT;   // clkRef cycles per clkDiv period
localparam int unsigned RST_RELEASE_LIMIT = 4 * DIV_PERIOD;
typedef logic [$bits(uConsumer.count)-1:0] consumer_count_t;
`DFF_INST(int unsigned, releaseCycles)
`DFF_INST(int unsigned, stallCycles)
`DFF_INST(consumer_count_t, lastCount)

always_comb begin
    n_lastCount = uConsumer.count;
    n_releaseCycles = releaseCycles;
    if (releaseCycles < RST_RELEASE_LIMIT) begin
        n_releaseCycles = releaseCycles + 1;
    end
    n_stallCycles = '0;
    if (rstDivInt_n && uConsumer.count == lastCount) begin
        n_stallCycles = stallCycles + 1;
    end
end

always_ff @(posedge clkRef) begin
    if (!rstRef_n) begin
        `qAssertFatal(!rstDivInt_n, "rstDivInt_n is not asserted while rstRef_n is asserted")
    end else begin
        `qAssertFatal(rstDivInt_n || releaseCycles < RST_RELEASE_LIMIT, "rstDivInt_n was not released after rstRef_n released")
        `qAssertFatal(stallCycles <= DIV_PERIOD, "uConsumer count stopped advancing after reset release")
    end
end
`endif

endmodule: clkGen
