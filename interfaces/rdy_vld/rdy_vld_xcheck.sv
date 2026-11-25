// Fails the run on the first X or Z at an rdy_vld port of an HDL wrapper.
// vld and rdy are always checked, data only while vld is high.
module rdy_vld_xcheck (
    input logic clk,
    input logic rst_n,
    rdy_vld_if  intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.vld)) begin
                xzFail("vld");
            end else if ($isunknown(intf.rdy)) begin
                xzFail("rdy");
            end else if (intf.vld && $isunknown(intf.data)) begin
                xzFail("data");
            end
        end
    end

endmodule : rdy_vld_xcheck
