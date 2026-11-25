// Fails the run on the first X or Z at an apb port of an HDL wrapper.
// psel, penable and pready are always checked. psel qualifies the request,
// and pwrite qualifies pwdata, which a read leaves undefined. The completing
// cycle, psel && penable && pready, qualifies pslverr, and prdata on a read.
module apb_xcheck (
    input logic clk,
    input logic rst_n,
    apb_if      intf
);
`include "a2c_xcheck.svh"

    always @(negedge clk) begin
        if (xzCheckEnabled()) begin
            if ($isunknown(intf.psel)) begin
                xzFail("psel");
            end else if ($isunknown(intf.penable)) begin
                xzFail("penable");
            end else if ($isunknown(intf.pready)) begin
                xzFail("pready");
            end else if (intf.psel && $isunknown(intf.paddr)) begin
                xzFail("paddr");
            end else if (intf.psel && $isunknown(intf.pwrite)) begin
                xzFail("pwrite");
            end else if (intf.psel && intf.pwrite && $isunknown(intf.pwdata)) begin
                xzFail("pwdata");
            end else if (intf.psel && intf.penable && intf.pready && $isunknown(intf.pslverr)) begin
                xzFail("pslverr");
            end else if (intf.psel && intf.penable && intf.pready && !intf.pwrite
                         && $isunknown(intf.prdata)) begin
                xzFail("prdata");
            end
        end
    end

endmodule : apb_xcheck
