// Fails the run on the first X or Z at a pop_ack port of an HDL wrapper.
// pop and ack are always checked, rdata only while ack is high.
module pop_ack_xcheck (
    input logic clk,
    input logic rst_n,
    pop_ack_if  intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.pop)) begin
                xzFail("pop");
            end else if ($isunknown(intf.ack)) begin
                xzFail("ack");
            end else if (intf.ack && $isunknown(intf.rdata)) begin
                xzFail("rdata");
            end
        end
    end

endmodule : pop_ack_xcheck
