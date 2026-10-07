// Self-checking simulation testbench for common/systemVerilog/memory_dp_2clk.sv
// and memory_dp.sv, built standalone by unittest/test_memory_dp_ports_sim.py
// with Verilator `--binary --timing`. Prints TB_PASS on success; any mismatch
// ends in $fatal.
//
// PORTA_READ_ONLY and PORTB_WRITE_ONLY remove a write or read path so the
// memory maps to one block RAM. Neither may change what the remaining paths
// store or return.
//
// Each module runs four variants side by side on identical stimulus, compared
// every port every cycle:
//   rw  dualPort, both paths present (the reference)
//   ro  portRportRW, PORTA_READ_ONLY=1
//   bw  portRWportW, PORTB_WRITE_ONLY=1
//   wo  portRportW, PORTA_READ_ONLY=1 + PORTB_WRITE_ONLY=1
// The memory_dp_2clk set (u_*) runs port B on its own clock. The memory_dp
// set (us_*) has its own stimulus on clk, because port B stimulus timed by
// clkB would be sampled a varying number of times by a single clock.
//
// The final phases check what the parameters promise: a port A write to a
// read-only port A is dropped, and a write-only port B reads zero. On one
// clock, port B wins a same-address write from both ports, and both writes
// land when the ports write different addresses in the same cycle. A read on
// the cycle of a same-address write from the other port returns the old data;
// the memory_dp_2clk set checks this only when the half periods are equal,
// because only then do the two clocks share edges.
module memory_dp_ports_tb;

parameter int unsigned DEPTH = 320;
parameter int unsigned A_HALF_PERIOD = 5;
parameter int unsigned B_HALF_PERIOD = 7;
localparam int unsigned AW = 9;
localparam int unsigned DW = 18;

typedef logic [DW-1:0] data_t;
typedef logic [AW-1:0] addr_t;

logic clk = 1'b0;
logic clkB = 1'b0;
always #(A_HALF_PERIOD) clk = ~clk;
always #(B_HALF_PERIOD) clkB = ~clkB;

memory_if #(.data_t(data_t), .addr_t(addr_t)) rw_A();
memory_if #(.data_t(data_t), .addr_t(addr_t)) rw_B();
memory_if #(.data_t(data_t), .addr_t(addr_t)) ro_A();
memory_if #(.data_t(data_t), .addr_t(addr_t)) ro_B();

memory_dp_2clk #(.DEPTH(DEPTH), .data_t(data_t), .PORTA_READ_ONLY(1'b0)) u_rw (
    .mem_portA (rw_A), .mem_portB (rw_B), .clkA (clk), .clkB (clkB));

memory_dp_2clk #(.DEPTH(DEPTH), .data_t(data_t), .PORTA_READ_ONLY(1'b1)) u_ro (
    .mem_portA (ro_A), .mem_portB (ro_B), .clkA (clk), .clkB (clkB));

// Port A reads only and port B writes only. Storage must behave exactly as
// above on port A, while port B read-back reads zero instead of contents.
memory_if #(.data_t(data_t), .addr_t(addr_t)) wo_A();
memory_if #(.data_t(data_t), .addr_t(addr_t)) wo_B();

memory_dp_2clk #(.DEPTH(DEPTH), .data_t(data_t),
                 .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) u_wo (
    .mem_portA (wo_A), .mem_portB (wo_B), .clkA (clk), .clkB (clkB));

assign wo_A.addr       = rw_A.addr;
assign wo_A.enable     = rw_A.enable;
assign wo_A.write_data = rw_A.write_data;
assign wo_A.wr_en      = rw_A.wr_en;
assign wo_B.addr       = rw_B.addr;
assign wo_B.enable     = rw_B.enable;
assign wo_B.wr_en      = rw_B.wr_en;
assign wo_B.write_data = rw_B.write_data;

// Port A keeps both paths and port B writes only.
memory_if #(.data_t(data_t), .addr_t(addr_t)) bw_A();
memory_if #(.data_t(data_t), .addr_t(addr_t)) bw_B();

