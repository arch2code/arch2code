//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkDivider
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: clkGen_clkDivider
module clkGen_clkDivider

(
    input clkRef, output clkDiv, clkDivBy2, input rstRef_n, output rstDivRaw_n
);

    // Default-domain aliases: the bare flop macros expand to clk / rst_n
    wire clk = clkRef;
    wire rst_n = rstRef_n;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

// Free-running divider, reset by its own reference reset (rst_n = rstRef_n,
// allowed: it is this block's own input, not an invented crossing) rather
// than left with no reset at all: DFFNR_INST's flop carries no initial
// value in 4-state simulation and would hold X forever. Toggles clkDiv every
// DIV_HALF_COUNT clkRef cycles, resuming from reset release (R23: the domain
// runs at a defined rate from then on). clkDivBy2 is a second tap on the
// same edge, left unused by every instance in this fixture (spec §4.5 "An
// output bound to `~` is left unconnected").
localparam int unsigned DIV_HALF_COUNT = 4;
typedef logic [$clog2(DIV_HALF_COUNT)-1:0] div_count_t;

`DFFR_INST(div_count_t, divCount, '0)
`DFFR_INST(logic, clkDivReg, 1'b0)

always_comb begin
    n_divCount = divCount + 1'b1;
    n_clkDivReg = clkDivReg;
    if (divCount == div_count_t'(DIV_HALF_COUNT - 1)) begin
        n_divCount = '0;
        n_clkDivReg = ~clkDivReg;
    end
end

assign clkDiv = clkDivReg;
assign clkDivBy2 = clkDivReg;

// rstDivRaw_n: the raw, un-synchronised reset of the clkDiv domain, asserted
// whenever rst_n (rstRef_n) is asserted (spec §4.5 R22: the clock's supplier
// also supplies a raw reset of the domain). uRstSync (a separate reset
// synchroniser block) takes this in as its asynchronous input and releases
// it synchronously to clkDiv; the divider itself performs no
// synchronisation.
assign rstDivRaw_n = rst_n;

endmodule: clkGen_clkDivider
