// Fails the run on the first X or Z at a notify_ack port of an HDL wrapper.
// notify and ack are always checked.
module notify_ack_xcheck (
    input logic   clk,
    input logic   rst_n,
    notify_ack_if intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.notify)) begin
                xzFail("notify");
            end else if ($isunknown(intf.ack)) begin
                xzFail("ack");
            end
        end
    end

endmodule : notify_ack_xcheck
