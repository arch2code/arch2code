// Fails the run on the first X or Z at an external_reg port of an HDL
// wrapper. write and rdata are always checked, wdata only while write is
// non-zero.
module external_reg_xcheck (
    input logic     clk,
    input logic     rst_n,
    external_reg_if intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.write)) begin
                xzFail("write");
            end else if ($isunknown(intf.rdata)) begin
                xzFail("rdata");
            end else if (intf.write != '0 && $isunknown(intf.wdata)) begin
                xzFail("wdata");
            end
        end
    end

endmodule : external_reg_xcheck