memory_dp_2clk #(.DEPTH(DEPTH), .data_t(data_t), .PORTB_WRITE_ONLY(1'b1)) u_bw (
    .mem_portA (bw_A), .mem_portB (bw_B), .clkA (clk), .clkB (clkB));

assign bw_A.addr       = rw_A.addr;
assign bw_A.enable     = rw_A.enable;
assign bw_A.write_data = rw_A.write_data;
assign bw_A.wr_en      = rw_A.wr_en;
assign bw_B.addr       = rw_B.addr;
assign bw_B.enable     = rw_B.enable;
assign bw_B.wr_en      = rw_B.wr_en;
assign bw_B.write_data = rw_B.write_data;

// Same stimulus into both copies.
assign ro_A.addr       = rw_A.addr;
assign ro_A.enable     = rw_A.enable;
assign ro_A.write_data = rw_A.write_data;
assign ro_B.addr       = rw_B.addr;
assign ro_B.enable     = rw_B.enable;
assign ro_B.wr_en      = rw_B.wr_en;
assign ro_B.write_data = rw_B.write_data;

// Port A write enable is driven per-phase (see below); the read-only instance
// always sees the same value the read/write instance does.
assign ro_A.wr_en = rw_A.wr_en;

// Single-clock set: us_rw is the reference, the others take its stimulus.
memory_if #(.data_t(data_t), .addr_t(addr_t)) s_rw_A();
memory_if #(.data_t(data_t), .addr_t(addr_t)) s_rw_B();
memory_if #(.data_t(data_t), .addr_t(addr_t)) s_ro_A();
memory_if #(.data_t(data_t), .addr_t(addr_t)) s_ro_B();
memory_if #(.data_t(data_t), .addr_t(addr_t)) s_bw_A();
memory_if #(.data_t(data_t), .addr_t(addr_t)) s_bw_B();
memory_if #(.data_t(data_t), .addr_t(addr_t)) s_wo_A();
memory_if #(.data_t(data_t), .addr_t(addr_t)) s_wo_B();

memory_dp #(.DEPTH(DEPTH), .data_t(data_t)) us_rw (
    .mem_portA (s_rw_A), .mem_portB (s_rw_B), .clk (clk));
memory_dp #(.DEPTH(DEPTH), .data_t(data_t), .PORTA_READ_ONLY(1'b1)) us_ro (
    .mem_portA (s_ro_A), .mem_portB (s_ro_B), .clk (clk));
memory_dp #(.DEPTH(DEPTH), .data_t(data_t), .PORTB_WRITE_ONLY(1'b1)) us_bw (
    .mem_portA (s_bw_A), .mem_portB (s_bw_B), .clk (clk));
memory_dp #(.DEPTH(DEPTH), .data_t(data_t),
            .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) us_wo (
    .mem_portA (s_wo_A), .mem_portB (s_wo_B), .clk (clk));

assign s_ro_A.addr = s_rw_A.addr;  assign s_ro_A.enable = s_rw_A.enable;
assign s_ro_A.wr_en = s_rw_A.wr_en; assign s_ro_A.write_data = s_rw_A.write_data;
assign s_ro_B.addr = s_rw_B.addr;  assign s_ro_B.enable = s_rw_B.enable;
assign s_ro_B.wr_en = s_rw_B.wr_en; assign s_ro_B.write_data = s_rw_B.write_data;
assign s_bw_A.addr = s_rw_A.addr;  assign s_bw_A.enable = s_rw_A.enable;
assign s_bw_A.wr_en = s_rw_A.wr_en; assign s_bw_A.write_data = s_rw_A.write_data;
assign s_bw_B.addr = s_rw_B.addr;  assign s_bw_B.enable = s_rw_B.enable;
assign s_bw_B.wr_en = s_rw_B.wr_en; assign s_bw_B.write_data = s_rw_B.write_data;
assign s_wo_A.addr = s_rw_A.addr;  assign s_wo_A.enable = s_rw_A.enable;
assign s_wo_A.wr_en = s_rw_A.wr_en; assign s_wo_A.write_data = s_rw_A.write_data;
assign s_wo_B.addr = s_rw_B.addr;  assign s_wo_B.enable = s_rw_B.enable;
assign s_wo_B.wr_en = s_rw_B.wr_en; assign s_wo_B.write_data = s_rw_B.write_data;

