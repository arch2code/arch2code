// Fails the run on the first X or Z at a push_ack port of an HDL wrapper.
// push and ack are always checked, data only while push is high.
module push_ack_xcheck (
    input logic clk,
    input logic rst_n,
    push_ack_if intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.push)) begin
                xzFail("push");
            end else if ($isunknown(intf.ack)) begin
                xzFail("ack");
            end else if (intf.push && $isunknown(intf.data)) begin
                xzFail("data");
            end
        end
    end

endmodule : push_ack_xcheck
