// Self-checking simulation testbench for
// common/systemVerilog/memory_reg_bridge.sv, built standalone by
// unittest/test_memory_reg_bridge_sim.py with Verilator `--binary --timing`.
//
// A reference model (ref_mem) tracks every write the bridge is expected to
// land, updated by the driver tasks below and checked against most reads.
// Two scenarios check it differently: scenario_random_traffic checks a
// per-row candidate set instead of one value, and scenario_bus_reset_mid_access
// accepts either the old or the new value for the row a reset lands on.
// Scenarios run in sequence, sharing that one reference model and the memory
// array behind it, so later scenarios see the state earlier ones left.

/* verilator lint_off BLKSEQ */
// This file is stimulus, not RTL: blocking assignments sequence reset and
// scenario control flow, and tasks use delays and edge waits freely.

module memory_reg_bridge_tb #(
    parameter int BUS_HALF_PERIOD = 2,
    parameter int MEM_HALF_PERIOD = 2,
    // Delays the first mem_clk toggle by this many time units, so a
    // symmetric clock ratio does not put every mem_clk edge exactly on a
    // bus_clk edge. Six of the twenty configurations
    // test_memory_reg_bridge_sim.py builds run with MEM_PHASE=1.
    parameter int MEM_PHASE = 0
) ();

    logic bus_clk, mem_clk;
    logic bus_rst_n, mem_rst_n;

    // The DUT's own bus-domain ports. Named apart from the driver tasks'
    // arguments below so a task argument never shadows the wire it drives.
    logic drv_req, drv_wr, drv_done, drv_err;
    logic [2:0] drv_addr;
    logic [47:0] drv_wdata, drv_rdata;

    logic [47:0] ref_mem [0:7];
    string scenario_name;
    // Set once by calibrate_done_cycles() near the start of the run, the
    // bus cycles from the first untimed access to a genuinely idle bus
    // (alive, connected, no ack or request outstanding); the sweeps below
    // add it to done_cycles to size an offset ceiling that still covers the
    // drain after an access, not just the access itself.
    int drain_cycles;
    // Set once by calibrate_done_cycles() near the start of the run, right
    // after drain_cycles; the sweeps below read it to size offset_ns, the
    // delay each sweep step passes to mem_reset_pulse as assert_delay_ns.
    int done_cycles;
    // retry_access's cap on retry attempts, derived once from the
    // connect-cost formula at the computation site below.
    int max_retries;
    // The largest attempt count any retry_access call actually needed,
    // tracked for the informational report at the end of the run.
    int max_attempts_seen = 0;

    memory_if #(.data_t(logic [47:0]), .addr_t(logic [2:0])) mem();

    memory_reg_bridge #(.data_t(logic [47:0]), .addr_t(logic [2:0])) dut (
        .bus_clk  (bus_clk),
        .bus_rst_n(bus_rst_n),
        .mem_clk  (mem_clk),
        .mem_rst_n(mem_rst_n),
        .req      (drv_req),
        .wr       (drv_wr),
        .addr     (drv_addr),
        .wdata    (drv_wdata),
        .done     (drv_done),
        .err      (drv_err),
        .rdata    (drv_rdata),
        .mem_port (mem)
    );

    memory_sp #(.DEPTH(8), .data_t(logic [47:0])) uMem (
        .mem_port(mem),
        .clk     (mem_clk)
    );

    // Diagnostic only, not a pass/fail check on its own. Counts bus_clk
    // edges where the bridge starts an access while the memory side has not
    // reported alive. A nonzero count shows a scenario reached the window
    // BUS_DRAIN exists for, a request accepted on an alive_sync_stable
    // reading that a memory reset landing moments later has already
    // invalidated. Reset at the start of each scenario and printed at its
    // end.
    int stale_starts;
    always @(posedge bus_clk) if (dut.start_access && !dut.alive) stale_starts++;

    // End-to-end monitor, always on, independent of which scenario is
    // running. A completion without error always corresponds to exactly one
    // execution of that same request against the memory array. mon_wr/mon_addr/
    // mon_wdata record the request latched at the most recent start_access;
    // mon_executed counts mem_port.enable pulses against it since. Only one
    // access is ever outstanding, so a new start_access cannot arrive before
    // the previous one's done, whether that done carried err or not.
    logic mon_wr;
    logic [2:0] mon_addr;
    logic [47:0] mon_wdata;
    int mon_executed;

    always @(posedge bus_clk) begin
        if (drv_done && !drv_err && mon_executed == 0)
            $fatal(1, "monitor: a completion without error had no execution behind it");
        if (dut.start_access) begin
            mon_wr = drv_wr;
            mon_addr = drv_addr;
            mon_wdata = drv_wdata;
            mon_executed = 0;
        end
    end

    always @(posedge mem_clk) begin
        if (mem.enable) begin
            if (mem.wr_en !== mon_wr || mem.addr !== mon_addr ||
                (mon_wr && mem.write_data !== mon_wdata))
                $fatal(1, "monitor: the memory executed a request that does not match the one recorded at start_access");
            mon_executed++;
            if (mon_executed > 1)
                $fatal(1, "monitor: one request executed against the memory more than once");
        end
    end