int unsigned errors;
int unsigned compares;
logic        checking;

// Continuous comparison rather than sampling at chosen points, so a divergence
// cannot hide between checks.
always @(posedge clk) begin
    if (checking) begin
        compares++;
        if (rw_A.read_data !== ro_A.read_data) begin
            if (errors < 8)
                $display("    port A differs: rw=0x%0x ro=0x%0x addr=%0d",
                         rw_A.read_data, ro_A.read_data, rw_A.addr);
            errors++;
        end
        // Dropping port B read-back must not disturb the datapath read.
        if (rw_A.read_data !== wo_A.read_data) begin
            if (errors < 8)
                $display("    port A differs: rw=0x%0x wo=0x%0x addr=%0d",
                         rw_A.read_data, wo_A.read_data, rw_A.addr);
            errors++;
        end
        if (rw_A.read_data !== bw_A.read_data) begin
            if (errors < 8)
                $display("    port A differs: rw=0x%0x bw=0x%0x addr=%0d",
                         rw_A.read_data, bw_A.read_data, rw_A.addr);
            errors++;
        end
    end
end

always @(posedge clkB) begin
    if (checking) begin
        if (rw_B.read_data !== ro_B.read_data) begin
            if (errors < 8)
                $display("    port B differs: rw=0x%0x ro=0x%0x addr=%0d",
                         rw_B.read_data, ro_B.read_data, rw_B.addr);
            errors++;
        end
        if (wo_B.read_data !== '0) begin
            if (errors < 8)
                $display("    PORTB_WRITE_ONLY=1 returned 0x%0x, expected 0",
                         wo_B.read_data);
            errors++;
        end
        if (bw_B.read_data !== '0) begin
            if (errors < 8)
                $display("    portRWportW port B returned 0x%0x, expected 0",
                         bw_B.read_data);
            errors++;
        end
    end
end

logic s_checking = 1'b0;

always @(posedge clk) begin
    if (s_checking) begin
        compares++;
        if (s_rw_A.read_data !== s_ro_A.read_data || s_rw_A.read_data !== s_bw_A.read_data
                || s_rw_A.read_data !== s_wo_A.read_data) begin
            if (errors < 8)
                $display("    single-clock port A differs: rw=0x%0x ro=0x%0x bw=0x%0x wo=0x%0x addr=%0d",
                         s_rw_A.read_data, s_ro_A.read_data, s_bw_A.read_data,
                         s_wo_A.read_data, s_rw_A.addr);
            errors++;
        end
        if (s_rw_B.read_data !== s_ro_B.read_data) begin
            if (errors < 8)
                $display("    single-clock port B differs: rw=0x%0x ro=0x%0x addr=%0d",
                         s_rw_B.read_data, s_ro_B.read_data, s_rw_B.addr);
            errors++;
        end
        if (s_bw_B.read_data !== '0 || s_wo_B.read_data !== '0) begin
            if (errors < 8)
                $display("    single-clock write-only port B returned bw=0x%0x wo=0x%0x, expected 0",
                         s_bw_B.read_data, s_wo_B.read_data);
            errors++;
        end
    end
end

task automatic s_idle();
    begin
        s_rw_A.enable = 1'b0; s_rw_A.wr_en = 1'b0;
        s_rw_A.addr = '0; s_rw_A.write_data = '0;
        s_rw_B.enable = 1'b0; s_rw_B.wr_en = 1'b0;
        s_rw_B.addr = '0; s_rw_B.write_data = '0;
    end
endtask

// Drives one cycle of a port A access and returns each copy's read data a
// cycle later.
task automatic s_read_a(input int unsigned i, output data_t rw, output data_t ro,
                        output data_t bw, output data_t wo);
    begin
        @(negedge clk);
        s_rw_A.enable = 1'b1; s_rw_A.wr_en = 1'b0; s_rw_A.addr = addr_t'(i);
        @(posedge clk); #1;
        rw = s_rw_A.read_data; ro = s_ro_A.read_data;
        bw = s_bw_A.read_data; wo = s_wo_A.read_data;
        @(negedge clk);
        s_idle();
    end
endtask

task automatic idle_a();
    begin
        rw_A.enable = 1'b0; rw_A.wr_en = 1'b0;
        rw_A.addr = '0; rw_A.write_data = '0;
    end
endtask

task automatic idle_b();
    begin
        rw_B.enable = 1'b0; rw_B.wr_en = 1'b0;
        rw_B.addr = '0; rw_B.write_data = '0;
    end
endtask

// Fill the array over port B.
task automatic fill_via_b();
    begin
        for (int unsigned i = 0; i < DEPTH; i++) begin
            @(negedge clkB);
            rw_B.enable = 1'b1; rw_B.wr_en = 1'b1;
            rw_B.addr = addr_t'(i);
            rw_B.write_data = data_t'((i * 7) ^ 32'h2A5A5);
        end
        @(negedge clkB);
        idle_b();
    end
endtask

function automatic data_t expected(input int unsigned i);
    return data_t'((i * 7) ^ 32'h2A5A5);
