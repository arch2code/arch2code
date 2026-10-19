// Fails the run on the first X or Z at an axi_write port of an HDL wrapper.
// awvalid, awready, wvalid, wready, bvalid and bready are always checked, the
// AW signals while awvalid is high, the W signals while wvalid is high and the
// B signals while bvalid is high. awid, awuser, wid, wuser, bid and buser are
// typed by optional payloads, so each is checked only under its CHECK_
// parameter, which the wrapper sets for a port that binds the payload. A port
// that leaves a payload unbound, id_t included, gets no check on its signals
// by design. The defaults are off, so a checker instantiated without the
// parameters never fails on one.
module axi_write_xcheck #(
    parameter bit CHECK_AWID   = 1'b0,
    parameter bit CHECK_AWUSER = 1'b0,
    parameter bit CHECK_WID    = 1'b0,
    parameter bit CHECK_WUSER  = 1'b0,
    parameter bit CHECK_BID    = 1'b0,
    parameter bit CHECK_BUSER  = 1'b0
) (
    input logic clk,
    input logic rst_n,
    axi_write_if intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.awvalid)) begin
                xzFail("awvalid");
            end else if ($isunknown(intf.awready)) begin
                xzFail("awready");
            end else if ($isunknown(intf.wvalid)) begin
                xzFail("wvalid");
            end else if ($isunknown(intf.wready)) begin
                xzFail("wready");
            end else if ($isunknown(intf.bvalid)) begin
                xzFail("bvalid");
            end else if ($isunknown(intf.bready)) begin
                xzFail("bready");
            end else if (intf.awvalid && $isunknown(intf.awaddr)) begin
                xzFail("awaddr");
            end else if (intf.awvalid && $isunknown(intf.awlen)) begin
                xzFail("awlen");
            end else if (intf.awvalid && $isunknown(intf.awsize)) begin
                xzFail("awsize");
            end else if (intf.awvalid && $isunknown(intf.awburst)) begin
                xzFail("awburst");
            end else if (intf.awvalid && CHECK_AWID && $isunknown(intf.awid)) begin
                xzFail("awid");
            end else if (intf.awvalid && CHECK_AWUSER && $isunknown(intf.awuser)) begin
                xzFail("awuser");
            end else if (intf.wvalid && $isunknown(intf.wdata)) begin
                xzFail("wdata");
            end else if (intf.wvalid && $isunknown(intf.wstrb)) begin
                xzFail("wstrb");
            end else if (intf.wvalid && $isunknown(intf.wlast)) begin
                xzFail("wlast");
            end else if (intf.wvalid && CHECK_WID && $isunknown(intf.wid)) begin
                xzFail("wid");
            end else if (intf.wvalid && CHECK_WUSER && $isunknown(intf.wuser)) begin
                xzFail("wuser");
            end else if (intf.bvalid && $isunknown(intf.bresp)) begin
                xzFail("bresp");
            end else if (intf.bvalid && CHECK_BID && $isunknown(intf.bid)) begin
                xzFail("bid");
            end else if (intf.bvalid && CHECK_BUSER && $isunknown(intf.buser)) begin
                xzFail("buser");
            end
        end
    end

endmodule : axi_write_xcheck