`ifdef A2C_CDC_JITTER
    // Drives the jitter hooks declared in memory_reg_bridge.sv, one urandom
    // draw per hook per receiving-domain edge, independent per hook, each a
    // 1-in-3 chance of asking to hold the first stage instead of updating
    // it. The RTL's own hold logic grants at most one hold per transition,
    // two on a crossing's first transition after reset (the release-credit
    // mechanism), so a draw of 1 here past that limit is simply not granted.
    always @(posedge mem_clk) begin
        dut.jit_req <= ($urandom_range(2) == 0);
        dut.jit_bus_alive <= ($urandom_range(2) == 0);
    end
    always @(posedge bus_clk) begin
        dut.jit_alive <= ($urandom_range(2) == 0);
        dut.jit_ack <= ($urandom_range(2) == 0);
    end
`endif

    always #BUS_HALF_PERIOD bus_clk = ~bus_clk;
    initial begin
        #MEM_PHASE;
        forever #MEM_HALF_PERIOD mem_clk = ~mem_clk;
    end

    // ------------------------------------------------------------- drivers --

    // Holds bus_rst_n low for `cycles` bus cycles, then releases it.
    //
    // Both edges sit on a negedge of bus_clk, here and at every other
    // rst_n write in this file, so every posedge between them samples
    // reset low unambiguously, whatever order the simulator runs
    // processes in; a width of 1 is as unambiguous as any other width.
    task automatic bus_reset(input int cycles);
        @(negedge bus_clk);
        bus_rst_n = 1'b0;
        repeat (cycles) @(posedge bus_clk);
        @(negedge bus_clk);
        bus_rst_n = 1'b1;
    endtask

    // Asserts mem_rst_n after assert_delay_ns, holds it for
    // width_mem_cycles memory cycles, then releases it.
    task automatic mem_reset_pulse(input int assert_delay_ns, input int width_mem_cycles);
        #(assert_delay_ns);
        @(negedge mem_clk);
        mem_rst_n = 1'b0;
        repeat (width_mem_cycles) @(posedge mem_clk);
        @(negedge mem_clk);
        mem_rst_n = 1'b1;
    endtask

    // Caller contract: set req/wr/addr/wdata at a negedge, hold until done,
    // sample err and rdata at the negedge after done, then drop req at that
    // same negedge so the gap before the next access can be as short as one
    // bus cycle. Checks err against expect_err, and on a successful access
    // checks or updates ref_mem.
    task automatic access(input logic wr, input logic [2:0] addr, input logic [47:0] wdata,
                          input logic expect_err, output logic [47:0] rdata_out);
        int timeout_count;
        @(negedge bus_clk);
        drv_req = 1'b1;
        drv_wr = wr;
        drv_addr = addr;
        drv_wdata = wdata;
        timeout_count = 0;
        // A same-cycle fail (memory domain not alive) settles done
        // combinationally off req itself, in this delta, before req_taken
        // registers at the next posedge and clears it; a negedge wait alone
        // arrives too late to see that pulse, so check once, settled, here.
        #0;
        while (!drv_done) begin
            @(negedge bus_clk);
            timeout_count++;
            if (timeout_count > 400)
                $fatal(1, "%s: timed out waiting for done", scenario_name);
        end
        if (drv_err !== expect_err)
            $fatal(1, "%s: err=%0d, expected %0d", scenario_name, drv_err, expect_err);
        rdata_out = drv_rdata;
        if (!expect_err) begin
            if (wr) ref_mem[addr] = wdata;
            else if (drv_rdata !== ref_mem[addr])
                $fatal(1, "%s: read row %0d returned %h, expected %h",
                       scenario_name, addr, drv_rdata, ref_mem[addr]);
        end
        drv_req = 1'b0;
    endtask

    // Same handshake as access(), but reports the outcome instead of
    // fatal-ing on a mismatch. Used where a scenario has to keep going
    // and tally failures across a sweep rather than stop at the first one.
    task automatic soft_access(input logic wr, input logic [2:0] addr, input logic [47:0] wdata,
                               output logic got_err, output logic [47:0] rdata_out);
        int timeout_count;
        @(negedge bus_clk);
        drv_req = 1'b1;
        drv_wr = wr;
        drv_addr = addr;
        drv_wdata = wdata;
        timeout_count = 0;
        #0;
        while (!drv_done) begin
            @(negedge bus_clk);
            timeout_count++;
            if (timeout_count > 400)
                $fatal(1, "%s: timed out waiting for done", scenario_name);
        end
        got_err = drv_err;
        rdata_out = drv_rdata;
        drv_req = 1'b0;
    endtask

    // Reissues an access at the minimum req gap while it returns err. The
    // bridge answers that way whenever the memory domain has not yet
    // reported alive, which firmware is expected to retry rather than treat
    // as a failure. Gives up after max_retries attempts (a hang or a dead
    // memory). A timeout inside soft_access, or a wrong result once err is
    // 0, is a real defect and fatals on its own.
    //
    // A read moves to a different row on each attempt (row_read reports
    // which row the successful attempt actually read) so a stale ack that
    // completes a retry cannot be mistaken for a correct one: a stale ack
    // carries the previous attempt's row and data, and comparing that
    // against the row it was actually read from, rather than the row the
    // caller asked for, catches it instead of matching by coincidence. A
    // write keeps the same row on every attempt; a stale ack completing a
    // write is a completion the monitor did not see executed, and the
    // monitor's own check (err=0 with mon_executed==0) catches that.
    task automatic retry_access(input logic wr, input logic [2:0] addr, input logic [47:0] wdata,
                                 output logic [47:0] rdata_out, output logic [2:0] row_read,
                                 output int attempts);
        logic got_err;
        logic [2:0] this_row;
        attempts = 0;
        forever begin
            this_row = wr ? addr : 3'((32'(addr) + attempts) % 8);
            soft_access(wr, this_row, wdata, got_err, rdata_out);
            if (!got_err) begin
                row_read = this_row;
                if (attempts > max_attempts_seen) max_attempts_seen = attempts;
                return;
            end
            attempts++;
            if (attempts >= max_retries)
                $fatal(1, "%s: addr=%0d still err after %0d attempts, memory side never returned alive",
                       scenario_name, addr, attempts);
        end
    endtask

    // Measures two figures off one settle-then-read sequence, in bus
    // cycles, so the sweeps below can size an offset ceiling that covers
    // both an access and the drain after it rather than one or the other.
    // A first, untimed access can still leave a previous access's drain
    // running behind it or, called this early in the run, the connect
    // handshake still finishing behind the startup retry above, so
    // drain_cycles counts bus negedges from that access until the bus
    // reads genuinely idle, alive and connected with no ack or request
    // outstanding. The timed read then rises at that same negedge, and
    // done_cycles counts from there to done, a pure idle read latency with
    // no drain folded into it.
    task automatic calibrate_done_cycles(output int drain, output int cycles);
        logic [47:0] rd;
        access(1'b0, 3'd0, 48'h0, 1'b0, rd);
        drain = 0;
        do begin
            @(negedge bus_clk);
            drain++;
            if (drain > 400)
                $fatal(1, "calibration: timed out waiting for an idle bus");
        end while (!(dut.bus_alive && dut.alive_sync_stable && !dut.ack_sync_stable &&
                     !dut.req_latch));
        drv_req = 1'b1;
        drv_wr = 1'b0;
        drv_addr = 3'd0;
        drv_wdata = 48'h0;
        cycles = 0;
        do begin
            @(negedge bus_clk);
            cycles++;
            if (cycles > 400)
                $fatal(1, "calibration: timed out waiting for done");
        end while (!drv_done);
        drv_req = 1'b0;
    endtask

    // ------------------------------------------------------------ scenarios --

    // Proves basic read/write correctness across every row.
    task automatic scenario_write_read_all();
        logic [47:0] vals [8];
        logic [47:0] rd;
        int i;
        scenario_name = "write_read_all";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        vals = '{48'hA1B2C3D4E5F6, 48'h123456789ABC, 48'hDEADBEEFCAFE, 48'h0F1E2D3C4B5A,
                 48'hFEDCBA987654, 48'h5555AAAA5555, 48'h010203040506, 48'hFFFFFFFFFFFF};
        for (i = 0; i < 8; i++) access(1'b1, i[2:0], vals[i], 1'b0, rd);
        for (i = 0; i < 8; i++) access(1'b0, i[2:0], 48'h0, 1'b0, rd);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Proves a caller holding req past done is not read as a second access.
    task automatic scenario_req_held_past_done();
        int i;
        int extra_done_count;
        int timeout_count;
        logic [47:0] rd;
        scenario_name = "req_held_past_done";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        @(negedge bus_clk);
        drv_req = 1'b1;
        drv_wr = 1'b1;
        drv_addr = 3'd2;
        drv_wdata = 48'hA5A5A5A5A5A5;
        timeout_count = 0;
        do begin
            @(negedge bus_clk);
            timeout_count++;
            if (timeout_count > 400)
                $fatal(1, "%s: timed out waiting for done", scenario_name);
        end while (!drv_done);
        if (drv_err !== 1'b0) $fatal(1, "%s: unexpected err on the write", scenario_name);
        ref_mem[2] = 48'hA5A5A5A5A5A5;
        extra_done_count = 0;
        for (i = 0; i < 5; i++) begin
            @(negedge bus_clk);
            if (drv_done) extra_done_count++;
        end
        drv_req = 1'b0;
        if (extra_done_count != 0)
            $fatal(1, "%s: saw %0d done pulses while req was held past the first, expected 0",
                   scenario_name, extra_done_count);
        access(1'b0, 3'd2, 48'h0, 1'b0, rd);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Proves back-to-back accesses at the minimum one-cycle req gap.
    task automatic scenario_back_to_back();
        int i;
        logic [47:0] rd;
        logic [47:0] val;
        scenario_name = "back_to_back";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        for (i = 0; i < 8; i++) begin
            val = 48'hC0FFEE000000 + 48'(i);
            access(1'b1, i[2:0], val, 1'b0, rd);
        end
        for (i = 0; i < 8; i++) access(1'b0, i[2:0], 48'h0, 1'b0, rd);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Proves a request that arrives while the memory side is held in reset
    // fails with err. The end-to-end monitor is the proof it never reaches
    // the memory array (a completion with err has no mem_port.enable behind
    // it, or the monitor's own check trips). The readback below only tests
    // row 3 itself on the pass where the recovery retry happens to land
    // back on row 3, since a read retry rotates its row on each attempt.
    task automatic scenario_mem_in_reset_at_request();
        logic [47:0] rd;
        logic [47:0] new_val;
        logic [2:0] row_read;
        int retries;
        scenario_name = "mem_in_reset_at_request";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        new_val = 48'hBAADF00DBAAD;
        @(negedge mem_clk);
        mem_rst_n = 1'b0;
        // Long enough at any clock ratio this suite builds for
        // alive_sync_stable to fall before the accesses below are issued.
        #(8 * (BUS_HALF_PERIOD + MEM_HALF_PERIOD));
        access(1'b1, 3'd3, new_val, 1'b1, rd);
        access(1'b0, 3'd3, 48'h0, 1'b1, rd);
        @(negedge mem_clk);
        mem_rst_n = 1'b1;
        // The memory side may still be arming right after release, so the
        // first read after reset uses the retry rule rather than a settle
        // delay: retry at the minimum req gap while err, until it clears.
        retry_access(1'b0, 3'd3, 48'h0, rd, row_read, retries);
        if (rd !== ref_mem[row_read])
            $fatal(1, "%s: row %0d read %h after the errored write, expected %h",
                   scenario_name, row_read, rd, ref_mem[row_read]);
        access(1'b1, 3'd3, new_val, 1'b0, rd);
        ref_mem[3] = new_val;
        access(1'b0, 3'd3, 48'h0, 1'b0, rd);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Sweeps a memory-side reset across the request window of one access,
    // then checks three further accesses recover cleanly. Bridge design.
    // BUS_IDLE and BUS_DRAIN answer with err while alive_sync_stable is low.
    // So a recovery access issued before the memory FSM is back at MEM_IDLE
    // is expected to see err and firmware is expected to retry it; that is
    // not a defect. A defect is a recovery access that comes back with
    // err=0 and the wrong data (a stale completion), or a done timeout, or
    // a recovery access that never clears err within the retry bound
    // (derived where max_retries is computed, below).
    task automatic scenario_mem_reset_mid_access_sweep();
        int step;
        int step_count;
        int fast_period;
        int max_offset;
        int offset_ns;
        int width;
        int timeout_count;
        int total_retries;
        int retries;
        logic got_err;
        logic [47:0] rd_local;
        logic [47:0] row4_new;
        logic [2:0] row_read;
        scenario_name = "mem_reset_mid_access_sweep";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        total_retries = 0;
        // The assertion offset steps in periods of the faster clock, not bus
        // periods: the defect this sweep is proving against needs a reset to
        // land inside a window one memory cycle wide, and when the memory
        // clock is the faster of the two, a bus-cycle step can land on
        // either side of that window without ever landing inside it.
        fast_period = 2 * ((BUS_HALF_PERIOD < MEM_HALF_PERIOD) ? BUS_HALF_PERIOD : MEM_HALF_PERIOD);
        // The ceiling covers the swept access's own latency (done_cycles)
        // plus the drain a reset landing near the end of it can still leave
        // running (drain_cycles), so the sweep reaches past the whole
        // window regardless of where in it the reset lands.
        max_offset = (done_cycles + drain_cycles + 4) * 2 * BUS_HALF_PERIOD;
        step_count = max_offset / fast_period + 1;
        $display("%s: %0d assertion-offset steps of %0d time units each",
                  scenario_name, step_count, fast_period);
        for (step = 0; step < step_count; step++) begin
            offset_ns = step * fast_period;
            for (width = 1; width <= 6; width++) begin
                @(negedge bus_clk);
                drv_req = 1'b1;
                drv_wr = 1'b0;
                drv_addr = 3'd1;
                drv_wdata = 48'h0;
                fork
                    mem_reset_pulse(offset_ns, width);
                    begin
                        timeout_count = 0;
                        #0;
                        while (!drv_done) begin
                            @(negedge bus_clk);
                            timeout_count++;
                            if (timeout_count > 400)
                                $fatal(1, "%s: offset=%0d width=%0d: timed out waiting for done",
                                       scenario_name, offset_ns, width);
                        end
                        got_err = drv_err;
                        rd_local = drv_rdata;
                    end
                join
                if (!got_err && rd_local !== ref_mem[1])
                    $fatal(1, "%s: offset=%0d width=%0d: row 1 read %h with err=0, expected %h",
                           scenario_name, offset_ns, width, rd_local, ref_mem[1]);
                // mem_reset_pulse ends on a mem_clk negedge, so join can
                // complete at any point relative to bus_clk; dropping req
                // there instead of at a bus negedge can leave it low for
                // less than one bus period, with no posedge in between for
                // req_taken to clear before the recovery access below
                // raises req again, and the bridge then reads that raise as
                // still the same request.
                @(negedge bus_clk);
                drv_req = 1'b0;

                // Recovery accesses: retry each while it returns err, at the
                // minimum req gap; retry_access fatals on a done timeout, a
                // hang, or too many attempts (the bound derived below). Once
                // one clears err, its data must be right; a wrong result
                // here is the real defect.
                retry_access(1'b0, 3'd2, 48'h0, rd_local, row_read, retries);
                total_retries += retries;
                if (rd_local !== ref_mem[row_read])
                    $fatal(1, "%s: offset=%0d width=%0d: row %0d recovery read %h, expected %h",
                           scenario_name, offset_ns, width, row_read, rd_local, ref_mem[row_read]);

                row4_new = 48'hAB0000000000 + 48'(step * 16) + 48'(width);
                retry_access(1'b1, 3'd4, row4_new, rd_local, row_read, retries);
                total_retries += retries;
                ref_mem[4] = row4_new;

                retry_access(1'b0, 3'd4, 48'h0, rd_local, row_read, retries);
                total_retries += retries;
                if (rd_local !== ref_mem[row_read])
                    $fatal(1, "%s: offset=%0d width=%0d: row %0d recovery readback %h, expected %h",
                           scenario_name, offset_ns, width, row_read, rd_local, ref_mem[row_read]);
            end
        end
        $display("%s: %0d recovery-access retries across the sweep (informational)",
                  scenario_name, total_retries);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Proves a bus-side reset mid-access leaves the memory holding either
    // the old or the new value, never a corrupted one, at reset-to-req-rise
    // alignments spanning the same range as the sweeps below.
    task automatic scenario_bus_reset_mid_access();
        int delay_cycles;
        logic [47:0] old_val;
        logic [47:0] new_val;
        logic [47:0] rd;
        logic [2:0] row_read;
        int retries;
        scenario_name = "bus_reset_mid_access";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        // The ceiling covers the swept access's own latency (done_cycles)
        // plus the drain a reset landing near the end of it can still leave
        // running (drain_cycles), so the sweep reaches past the whole
        // window regardless of where in it the reset lands.
        for (delay_cycles = 1; delay_cycles <= done_cycles + drain_cycles + 4; delay_cycles++) begin
            old_val = ref_mem[5];
            new_val = 48'h700000000000 + 48'(delay_cycles);
            @(negedge bus_clk);
            drv_req = 1'b1;
            drv_wr = 1'b1;
            drv_addr = 3'd5;
            drv_wdata = new_val;
            repeat (delay_cycles) @(posedge bus_clk);
            @(negedge bus_clk);
            bus_rst_n = 1'b0;
            drv_req = 1'b0;
            drv_wr = 1'b0;
            repeat (3) @(posedge bus_clk);
            @(negedge bus_clk);
            bus_rst_n = 1'b1;
            // Settle. Retry a read of row 0 while it returns err, the same
            // rule as any other post-reset access, with the timeout inside
            // retry_access as the guard.
            retry_access(1'b0, 3'd0, 48'h0, rd, row_read, retries);
            // A plain read check against a single expected value does not
            // apply to row 5 itself: it may legitimately hold either value,
            // so when the retry actually lands on row 5 (row_read == 5),
            // compare against both by hand. retry_access rotates a read's
            // row on each retry, so a retry can land on a different row
            // instead; that row's value is not in question here, so it is
            // checked the normal way, against ref_mem[row_read].
            retry_access(1'b0, 3'd5, 48'h0, rd, row_read, retries);
            if (row_read == 3'd5) begin
                if (rd !== old_val && rd !== new_val)
                    $fatal(1, "%s: delay=%0d: row 5 read %h, expected the old value %h or the new value %h",
                           scenario_name, delay_cycles, rd, old_val, new_val);
                ref_mem[5] = rd;
            end else if (rd !== ref_mem[row_read]) begin
                $fatal(1, "%s: delay=%0d: row %0d read %h, expected %h",
                       scenario_name, delay_cycles, row_read, rd, ref_mem[row_read]);
            end
        end
        new_val = 48'h7F7F7F7F7F7F;
        access(1'b1, 3'd5, new_val, 1'b0, rd);
        ref_mem[5] = new_val;
        access(1'b0, 3'd5, 48'h0, 1'b0, rd);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Proves recovery from a memory-side reset with the bus idle: the first
    // access afterward may still see the memory arming and fail with err,
    // but it must not take more than a handful of attempts, and the next
    // access must succeed cleanly.
    task automatic scenario_mem_reset_between_accesses();
        logic [47:0] rd;
        logic [47:0] new_val;
        logic [2:0] row_read;
        int retries;
        scenario_name = "mem_reset_between_accesses";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        mem_reset_pulse(0, 2);
        retry_access(1'b0, 3'd0, 48'h0, rd, row_read, retries);
        new_val = 48'h777777777777;
        access(1'b1, 3'd6, new_val, 1'b0, rd);
        ref_mem[6] = new_val;
        access(1'b0, 3'd6, 48'h0, 1'b0, rd);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Sweeps a bus-side reset across the request window of a read, mirror of
    // scenario_mem_reset_mid_access_sweep. The tb driver drops req when it
    // asserts bus_rst_n, since the real caller sits in the bus domain and is
    // reset with it, so the in-flight read is abandoned rather than checked.
    // After release and a settle, every recovery access is data-checked
    // under the retry rule; a defect is a recovery access that comes back
    // with err=0 and the wrong data, or a done timeout.
    task automatic scenario_bus_reset_mid_access_sweep();
        int step;
        int step_count;
        int fast_period;
        int max_offset;
        int offset_ns;
        int width;
        int retries;
        logic [47:0] rd;
        logic [47:0] row4_new;
        logic [2:0] row_read;
        scenario_name = "bus_reset_mid_access_sweep";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        // Same reasoning as scenario_mem_reset_mid_access_sweep: the
        // assertion offset steps in periods of the faster clock, since the
        // defect window is one clock cycle wide in whichever domain is
        // faster, and a step sized to the slower domain's cycle can straddle
        // it.
        fast_period = 2 * ((BUS_HALF_PERIOD < MEM_HALF_PERIOD) ? BUS_HALF_PERIOD : MEM_HALF_PERIOD);
        // The ceiling covers the swept access's own latency (done_cycles)
        // plus the drain a reset landing near the end of it can still leave
        // running (drain_cycles), so the sweep reaches past the whole
        // window regardless of where in it the reset lands.
        max_offset = (done_cycles + drain_cycles + 4) * 2 * BUS_HALF_PERIOD;
        step_count = max_offset / fast_period + 1;
        $display("%s: %0d assertion-offset steps of %0d time units each",
                  scenario_name, step_count, fast_period);
        for (step = 0; step < step_count; step++) begin
            offset_ns = step * fast_period;
            for (width = 1; width <= 6; width++) begin
                @(negedge bus_clk);
                drv_req = 1'b1;
                drv_wr = 1'b0;
                drv_addr = 3'd1;
                drv_wdata = 48'h0;
                #(offset_ns);
                drv_req = 1'b0;
                @(negedge bus_clk);
                bus_rst_n = 1'b0;
                repeat (width) @(posedge bus_clk);
                @(negedge bus_clk);
                bus_rst_n = 1'b1;
                repeat (4) @(posedge bus_clk);

                retry_access(1'b0, 3'd2, 48'h0, rd, row_read, retries);
                if (rd !== ref_mem[row_read])
                    $fatal(1, "%s: offset=%0d width=%0d: row %0d recovery read %h, expected %h",
                           scenario_name, offset_ns, width, row_read, rd, ref_mem[row_read]);

                row4_new = 48'hCD0000000000 + 48'(step * 16) + 48'(width);
                retry_access(1'b1, 3'd4, row4_new, rd, row_read, retries);
                ref_mem[4] = row4_new;

                retry_access(1'b0, 3'd4, 48'h0, rd, row_read, retries);
                if (rd !== ref_mem[row_read])
                    $fatal(1, "%s: offset=%0d width=%0d: row %0d recovery readback %h, expected %h",
                           scenario_name, offset_ns, width, row_read, rd, ref_mem[row_read]);

                retry_access(1'b0, 3'd1, 48'h0, rd, row_read, retries);
                if (rd !== ref_mem[row_read])
                    $fatal(1, "%s: offset=%0d width=%0d: row %0d recovery read %h, expected %h",
                           scenario_name, offset_ns, width, row_read, rd, ref_mem[row_read]);
            end
        end
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Both resets overlap mid-access: bus_rst_n asserts one bus cycle before
    // mem_rst_n, and mem_rst_n is released 2 mem cycles after bus_rst_n is
    // released, so the memory side is still in reset for a stretch after
    // the bus side has started reconnecting. Same recovery sequence and
    // defect definition as scenario_bus_reset_mid_access_sweep.
    task automatic scenario_both_reset_mid_access();
        int retries;
        logic [47:0] rd;
        logic [47:0] row4_new;
        logic [2:0] row_read;
        scenario_name = "both_reset_mid_access";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        @(negedge bus_clk);
        drv_req = 1'b1;
        drv_wr = 1'b0;
        drv_addr = 3'd1;
        drv_wdata = 48'h0;
        @(negedge bus_clk);
        drv_req = 1'b0;
        bus_rst_n = 1'b0;
        @(posedge bus_clk);
        @(negedge mem_clk);
        mem_rst_n = 1'b0;
        repeat (3) @(posedge bus_clk);
        @(negedge bus_clk);
        bus_rst_n = 1'b1;
        repeat (2) @(posedge mem_clk);
        @(negedge mem_clk);
        mem_rst_n = 1'b1;
        repeat (4) @(posedge bus_clk);

        retry_access(1'b0, 3'd2, 48'h0, rd, row_read, retries);
        if (rd !== ref_mem[row_read])
            $fatal(1, "%s: row %0d recovery read %h, expected %h",
                   scenario_name, row_read, rd, ref_mem[row_read]);

        row4_new = 48'hEF00000000EF;
        retry_access(1'b1, 3'd4, row4_new, rd, row_read, retries);
        ref_mem[4] = row4_new;

        retry_access(1'b0, 3'd4, 48'h0, rd, row_read, retries);
        if (rd !== ref_mem[row_read])
            $fatal(1, "%s: row %0d recovery readback %h, expected %h",
                   scenario_name, row_read, rd, ref_mem[row_read]);

        retry_access(1'b0, 3'd1, 48'h0, rd, row_read, retries);
        if (rd !== ref_mem[row_read])
            $fatal(1, "%s: row %0d recovery read %h, expected %h",
                   scenario_name, row_read, rd, ref_mem[row_read]);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Reproduces the one-cycle alive pulse the module header describes: a
    // memory reset lands while a read of row 1 is outstanding, so the bus
    // answers err from BUS_WAIT_ACK and moves to BUS_DRAIN with req_latch
    // still owed an answer. A one-bus-cycle bus_rst_n pulse is then swept
    // across the done_cycles bus cycles after that err, landing BUS_ARM's
    // own wait for alive_sync_stable to fall at a different point in the
    // drain on each pass. Recovery must still be data-clean at every
    // offset; a stale completion or a done timeout is the real defect.
    task automatic scenario_bus_reset_during_drain();
        int offset;
        int retries;
        int timeout_count;
        int mem_reset_width;
        logic got_err;
        logic [47:0] rd;
        logic [47:0] row4_new;
        logic [2:0] row_read;
        scenario_name = "bus_reset_during_drain";
        $display("SCENARIO %s", scenario_name);
        // A crossing only guarantees the receiving domain observes a pulse
        // if the source holds it for at least one receiving-domain period;
        // a memory reset narrower than a bus period can resolve (both the
        // reset and the stale-request answer it forces) before the bus ever
        // samples alive low, reaching BUS_WAIT_ACK_LOW on the ack alone
        // without ever visiting BUS_DRAIN. This scenario means to land in
        // BUS_DRAIN specifically, so the pulse is sized in bus periods, not
        // left at the fixed few memory cycles the other reset sweeps use.
        // It is two bus periods converted to memory cycles, plus a floor of
        // 2 memory cycles so the bus is sure to see alive fall.
        mem_reset_width = (4 * BUS_HALF_PERIOD) / MEM_HALF_PERIOD + 2;
        for (offset = 0; offset <= done_cycles; offset++) begin
            stale_starts = 0;
            // Wait for a clean BUS_IDLE base state before racing the reset,
            // checked on signals rather than the state code: bus_alive high
            // rules out BUS_ARM, and with alive_sync_stable high and
            // ack_sync_stable low, BUS_CONNECT and BUS_WAIT_ACK_LOW both
            // leave within one cycle, so the extra negedge below before
            // raising drv_req lands in BUS_IDLE. req_latch low rules out a
            // stale access from the previous iteration or scenario still
            // draining. Without this, the read below can be accepted
            // straight into an immediate err (alive_sync_stable already low
            // from this iteration's own reset) instead of reaching
            // BUS_WAIT_ACK first, and never drains through BUS_DRAIN at all.
            timeout_count = 0;
            while (!(dut.bus_alive && dut.alive_sync_stable && !dut.ack_sync_stable && !dut.req_latch)) begin
                @(negedge bus_clk);
                timeout_count++;
                if (timeout_count > 200)
                    $fatal(1, "%s: offset=%0d: never reached a clean BUS_IDLE base state",
                           scenario_name, offset);
            end
            @(negedge bus_clk);
            drv_req = 1'b1;
            drv_wr = 1'b0;
            drv_addr = 3'd1;
            drv_wdata = 48'h0;
            fork
                mem_reset_pulse(0, mem_reset_width);
                begin
                    timeout_count = 0;
                    #0;
                    while (!drv_done) begin
                        @(negedge bus_clk);
                        timeout_count++;
                        if (timeout_count > 400)
                            $fatal(1, "%s: offset=%0d: timed out waiting for done",
                                   scenario_name, offset);
                    end
                    got_err = drv_err;
                end
            join
            if (!got_err)
                $fatal(1, "%s: offset=%0d: expected err from the memory reset, got none",
                       scenario_name, offset);
            // n_bus_state computed on the edge that produced done/err takes
            // effect on the next edge; step once more before checking.
            // Only BUS_WAIT_ACK's alive-low branch reports err while keeping
            // req_latch high, and it moves to BUS_DRAIN, so req_latch still
            // being 1 here means the errored request is being held for the
            // drain rather than answered and dropped.
            @(negedge bus_clk);
            if (!dut.req_latch)
                $fatal(1, "%s: offset=%0d: expected the errored request to be held for the drain",
                       scenario_name, offset);
            drv_req = 1'b0;
            repeat (offset) @(posedge bus_clk);
            @(negedge bus_clk);
            bus_rst_n = 1'b0;
            @(posedge bus_clk);
            @(negedge bus_clk);
            bus_rst_n = 1'b1;

            // Usual recovery sequence: retry each while it returns err, at
            // the minimum req gap, with data checks against ref_mem.
            retry_access(1'b0, 3'd2, 48'h0, rd, row_read, retries);
            if (rd !== ref_mem[row_read])
                $fatal(1, "%s: offset=%0d: row %0d recovery read %h, expected %h",
                       scenario_name, offset, row_read, rd, ref_mem[row_read]);

            row4_new = 48'hDE0000000000 + 48'(offset);
            retry_access(1'b1, 3'd4, row4_new, rd, row_read, retries);
            ref_mem[4] = row4_new;

            retry_access(1'b0, 3'd4, 48'h0, rd, row_read, retries);
            if (rd !== ref_mem[row_read])
                $fatal(1, "%s: offset=%0d: row %0d recovery readback %h, expected %h",
                       scenario_name, offset, row_read, rd, ref_mem[row_read]);

            retry_access(1'b0, 3'd1, 48'h0, rd, row_read, retries);
            if (rd !== ref_mem[row_read])
                $fatal(1, "%s: offset=%0d: row %0d recovery read %h, expected %h",
                       scenario_name, offset, row_read, rd, ref_mem[row_read]);

            $display("%s: offset=%0d: stale_starts=%0d (informational)",
                      scenario_name, offset, stale_starts);
        end
        $display("PASS %s", scenario_name);
    endtask

    // Targets the request that arrives inside the two-bus-cycle window
    // after a memory reset lands, when the bus still reads the memory as
    // alive. The bus accepts it, then abandons it once alive falls, and the
    // memory may still execute it after its own reset clears. The next
    // access must not be completed by that stale answer. Sweeps the reset
    // width across several memory cycles and the assertion-to-request offset
    // across a short, fixed range, since the window in question is only a
    // couple of bus cycles wide, unlike the ack-crossing range the other
    // sweeps size from done_cycles.
    task automatic scenario_mem_reset_then_request_sweep();
        int width;
        int step;
        int step_count;
        int fast_period;
        int max_offset;
        int offset_ns;
        int iteration;
        int retries;
        logic [2:0] row_a;
        logic [2:0] row_b;
        logic [2:0] row_read;
        logic [47:0] rd;
        scenario_name = "mem_reset_then_request_sweep";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        // Same reasoning as the other sweeps: step in periods of the faster
        // clock so the offset can land inside a window one memory cycle
        // wide regardless of which domain is faster.
        fast_period = 2 * ((BUS_HALF_PERIOD < MEM_HALF_PERIOD) ? BUS_HALF_PERIOD : MEM_HALF_PERIOD);
        max_offset = 4 * 2 * BUS_HALF_PERIOD;
        step_count = max_offset / fast_period + 1;
        $display("%s: %0d assertion-offset steps of %0d time units each",
                  scenario_name, step_count, fast_period);
        iteration = 0;
        for (width = 1; width <= 6; width++) begin
            for (step = 0; step < step_count; step++) begin
                offset_ns = step * fast_period;
                row_a = 3'(iteration % 8);
                row_b = 3'((iteration + 1) % 8);
                fork
                    mem_reset_pulse(0, width);
                    begin
                        #(offset_ns);
                        retry_access(1'b0, row_a, 48'h0, rd, row_read, retries);
                        if (rd !== ref_mem[row_read])
                            $fatal(1, "%s: width=%0d offset=%0d: row %0d read %h, expected %h",
                                   scenario_name, width, offset_ns, row_read, rd, ref_mem[row_read]);
                        retry_access(1'b0, row_b, 48'h0, rd, row_read, retries);
                        if (rd !== ref_mem[row_read])
                            $fatal(1, "%s: width=%0d offset=%0d: row %0d read %h, expected %h",
                                   scenario_name, width, offset_ns, row_read, rd, ref_mem[row_read]);
                    end
                join
                // Settle. A plain retry_access read waits out the rest of
                // the reset pulse and the reconnect handshake before the
                // next iteration starts a fresh one.
                retry_access(1'b0, 3'd0, 48'h0, rd, row_read, retries);
                if (rd !== ref_mem[row_read])
                    $fatal(1, "%s: width=%0d offset=%0d: settle read row %0d returned %h, expected %h",
                           scenario_name, width, offset_ns, row_read, rd, ref_mem[row_read]);
                iteration++;
            end
        end
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Measures the connect handshake's three legs directly, each in the
    // domain where it happens, rather than folding all three into one
    // bus-cycle total that a fast memory clock can shrink to less than a
    // workable tolerance. Runs after scenario_random_traffic so the jitter
    // random stream random traffic draws from is unchanged from before this
    // scenario existed. It can no longer rely on scenario_back_to_back's row
    // 0 value surviving random traffic, so it starts by writing a known
    // value to row 0 with retry_access and reading it back once;
    // random_traffic's own join_any already released both resets, and if it
    // left the design mid-reconnect, this retry_access absorbs that.
    // The reset sequence asserts bus_rst_n at a bus negedge and waits for
    // the following bus posedge, the edge that clears bus_alive, before
    // asserting mem_rst_n at a memory negedge. Asserting the memory reset
    // any earlier lets the memory leave reset onto a stale bus_alive of 1,
    // which produces the header's alive pulse and leaves L1 measuring that
    // pulse instead of the handshake. mem_rst_n then holds for two memory
    // cycles and releases at a memory negedge, before bus_rst_n releases at
    // a bus negedge; the memory may release first because its
    // bus_alive_sync chain holds zeros through the wait and MEM_ARM does
    // not exit until bus_alive itself falls. The leg counters therefore
    // start from the bus_rst_n rise itself, watched by a fork branch armed
    // before the reset sequence runs, rather than from a $time read taken
    // after the sequence completes, which can already have missed a real
    // bus edge that fired earlier in the sequence.
    //
    // Each leg pairs a free-running edge counter against a guarded wait on
    // the signal's own positive-edge event (`@(posedge dut.bus_alive)` and
    // so on, skipped when the signal already reads 1, since a signal that
    // never falls first has no rising edge left to wait for; this is what
    // keeps L1 and L2 at 0 under +no_reset_tests, where bus_alive and alive
    // are already at their post-power-on values), racing them in a fork
    // with join_any and disabling the counter once the wait completes. The
    // event wait only wakes once the simulator has settled the signal's new
    // value, so it always reflects the same edge the counter's own last
    // increment came from; reading dut.bus_alive or dut.alive directly
    // inside the counting loop's own condition
    // instead would race the DUT's clocked update on any edge the bus and
    // memory clocks share, which happens at equal half periods or any exact
    // ratio, since which of the two processes sensitive to that edge runs
    // first is scheduling order, not RTL behaviour. L1 counts bus edges
    // from the bus_rst_n rise until dut.bus_alive reads 1, expected 3
    // exactly (two alive_sync stages capturing the memory's alive of 0
    // while it still sits in MEM_ARM, then BUS_ARM's own reaction edge). L2
    // counts memory edges strictly after the bus edge L1 ends on until
    // dut.alive reads 1, expected 5 (four bus_alive_sync stages plus
    // MEM_ARM's reaction edge); tolerance 1 covers a memory edge landing at
    // the same simulation time as that bus edge. L3 counts bus edges
    // strictly after the memory edge L2 ends on until dut.start_access
    // pulses, expected 4 (two alive_sync stages, BUS_CONNECT's reaction
    // edge, BUS_IDLE's accept edge); tolerance 2 covers a coinciding edge
    // and the retry loop's req sitting low for one bus cycle between
    // attempts, which can push acceptance one cycle later. That retry loop
    // (soft_access at the minimum req gap) has to stay active through the
    // reset sequence and all three legs for BUS_IDLE to ever accept and
    // produce the start_access pulse L3 ends on, so the reset sequence,
    // the leg counters and the retry loop run as three branches of one
    // fork. Each leg restates one piece of the module header's
    // connect-cost figure and pins it to the RTL; measuring it in its own
    // domain catches an extra synchroniser stage at every clock ratio,
    // including where the memory clock is faster than the bus, unlike a
    // bus-cycle total, and catches a slower reconnect that the retry bound,
    // sized with margin rather than against the figure itself, absorbs
    // without ever timing out. Under A2C_CDC_JITTER only an upper bound is
    // checked on each leg, since a held synchroniser stage adds cycles a
    // two-sided tolerance would then have to cover on the low side too: L1
    // up to 5, L2 up to 7, L3 up to 8, one held cycle per crossing the leg
    // contains, plus one more for L3 covering the accept's own dependence
    // on ack_sync_stable falling. The three legs and the total bus cycles
    // from the bus_rst_n rise to the first clean completion (informational
    // only) print in every configuration. The fatal checks are skipped,
    // with a printed line, under +no_reset_tests: A2C_RESET_NONE has no
    // live reset past time 0 (flops.sv's A2C_RESET_NONE body never reads
    // rstSig), so bus_alive and alive already read their post-power-on
    // values before this reset pulse and L1 and L2 measure 0, with nothing
    // meaningful to check against the connect-cost figure.
    task automatic scenario_connect_latency();
        int l1, l2, l3;
        int total_cycles;
        int attempts;
        time release_time;
        time done_time;
        logic got_err;
        logic [47:0] rd;
        logic [2:0] row_read;
        int retries;
        logic [47:0] known_val;
        scenario_name = "connect_latency";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;

        known_val = 48'h5CA1AB1E5EED;
        retry_access(1'b1, 3'd0, known_val, rd, row_read, retries);
        ref_mem[0] = known_val;
        retry_access(1'b0, 3'd0, 48'h0, rd, row_read, retries);
        if (rd !== ref_mem[row_read])
            $fatal(1, "%s: row %0d readback %h before the reset, expected %h",
                   scenario_name, row_read, rd, ref_mem[row_read]);

        l1 = 0;
        l2 = 0;
        l3 = 0;
        attempts = 0;
        fork
            begin : reset_seq
                @(negedge bus_clk); bus_rst_n = 1'b0;
                @(posedge bus_clk);                 // bus_alive clears on this edge
                @(negedge mem_clk); mem_rst_n = 1'b0;
                repeat (2) @(posedge mem_clk);
                @(negedge mem_clk); mem_rst_n = 1'b1;   // memory releases into an all-zero
                                                        // bus_alive_sync chain and waits in MEM_ARM
                @(negedge bus_clk); bus_rst_n = 1'b1;   // alive is 0 and stays 0 from here
            end
            begin : legs
                @(posedge bus_rst_n);
                release_time = $time;
                fork
                    begin
                        forever begin
                            @(posedge bus_clk);
                            l1++;
                        end
                    end
                    if (!dut.bus_alive) @(posedge dut.bus_alive);
                join_any
                disable fork;
                fork
                    begin
                        forever begin
                            @(posedge mem_clk);
                            l2++;
                        end
                    end
                    if (!dut.alive) @(posedge dut.alive);
                join_any
                disable fork;
                fork
                    begin
                        forever begin
                            @(posedge bus_clk);
                            l3++;
                        end
                    end
                    if (!dut.start_access) @(posedge dut.start_access);
                join_any
                disable fork;
            end
            begin : req_loop
                forever begin
                    soft_access(1'b0, 3'd0, 48'h0, got_err, rd);
                    attempts++;
                    if (!got_err) break;
                    if (attempts > 500)
                        $fatal(1, "%s: still err after %0d attempts, never reconnected",
                               scenario_name, attempts);
                end
            end
        join
        done_time = $time;
        if (rd !== ref_mem[0])
            $fatal(1, "%s: row 0 read %h, expected %h", scenario_name, rd, ref_mem[0]);
        total_cycles = int'((done_time - release_time) / (2 * BUS_HALF_PERIOD));

        $display("%s: L1=%0d L2=%0d L3=%0d total_bus_cycles=%0d (informational)",
                  scenario_name, l1, l2, l3, total_cycles);

        if ($test$plusargs("no_reset_tests")) begin
            $display("%s: skipped, no_reset_tests selects a style with no live mid-run reset to reconnect from",
                      scenario_name);
        end else begin
`ifdef A2C_CDC_JITTER
            if (l1 > 3 + 2)
                $fatal(1, "%s: leg L1 measured %0d bus edges, expected at most %0d under jitter",
                       scenario_name, l1, 3 + 2);
            if (l2 > 5 + 2)
                $fatal(1, "%s: leg L2 measured %0d memory edges, expected at most %0d under jitter",
                       scenario_name, l2, 5 + 2);
            if (l3 > 4 + 2 + 2)
                $fatal(1, "%s: leg L3 measured %0d bus edges, expected at most %0d under jitter",
                       scenario_name, l3, 4 + 2 + 2);
`else
            if (l1 != 3)
                $fatal(1, "%s: leg L1 measured %0d bus edges, expected %0d", scenario_name, l1, 3);
            if (l2 < 5 - 1 || l2 > 5 + 1)
                $fatal(1, "%s: leg L2 measured %0d memory edges, expected %0d +/- %0d",
                       scenario_name, l2, 5, 1);
            if (l3 < 4 - 2 || l3 > 4 + 2)
                $fatal(1, "%s: leg L3 measured %0d bus edges, expected %0d +/- %0d",
                       scenario_name, l3, 4, 2);
`endif
        end
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // Random read/write traffic against every row, concurrent with random
    // memory- and bus-side resets, seeded from the +seed plusarg so a
    // failure is reproducible. Scoreboard per row: row_cand holds every
    // value the row could actually hold. A clean access (err=0) collapses it
    // to a single confirmed value. A write with err=1, or one abandoned by a
    // bus reset, does not collapse it: the header allows such an access to
    // have executed anyway, so its value joins the row's existing
    // candidates rather than replacing them, which is what a second
    // unresolved write to the same row before the first resolves needs. A
    // read with err=0 must match one of the row's candidates and resolves
    // the row to that single value. A read with err=1 has nothing to check.
    // A hang, neither done nor err within the timeout, is fatal, same as
    // every other access task in this file.
    //
    // The access loop watches bus_rst_n directly rather than a separate
    // flag: it polls once per bus_clk edge and the reset pulser below holds
    // bus_rst_n low for at least one full bus cycle, so the loop cannot miss
    // it. Finding it low is read as the access having been abandoned,
    // whether or not done also happened to settle that same edge.
    //
    // Each access here is single-shot rather than routed through
    // retry_access, so max_retries and its bound do not apply. An errored
    // access is simply scored and the loop moves on; with resets landing at
    // random times the number of errored accesses in a run is arbitrary.
    task automatic scenario_random_traffic();
        localparam int N = 1500;
        int i;
        logic wr_pick;
        logic [2:0] addr_pick;
        logic [47:0] wdata_pick;
        logic got_err;
        logic [47:0] rd;
        logic matched;
        int timeout_count;
        int access_count;
        int error_count;
        int mem_reset_count;
        int bus_reset_count;
        logic [47:0] row_cand [8][$];
        int r;
        int mem_gap, mem_width;
        int bus_gap, bus_width;
        logic run_bus_resets;

        scenario_name = "random_traffic";
        $display("SCENARIO %s", scenario_name);
        stale_starts = 0;
        access_count = 0;
        error_count = 0;
        mem_reset_count = 0;
        bus_reset_count = 0;
        run_bus_resets = !$test$plusargs("no_reset_tests");
        for (r = 0; r < 8; r++) begin
            row_cand[r] = {};
            row_cand[r].push_back(ref_mem[r]);
        end

        fork
            // N random accesses at the minimum request gap.
            begin
                for (i = 0; i < N; i++) begin
                    wr_pick = 1'($urandom_range(1));
                    addr_pick = 3'($urandom_range(7));
                    wdata_pick = 48'({$urandom(), $urandom()});
                    @(negedge bus_clk);
                    drv_req = 1'b1;
                    drv_wr = wr_pick;
                    drv_addr = addr_pick;
                    drv_wdata = wdata_pick;
                    timeout_count = 0;
                    #0;
                    while (!drv_done && bus_rst_n) begin
                        @(negedge bus_clk);
                        timeout_count++;
                        if (timeout_count > 400)
                            $fatal(1, "%s: access %0d timed out waiting for done", scenario_name, i);
                    end
                    access_count++;
                    if (!bus_rst_n) begin
                        drv_req = 1'b0;
                        if (wr_pick) row_cand[addr_pick].push_back(wdata_pick);
                    end else begin
                        got_err = drv_err;
                        rd = drv_rdata;
                        if (got_err) error_count++;
                        if (wr_pick) begin
                            if (!got_err) begin
                                row_cand[addr_pick] = {};
                                row_cand[addr_pick].push_back(wdata_pick);
                            end else begin
                                row_cand[addr_pick].push_back(wdata_pick);
                            end
                        end else if (!got_err) begin
                            matched = 1'b0;
                            foreach (row_cand[addr_pick][k])
                                if (rd === row_cand[addr_pick][k]) matched = 1'b1;
                            if (!matched)
                                $fatal(1, "%s: access %0d: row %0d read %h, not among %0d still-possible value(s)",
                                       scenario_name, i, addr_pick, rd, row_cand[addr_pick].size());
                            row_cand[addr_pick] = {};
                            row_cand[addr_pick].push_back(rd);
                        end
                        drv_req = 1'b0;
                    end
                end
            end

            // Memory-side reset pulser: random width 1-6 memory cycles,
            // random gap 20-200 memory cycles between pulses. Runs
            // unconditionally; a memory reset has no caller to abandon.
            begin
                forever begin
                    mem_gap = 20 + $urandom_range(180);
                    repeat (mem_gap) @(posedge mem_clk);
                    mem_width = 1 + $urandom_range(5);
                    mem_reset_pulse(0, mem_width);
                    mem_reset_count++;
                end
            end

            // Bus-side reset pulser, reset-capable styles only: random width
            // 1-4 bus cycles, random gap 50-400 bus cycles between pulses.
            // Stays a forever loop either way so it never ends this fork's
            // join_any on its own under +no_reset_tests.
            begin
                forever begin
                    if (run_bus_resets) begin
                        bus_gap = 50 + $urandom_range(350);
                        repeat (bus_gap) @(posedge bus_clk);
                        bus_width = 1 + $urandom_range(3);
                        @(negedge bus_clk);
                        bus_rst_n = 1'b0;
                        repeat (bus_width) @(posedge bus_clk);
                        @(negedge bus_clk);
                        bus_rst_n = 1'b1;
                        bus_reset_count++;
                    end else begin
                        @(posedge bus_clk);
                    end
                end
            end
        join_any
        disable fork;
        // A pulser killed mid-pulse by disable fork can leave its reset
        // asserted; release both so a later scenario never starts in reset.
        @(negedge bus_clk);
        bus_rst_n = 1'b1;
        @(negedge mem_clk);
        mem_rst_n = 1'b1;

        $display("%s: %0d accesses, %0d errors, %0d memory resets, %0d bus resets",
                  scenario_name, access_count, error_count, mem_reset_count, bus_reset_count);
        $display("%s: stale_starts=%0d (informational)", scenario_name, stale_starts);
        $display("PASS %s", scenario_name);
    endtask

    // ------------------------------------------------------------------ run --

    initial begin
        int startup_retries;
        logic [47:0] startup_rd;
        logic [2:0] startup_row;
        int seed;
        int connect_cost_cycles;
        int jitter_allowance_cycles;
        int reset_width_cycles;

        // Seeds $urandom before anything that draws from it, including the
        // jitter driver above, which starts drawing on the first clock edge.
        if (!$value$plusargs("seed=%d", seed)) seed = 1;
        void'($urandom(seed));
        $display("seed: %0d (used for jitter and scenario_random_traffic)", seed);

        if ($test$plusargs("trace")) begin
            $dumpfile("wave.vcd");
            $dumpvars(0, memory_reg_bridge_tb);
        end
        bus_clk = 1'b0;
        mem_clk = 1'b0;
        // Both resets start low at time 0, before either clock has toggled,
        // so a four-state simulator never evaluates a checker against X;
        // bus_reset()/mem_reset_pulse() below release them the normal way.
        bus_rst_n = 1'b0;
        mem_rst_n = 1'b0;
        drv_req = 1'b0;
        drv_wr = 1'b0;
        drv_addr = 3'd0;
        drv_wdata = 48'h0;
        scenario_name = "startup";

        fork
            bus_reset(4);
            mem_reset_pulse(0, 4);
        join
        // Settle. bus_alive_sync_stable and alive_sync_stable need a few
        // cycles of their own domain after release before the first access,
        // same margin as the reset scenarios below use.
        #(8 * (BUS_HALF_PERIOD + MEM_HALF_PERIOD));

        // Connect-cost cycles in the bus domain, sized for a retry bound
        // rather than restating the module header's connect-cost figure
        // (item 2, measured from a joint reset release). A retry after a
        // bus-only reset instead waits out alive_sync_stable's fall in
        // BUS_ARM and then its rise in BUS_CONNECT, two transitions rather
        // than the header's one release-to-connect pass, and jitter's held
        // transitions add further delay at every clock ratio. Measured
        // directly with the tb across the suite's clock ratios under
        // A2C_CDC_JITTER, worst case scaled with MEM_HALF_PERIOD /
        // BUS_HALF_PERIOD as the header's connect-cost figure does; the
        // multiplier below carries margin over every measurement rather
        // than fitting the worst one exactly. Needed before done_cycles is
        // known, so the startup retry below is capped on cycles directly
        // rather than attempts; an attempt costs at least one bus cycle, so
        // a cycle count is also a safe attempts bound.
        connect_cost_cycles = 6 + (12 * MEM_HALF_PERIOD + BUS_HALF_PERIOD - 1) / BUS_HALF_PERIOD;
`ifdef A2C_CDC_JITTER
        jitter_allowance_cycles = 6;
`else
        jitter_allowance_cycles = 0;
`endif
        max_retries = connect_cost_cycles + jitter_allowance_cycles;

        // Startup check: the connect handshake after a shared reset costs a
        // few synchroniser delays on each leg (module header comment), so
        // the very first access may still see err. Retry under the normal
        // rule and report how many attempts it took.
        retry_access(1'b1, 3'd0, 48'h0, startup_rd, startup_row, startup_retries);
        $display("startup: %0d retries before the first access succeeded (informational)",
                  startup_retries);

        // Sizes the sweeps' offset_ns range from actual done and drain
        // latencies, since both differ by clock ratio and a fixed guess
        // would miss the ack-crossing window at some of them.
        calibrate_done_cycles(drain_cycles, done_cycles);
        $display("calibration: drain_cycles=%0d bus cycles from an access to a genuinely idle bus, done_cycles=%0d bus cycles for one plain read from there (informational)",
                  drain_cycles, done_cycles);

        // Checked bound on retry_access's attempts. connect_cost_cycles and
        // jitter_allowance_cycles are as computed above. reset_width_cycles
        // is the widest reset a retry_access caller can still be holding
        // concurrently with the call, which is scenario_mem_reset_then_
        // request_sweep's own memory reset, up to 6 memory cycles, also
        // converted to bus cycles and rounded up. The three added together
        // are a bus-cycle budget for reconnecting and answering. A retry
        // that comes back err is rejected combinationally in BUS_ARM,
        // BUS_CONNECT or BUS_IDLE without waiting out a read latency, so it
        // costs about one bus cycle (the minimum req gap), not done_cycles;
        // the cycle budget is used directly as the attempts bound rather
        // than divided by done_cycles, which would undercount attempts.
        reset_width_cycles = (6 * MEM_HALF_PERIOD + BUS_HALF_PERIOD - 1) / BUS_HALF_PERIOD;
        max_retries = connect_cost_cycles + jitter_allowance_cycles + reset_width_cycles;

        scenario_write_read_all();
        scenario_req_held_past_done();
        scenario_back_to_back();

        if (!$test$plusargs("no_reset_tests")) begin
            scenario_mem_in_reset_at_request();
            scenario_mem_reset_mid_access_sweep();
            scenario_bus_reset_mid_access();
            scenario_bus_reset_mid_access_sweep();
            scenario_both_reset_mid_access();
            scenario_bus_reset_during_drain();
            // No bridge flop responds to mem_rst_n in A2C_RESET_NONE, the
            // style +no_reset_tests selects, so these two have nothing to
            // exercise there either.
            scenario_mem_reset_between_accesses();
            scenario_mem_reset_then_request_sweep();
        end

        scenario_random_traffic();

        scenario_connect_latency();

        $display("retry bound: max_retries=%0d attempts, largest attempt count any retry_access call actually used=%0d (informational)",
                  max_retries, max_attempts_seen);
        $display("TB_PASS");
        $finish;
    end

endmodule : memory_reg_bridge_tb