endfunction

int unsigned seed = 32'h1234_5678;

initial begin
    errors = 0;
    compares = 0;
    checking = 1'b0;
    idle_a();
    idle_b();

    repeat (4) @(negedge clk);
    fill_via_b();
    checking = 1'b1;

    $display("=== memory_dp_2clk two clocks ===");

    // Phase 1: port A reads while port B is idle.
    for (int unsigned i = 0; i < DEPTH; i++) begin
        @(negedge clk);
        rw_A.enable = 1'b1; rw_A.wr_en = 1'b0;
        rw_A.addr = addr_t'(i);
    end
    @(negedge clk);
    idle_a();
    repeat (4) @(negedge clk);

    // Port A must be returning the real contents, not a stuck value - proves
    // the read path in the PORTA_READ_ONLY=1 branch actually works.
    begin
        int unsigned bad = 0;
        for (int unsigned i = 0; i < 64; i++) begin
            @(negedge clk);
            rw_A.enable = 1'b1; rw_A.wr_en = 1'b0; rw_A.addr = addr_t'(i);
            @(posedge clk);
            #1;
            if (ro_A.read_data !== expected(i)) begin
                if (bad < 4)
                    $display("    read %0d got 0x%0x expected 0x%0x",
                             i, ro_A.read_data, expected(i));
                bad++;
            end
            // Same array, written only through the write-only port B.
            if (wo_A.read_data !== expected(i)) begin
                if (bad < 4)
                    $display("    wo read %0d got 0x%0x expected 0x%0x",
                             i, wo_A.read_data, expected(i));
                bad++;
            end
            if (bw_A.read_data !== expected(i)) begin
                if (bad < 4)
                    $display("    bw read %0d got 0x%0x expected 0x%0x",
                             i, bw_A.read_data, expected(i));
                bad++;
            end
        end
        @(negedge clk);
        idle_a();
        errors += bad;
        $display("  %-40s mismatches=%0d  %s", "port A returns stored data",
                 bad, (bad == 0) ? "PASS" : "FAIL");
    end

    // Phase 2: both ports active at once, random addresses, port B still
    // writing.
    for (int unsigned n = 0; n < 2000; n++) begin
        @(negedge clk);
        rw_A.enable = ($urandom(seed) % 4) != 0;
        rw_A.wr_en  = 1'b0;
        rw_A.addr   = addr_t'($urandom % DEPTH);
        if ((n % 3) == 0) begin
            rw_B.enable     = 1'b1;
            rw_B.wr_en      = 1'($urandom % 2);
            rw_B.addr       = addr_t'($urandom % DEPTH);
            rw_B.write_data = data_t'($urandom);
        end else begin
            rw_B.enable = 1'b0; rw_B.wr_en = 1'b0;
        end
    end
    @(negedge clk);
    idle_a();
    idle_b();
    repeat (8) @(negedge clk);
    $display("  %-40s compares=%0d  %s", "identical under concurrent access",
             compares, (errors == 0) ? "PASS" : "FAIL");

    // Phase 3: the parameter's contract. Drive a port A write at every copy;
    // the read/write ones take it, the read-only one must ignore it. They are
    // expected to differ here, so comparison is off.
    checking = 1'b0;
    begin
        localparam int unsigned PROBE = 100;
        data_t before_val, rw_val, ro_val, bw_val;

        @(negedge clk);
        rw_A.enable = 1'b1; rw_A.wr_en = 1'b0; rw_A.addr = addr_t'(PROBE);
        @(posedge clk); #1;
        before_val = ro_A.read_data;

        @(negedge clk);
        rw_A.enable = 1'b1; rw_A.wr_en = 1'b1; rw_A.addr = addr_t'(PROBE);
        rw_A.write_data = data_t'(18'h3FFFF);
        @(negedge clk);
        rw_A.enable = 1'b1; rw_A.wr_en = 1'b0; rw_A.addr = addr_t'(PROBE);
        @(posedge clk); #1;
        rw_val = rw_A.read_data;
        ro_val = ro_A.read_data;
        bw_val = bw_A.read_data;
        @(negedge clk);
        idle_a();

        if (rw_val !== data_t'(18'h3FFFF)) begin
            $display("    PORTA_READ_ONLY=0 did not take the write: 0x%0x", rw_val);
            errors++;
        end
        if (bw_val !== data_t'(18'h3FFFF)) begin
            $display("    portRWportW port A did not take the write: 0x%0x", bw_val);
            errors++;
        end
        if (ro_val !== before_val) begin
            $display("    PORTA_READ_ONLY=1 honoured a port A write: 0x%0x -> 0x%0x",
                     before_val, ro_val);
            errors++;
        end
        $display("  %-40s %s", "PORTA_READ_ONLY=1 drops port A writes",
                 ((rw_val === data_t'(18'h3FFFF)) && (bw_val === data_t'(18'h3FFFF))
                  && (ro_val === before_val))
                 ? "PASS" : "FAIL");
    end

    // Port B read-back. Checking the write-only copy returns zero proves
    // nothing on its own, so the reference is read at the same address in the
    // same cycle: it must return real contents where the other returns zero.
    begin
        localparam int unsigned PROBE = 301;
        localparam data_t SENTINEL = data_t'(18'h1C3C3);
        data_t rw_val, wo_val, bw_val;

        // Phase 2 scribbled random data, so plant a known value first.
        @(negedge clkB);
        rw_B.enable = 1'b1; rw_B.wr_en = 1'b1; rw_B.addr = addr_t'(PROBE);
        rw_B.write_data = SENTINEL;
        @(negedge clkB);
        rw_B.enable = 1'b1; rw_B.wr_en = 1'b0; rw_B.addr = addr_t'(PROBE);
        @(posedge clkB); #1;
        rw_val = rw_B.read_data;
        wo_val = wo_B.read_data;
        bw_val = bw_B.read_data;
        @(negedge clkB);
        idle_b();

        if (rw_val !== SENTINEL) begin
            $display("    reference port B read 0x%0x, expected 0x%0x",
                     rw_val, SENTINEL);
            errors++;
        end
        if (wo_val !== '0) begin
            $display("    PORTB_WRITE_ONLY=1 returned 0x%0x, expected 0", wo_val);
            errors++;
        end
        if (bw_val !== '0) begin
            $display("    portRWportW port B returned 0x%0x, expected 0", bw_val);
            errors++;
        end
        $display("  %-40s %s", "PORTB_WRITE_ONLY=1 reads zero, ref reads data",
                 ((rw_val === SENTINEL) && (wo_val === '0) && (bw_val === '0))
                 ? "PASS" : "FAIL");
    end

    // A same-cycle read and write only exists when both clocks share their
    // edges, so the old-data probe runs at equal half periods only.
    if (A_HALF_PERIOD == B_HALF_PERIOD) begin
        localparam int unsigned PX = 40;
        localparam data_t NEW_VAL = data_t'(18'h2DDDD);
        data_t old_rw, old_ro, old_bw, old_wo, got_rw, got_ro, got_bw, got_wo;
        data_t old_b, got_b;
        int unsigned bad = 0;

        @(negedge clk);
        rw_A.enable = 1'b1; rw_A.wr_en = 1'b0; rw_A.addr = addr_t'(PX);
        @(posedge clk); #1;
        old_rw = rw_A.read_data; old_ro = ro_A.read_data;
        old_bw = bw_A.read_data; old_wo = wo_A.read_data;
        // Port B writes PX in the cycle port A reads it.
        @(negedge clk);
        rw_B.enable = 1'b1; rw_B.wr_en = 1'b1; rw_B.addr = addr_t'(PX);
        rw_B.write_data = NEW_VAL;
        @(posedge clk); #1;
        got_rw = rw_A.read_data; got_ro = ro_A.read_data;
        got_bw = bw_A.read_data; got_wo = wo_A.read_data;
        @(negedge clk);
        idle_a();
        idle_b();
        if (got_rw !== old_rw || got_ro !== old_ro || got_bw !== old_bw || got_wo !== old_wo) begin
            $display("    port A read during a port B write: rw=0x%0x ro=0x%0x bw=0x%0x wo=0x%0x, expected old rw=0x%0x ro=0x%0x bw=0x%0x wo=0x%0x",
                     got_rw, got_ro, got_bw, got_wo, old_rw, old_ro, old_bw, old_wo);
            bad++;
        end

        // Port A writes PX + 1 in the cycle port B reads it, on u_rw.
        @(negedge clk);
        rw_B.enable = 1'b1; rw_B.wr_en = 1'b0; rw_B.addr = addr_t'(PX + 1);
        @(posedge clk); #1;
        old_b = rw_B.read_data;
        @(negedge clk);
        rw_A.enable = 1'b1; rw_A.wr_en = 1'b1; rw_A.addr = addr_t'(PX + 1);
        rw_A.write_data = NEW_VAL;
        @(posedge clk); #1;
        got_b = rw_B.read_data;
        @(negedge clk);
        idle_a();
        idle_b();
        if (got_b !== old_b || old_b === NEW_VAL) begin
            $display("    port B read during a port A write: 0x%0x, expected old 0x%0x",
                     got_b, old_b);
            bad++;
        end
        errors += bad;
        $display("  %-40s %s", "same-cycle read returns the old data",
                 (bad == 0) ? "PASS" : "FAIL");
    end

    $display("=== memory_dp single clock ===");
    s_idle();
    for (int unsigned i = 0; i < DEPTH; i++) begin
        @(negedge clk);
        s_rw_B.enable = 1'b1; s_rw_B.wr_en = 1'b1;
        s_rw_B.addr = addr_t'(i); s_rw_B.write_data = expected(i);
    end
    @(negedge clk);
    s_idle();
    s_checking = 1'b1;

    begin
        int unsigned bad = 0;
        data_t rw, ro, bw, wo;
        for (int unsigned i = 0; i < 64; i++) begin
            s_read_a(i, rw, ro, bw, wo);
            if (rw !== expected(i) || ro !== expected(i) || bw !== expected(i)
                    || wo !== expected(i)) begin
                if (bad < 4)
                    $display("    read %0d got rw=0x%0x ro=0x%0x bw=0x%0x wo=0x%0x expected 0x%0x",
                             i, rw, ro, bw, wo, expected(i));
                bad++;
            end
        end
        errors += bad;
        $display("  %-40s mismatches=%0d  %s", "port A returns stored data",
                 bad, (bad == 0) ? "PASS" : "FAIL");
    end

    // Port A reads and port B reads or writes every cycle, random addresses.
    for (int unsigned n = 0; n < 2000; n++) begin
        @(negedge clk);
        s_rw_A.enable     = ($urandom(seed) % 4) != 0;
        s_rw_A.wr_en      = 1'b0;
        s_rw_A.addr       = addr_t'($urandom % DEPTH);
        s_rw_B.enable     = ($urandom % 2) != 0;
        s_rw_B.wr_en      = 1'($urandom % 2);
        s_rw_B.addr       = addr_t'($urandom % DEPTH);
        s_rw_B.write_data = data_t'($urandom);
    end
    @(negedge clk);
    s_idle();
    repeat (4) @(negedge clk);
    $display("  %-40s compares=%0d  %s", "identical under concurrent access",
             compares, (errors == 0) ? "PASS" : "FAIL");

    // The copies are expected to differ from here on.
    s_checking = 1'b0;
    begin
        localparam int unsigned PROBE = 100;
        data_t before_val, rw, ro, bw, wo;
        s_read_a(PROBE, rw, before_val, bw, wo);
        @(negedge clk);
        s_rw_A.enable = 1'b1; s_rw_A.wr_en = 1'b1; s_rw_A.addr = addr_t'(PROBE);
        s_rw_A.write_data = data_t'(18'h3FFFF);
        s_read_a(PROBE, rw, ro, bw, wo);
        if (rw !== data_t'(18'h3FFFF) || bw !== data_t'(18'h3FFFF)
                || ro !== before_val || wo !== before_val) begin
            $display("    port A write: rw=0x%0x bw=0x%0x ro=0x%0x wo=0x%0x before=0x%0x",
                     rw, bw, ro, wo, before_val);
            errors++;
        end
        $display("  %-40s %s", "PORTA_READ_ONLY=1 drops port A writes",
                 (rw === data_t'(18'h3FFFF) && bw === data_t'(18'h3FFFF)
                  && ro === before_val && wo === before_val) ? "PASS" : "FAIL");
    end

    begin
        localparam int unsigned PROBE = 301;
        localparam data_t SENTINEL = data_t'(18'h1C3C3);
        data_t rw, ro, bw, wo;
        @(negedge clk);
        s_rw_B.enable = 1'b1; s_rw_B.wr_en = 1'b1; s_rw_B.addr = addr_t'(PROBE);
        s_rw_B.write_data = SENTINEL;
        @(negedge clk);
        s_rw_B.enable = 1'b1; s_rw_B.wr_en = 1'b0; s_rw_B.addr = addr_t'(PROBE);
        @(posedge clk); #1;
        rw = s_rw_B.read_data; ro = s_ro_B.read_data;
        bw = s_bw_B.read_data; wo = s_wo_B.read_data;
        @(negedge clk);
        s_idle();
        if (rw !== SENTINEL || ro !== SENTINEL || bw !== '0 || wo !== '0) begin
            $display("    port B read: rw=0x%0x ro=0x%0x bw=0x%0x wo=0x%0x, expected 0x%0x 0x%0x 0 0",
                     rw, ro, bw, wo, SENTINEL, SENTINEL);
            errors++;
        end
        $display("  %-40s %s", "PORTB_WRITE_ONLY=1 reads zero, ref reads data",
                 (rw === SENTINEL && ro === SENTINEL && bw === '0 && wo === '0)
                 ? "PASS" : "FAIL");
    end

    // Both ports write one address in the same cycle. Port B wins in every
    // mode: by ordering where port A writes, by construction where it cannot.
    begin
        localparam int unsigned PROBE = 7;
        localparam data_t A_VAL = data_t'(18'h0AAAA);
        localparam data_t B_VAL = data_t'(18'h15555);
        data_t rw, ro, bw, wo;
        @(negedge clk);
        s_rw_A.enable = 1'b1; s_rw_A.wr_en = 1'b1; s_rw_A.addr = addr_t'(PROBE);
        s_rw_A.write_data = A_VAL;
        s_rw_B.enable = 1'b1; s_rw_B.wr_en = 1'b1; s_rw_B.addr = addr_t'(PROBE);
        s_rw_B.write_data = B_VAL;
        s_read_a(PROBE, rw, ro, bw, wo);
        if (rw !== B_VAL || ro !== B_VAL || bw !== B_VAL || wo !== B_VAL) begin
            $display("    double write: rw=0x%0x ro=0x%0x bw=0x%0x wo=0x%0x, expected 0x%0x",
                     rw, ro, bw, wo, B_VAL);
            errors++;
        end
        $display("  %-40s %s", "port B wins a same-address double write",
                 (rw === B_VAL && ro === B_VAL && bw === B_VAL && wo === B_VAL)
                 ? "PASS" : "FAIL");
    end

    // Both ports write different addresses in one cycle. Neither write may be
    // lost on the copies where port A writes.
    begin
        localparam int unsigned PA = 20;
        localparam int unsigned PB = 21;
        localparam data_t A_VAL = data_t'(18'h0F0F0);
        localparam data_t B_VAL = data_t'(18'h30303);
        data_t rwA, rwB, bwA, bwB, ro, wo;
        @(negedge clk);
        s_rw_A.enable = 1'b1; s_rw_A.wr_en = 1'b1; s_rw_A.addr = addr_t'(PA);
        s_rw_A.write_data = A_VAL;
        s_rw_B.enable = 1'b1; s_rw_B.wr_en = 1'b1; s_rw_B.addr = addr_t'(PB);
        s_rw_B.write_data = B_VAL;
        @(negedge clk);
        s_idle();
        s_read_a(PA, rwA, ro, bwA, wo);
        s_read_a(PB, rwB, ro, bwB, wo);
        if (rwA !== A_VAL || bwA !== A_VAL || rwB !== B_VAL || bwB !== B_VAL) begin
            $display("    two-address write: rw A=0x%0x B=0x%0x bw A=0x%0x B=0x%0x, expected 0x%0x 0x%0x",
                     rwA, rwB, bwA, bwB, A_VAL, B_VAL);
            errors++;
        end
        $display("  %-40s %s", "both ports write two addresses at once",
                 (rwA === A_VAL && bwA === A_VAL && rwB === B_VAL && bwB === B_VAL)
                 ? "PASS" : "FAIL");
    end

    // A read in the cycle the other port writes the same address returns the
    // old data.
    begin
        localparam int unsigned PX = 40;
        localparam data_t NEW_VAL = data_t'(18'h2DDDD);
        data_t old_rw, old_ro, old_bw, old_wo, got_rw, got_ro, got_bw, got_wo;
        data_t old_b, got_b;
        int unsigned bad = 0;

        s_read_a(PX, old_rw, old_ro, old_bw, old_wo);
        @(negedge clk);
        s_rw_A.enable = 1'b1; s_rw_A.wr_en = 1'b0; s_rw_A.addr = addr_t'(PX);
        s_rw_B.enable = 1'b1; s_rw_B.wr_en = 1'b1; s_rw_B.addr = addr_t'(PX);
        s_rw_B.write_data = NEW_VAL;
        @(posedge clk); #1;
        got_rw = s_rw_A.read_data; got_ro = s_ro_A.read_data;
        got_bw = s_bw_A.read_data; got_wo = s_wo_A.read_data;
        @(negedge clk);
        s_idle();
        if (got_rw !== old_rw || got_ro !== old_ro || got_bw !== old_bw || got_wo !== old_wo
                || old_rw === NEW_VAL) begin
            $display("    port A read during a port B write: rw=0x%0x ro=0x%0x bw=0x%0x wo=0x%0x, expected old rw=0x%0x ro=0x%0x bw=0x%0x wo=0x%0x",
                     got_rw, got_ro, got_bw, got_wo, old_rw, old_ro, old_bw, old_wo);
            bad++;
        end

        // The reverse direction exists only on us_rw: port A writes, port B reads.
        @(negedge clk);
        s_rw_B.enable = 1'b1; s_rw_B.wr_en = 1'b0; s_rw_B.addr = addr_t'(PX + 1);
        @(posedge clk); #1;
        old_b = s_rw_B.read_data;
        @(negedge clk);
        s_rw_A.enable = 1'b1; s_rw_A.wr_en = 1'b1; s_rw_A.addr = addr_t'(PX + 1);
        s_rw_A.write_data = NEW_VAL;
        @(posedge clk); #1;
        got_b = s_rw_B.read_data;
        @(negedge clk);
        s_idle();
        if (got_b !== old_b || old_b === NEW_VAL) begin
            $display("    port B read during a port A write: 0x%0x, expected old 0x%0x",
                     got_b, old_b);
            bad++;
        end
        errors += bad;
        $display("  %-40s %s", "same-cycle read returns the old data",
                 (bad == 0) ? "PASS" : "FAIL");
    end

    $display("=== %s (%0d errors) ===", (errors == 0) ? "PASS" : "FAIL", errors);
    if (errors != 0)
        $fatal(1, "memory_dp_ports_tb: %0d errors", errors);
    $display("TB_PASS");
    $finish;
end

endmodule: memory_dp_ports_tb
