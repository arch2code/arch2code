// Fails the run on the first X or Z at a raw port of an HDL wrapper. raw has
// no qualifier, so data is checked on every cycle.
module raw_xcheck (
    input logic clk,
    input logic rst_n,
    raw_if      intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled() && $isunknown(intf.data)) begin
            xzFail("data");
        end
    end

endmodule : raw_xcheck
