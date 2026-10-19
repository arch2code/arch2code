// Fails the run on the first X or Z at an axi_read port of an HDL wrapper.
// arvalid, arready, rvalid and rready are always checked, the AR signals
// while arvalid is high and the R signals while rvalid is high. arid, aruser,
// rid and ruser are typed by optional payloads, so each is checked only under
// its CHECK_ parameter, which the wrapper sets for a port that binds the
// payload. A port that leaves a payload unbound, id_t included, gets no check
// on its signals by design. The defaults are off, so a checker instantiated
// without the parameters never fails on one.
module axi_read_xcheck #(
    parameter bit CHECK_ARID   = 1'b0,
    parameter bit CHECK_ARUSER = 1'b0,
    parameter bit CHECK_RID    = 1'b0,
    parameter bit CHECK_RUSER  = 1'b0
) (
    input logic clk,
    input logic rst_n,
    axi_read_if intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.arvalid)) begin
                xzFail("arvalid");
            end else if ($isunknown(intf.arready)) begin
                xzFail("arready");
            end else if ($isunknown(intf.rvalid)) begin
                xzFail("rvalid");
            end else if ($isunknown(intf.rready)) begin
                xzFail("rready");
            end else if (intf.arvalid && $isunknown(intf.araddr)) begin
                xzFail("araddr");
            end else if (intf.arvalid && $isunknown(intf.arlen)) begin
                xzFail("arlen");
            end else if (intf.arvalid && $isunknown(intf.arsize)) begin
                xzFail("arsize");
            end else if (intf.arvalid && $isunknown(intf.arburst)) begin
                xzFail("arburst");
            end else if (intf.arvalid && CHECK_ARID && $isunknown(intf.arid)) begin
                xzFail("arid");
            end else if (intf.arvalid && CHECK_ARUSER && $isunknown(intf.aruser)) begin
                xzFail("aruser");
            end else if (intf.rvalid && $isunknown(intf.rdata)) begin
                xzFail("rdata");
            end else if (intf.rvalid && $isunknown(intf.rresp)) begin
                xzFail("rresp");
            end else if (intf.rvalid && $isunknown(intf.rlast)) begin
                xzFail("rlast");
            end else if (intf.rvalid && CHECK_RID && $isunknown(intf.rid)) begin
                xzFail("rid");
            end else if (intf.rvalid && CHECK_RUSER && $isunknown(intf.ruser)) begin
                xzFail("ruser");
            end
        end
    end

endmodule : axi_read_xcheck
