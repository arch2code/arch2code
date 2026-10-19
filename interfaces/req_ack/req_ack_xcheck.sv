// Fails the run on the first X or Z at a req_ack port of an HDL wrapper.
// req and ack are always checked, data only while req is high and rdata only
// while ack is high.
module req_ack_xcheck (
    input logic clk,
    input logic rst_n,
    req_ack_if  intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.req)) begin
                xzFail("req");
            end else if ($isunknown(intf.ack)) begin
                xzFail("ack");
            end else if (intf.req && $isunknown(intf.data)) begin
                xzFail("data");
            end else if (intf.ack && $isunknown(intf.rdata)) begin
                xzFail("rdata");
            end
        end
    end

endmodule : req_ack_xcheck
