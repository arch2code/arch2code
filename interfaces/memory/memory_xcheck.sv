// Fails the run on the first X or Z at a memory port of an HDL wrapper.
// enable is always checked, addr and wr_en while enable is high, and
// write_data on a write. read_data is checked on the clock after a read, when
// it carries that read's word. An X or Z word fails unless the port's next
// access writes the same address: a read-modify-write of a word never
// written, such as a register update's pre-read, may return the memory's
// power-on X, and that write replaces it. A read whose X word no access
// follows fails at the end of the run. A reset drops the pending word.
module memory_xcheck (
    input logic clk,
    input logic rst_n,
    memory_if   intf
);
`include "a2c_xcheck.svh"

    // The previous sample saw a read of readAddr, so read_data now holds its
    // word.
    bit        readPending;
    bit [63:0] readAddr;
    // A read of xAddr returned X or Z, and no access has followed it yet.
    bit        xPending;
    bit [63:0] xAddr;

    always @(negedge clk) begin
        if (!xzCheckEnabled()) begin
            readPending = 1'b0;
            xPending = 1'b0;
        end else begin
            if ($isunknown(intf.enable)) begin
                xzFail("enable");
            end else if (intf.enable && $isunknown(intf.addr)) begin
                xzFail("addr");
            end else if (intf.enable && $isunknown(intf.wr_en)) begin
                xzFail("wr_en");
            end else if (intf.enable && intf.wr_en && $isunknown(intf.write_data)) begin
                xzFail("write_data");
            end
            if (readPending && $isunknown(intf.read_data)) begin
                xPending = 1'b1;
                xAddr = readAddr;
            end
            if (xPending && intf.enable === 1'b1 && !xzReported) begin
                xPending = 1'b0;
                if (!(intf.wr_en === 1'b1 && 64'(intf.addr) === xAddr)) begin
                    xzFail("read_data");
                end
            end
            readPending = intf.enable === 1'b1 && intf.wr_en === 1'b0;
            readAddr = 64'(intf.addr);
        end
    end

    // Reports a pending X word. The end of the run calls it; a test may call
    // it earlier, since a second call finds nothing pending.
    function automatic void xzEndOfRun();
        if (xPending && xzCheckEnabled()) begin
            xPending = 1'b0;
            xzFail("read_data");
        end
    endfunction

    final xzEndOfRun();

endmodule : memory_xcheck
