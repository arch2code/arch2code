// Fails the run on the first X or Z at a status port of an HDL wrapper.
// status has no qualifier, so data is checked on every cycle.
module status_xcheck (
    input logic clk,
    input logic rst_n,
    status_if   intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled() && $isunknown(intf.data)) begin
            xzFail("data");
        end
    end

endmodule : status_xcheck
