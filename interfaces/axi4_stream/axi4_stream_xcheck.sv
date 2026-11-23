// Fails the run on the first X or Z at an axi4_stream port of an HDL wrapper.
// tvalid and tready are always checked, the other signals only while tvalid
// is high. tuser is checked only under CHECK_TUSER, which the wrapper sets
// for a port that binds a TUSER type: an unbound tuser is an undriven
// placeholder. The default is off, so a checker instantiated without the
// parameter never fails on a placeholder.
module axi4_stream_xcheck #(
    parameter bit CHECK_TUSER = 1'b0
) (
    input logic    clk,
    input logic    rst_n,
    axi4_stream_if intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.tvalid)) begin
                xzFail("tvalid");
            end else if ($isunknown(intf.tready)) begin
                xzFail("tready");
            end else if (intf.tvalid) begin
                if ($isunknown(intf.tdata)) begin
                    xzFail("tdata");
                end else if ($isunknown(intf.tstrb)) begin
                    xzFail("tstrb");
                end else if ($isunknown(intf.tkeep)) begin
                    xzFail("tkeep");
                end else if ($isunknown(intf.tlast)) begin
                    xzFail("tlast");
                end else if ($isunknown(intf.tid)) begin
                    xzFail("tid");
                end else if ($isunknown(intf.tdest)) begin
                    xzFail("tdest");
                end else if (CHECK_TUSER && $isunknown(intf.tuser)) begin
                    xzFail("tuser");
                end
            end
        end
    end

endmodule : axi4_stream_xcheck
