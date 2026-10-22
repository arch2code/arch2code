// Loopback tests of a2c_replay_drain on replay logs whose lanes are
// lb_fake_lanes, which the test sets directly, so a test can start a
// transaction on the exact edge it needs. Included in a2c_uvm_loopback_pkg
// after a2c_model_cmp_lb_tests.svh.

    typedef a2c_replay_log #(bit) lb_bit_log_t;

    // The lanes of a Mode B responder with no pins behind them.
    class lb_fake_lanes implements a2c_replay_lanes;
        bit          busy[2];
        int unsigned starts[2];
        int unsigned done[2];

        virtual function bit lane_busy(a2c_lane_e l);
            return busy[l];
        endfunction

        virtual function int unsigned lane_starts(a2c_lane_e l);
            return starts[l];
        endfunction

        virtual function int unsigned lane_done(a2c_lane_e l);
            return done[l];
        endfunction
    endclass : lb_fake_lanes

    // Replay logs on fake lanes. The test drops its objection at a falling
    // edge of clk, so the drain's first clock on clk is the rising edge
    // after the drop. on_ready() runs on each of the run phase's
    // phase_ready_to_end() calls, in the time step the drain starts or
    // ends.
    class lb_drain_base extends lb_mode_b_base;
        lb_bit_log_t  logs[$];
        lb_fake_lanes lanes[$];
        realtime      drop_time;
        realtime      ready_time[$];

        `uvm_component_utils(lb_drain_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected function void add_log(string name, virtual a2c_clk_if clk, int unsigned quiet, int unsigned deadline);
            lb_bit_log_t  log = lb_bit_log_t::type_id::create(name, this);
            lb_fake_lanes l = new();
            log.driver                = l;
            log.clk_vif               = clk;
            log.drain_quiet_cycles    = quiet;
            log.drain_deadline_cycles = deadline;
            logs.push_back(log);
            lanes.push_back(l);
        endfunction

        // Starts a transaction on lane l of log k now, busy until finish()
        // when hold is set. The DUT lane records it and the model lane
        // replays it; these tests never let the model lane lead.
        protected function void start(int unsigned k, a2c_lane_e l, bit hold = 1);
            bit          rsp;
            int unsigned delay;
            lanes[k].starts[l]++;
            lanes[k].busy[l] = hold;
            if (l == A2C_DUT_LANE) begin
                logs[k].record(1'b0, 0);
            end else if (logs[k].can_replay()) begin
                logs[k].replay(rsp, delay);
            end else begin
                `uvm_error("LB_DRAIN", $sformatf("%s: the model lane led, which this test never does", logs[k].get_full_name()))
            end
        endfunction

        protected function void finish(int unsigned k, a2c_lane_e l);
            lanes[k].busy[l] = 0;
            lanes[k].done[l]++;
        endfunction

        // A transaction on both lanes of log k that starts and completes
        // now, so neither lane is busy at any rising edge, as a hand-written
        // driver of a port with no handshake may report it.
        protected function void blip(int unsigned k);
            start(k, A2C_DUT_LANE, 0);
            start(k, A2C_MODEL_LANE, 0);
            finish(k, A2C_DUT_LANE);
            finish(k, A2C_MODEL_LANE);
        endfunction

        // Runs after reset, before the drop.
        virtual task before_drop();
        endtask

        virtual function void on_ready(uvm_phase phase, int unsigned call);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            before_drop();
            clk_vif.sample_edge();
            drop_time = $realtime;
            phase.drop_objection(this);
        endtask

        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (phase.get_imp() != uvm_run_phase::get()) return;
            ready_time.push_back($realtime);
            on_ready(phase, ready_time.size());
        endfunction

        protected function void check_calls(int unsigned want);
            if (ready_time.size() != want) begin
                `uvm_error("LB_DRAIN", $sformatf("%0d phase_ready_to_end calls, expected %0d", ready_time.size(), want))
            end
        endfunction
    endclass : lb_drain_base

    // Two logs on one clock: fast on clk, with a quiet window of 10 clocks,
    // and late on clk_nba, clk's copy one NBA region later, with a window
    // of 2. At each rising edge fast's watcher updates and wakes the drain
    // before late's watcher has run. late settles first. Its DUT lane starts
    // a transaction at the falling edge before the edge on which fast
    // settles, and its model lane replays it 20 clocks later. When fast
    // settles, late's settled flag is a clock old, so only the drain's
    // re-check of late keeps it until the replay: no A2C_REPLAY.
    class drain_stale_settle_test extends lb_drain_base;
        virtual a2c_clk_if clk_nba_vif;
        int unsigned       fast_quiet = 10;
        // The drain's first clock, late's first start, and the start of its
        // last transaction.
        realtime           first_tick;
        realtime           start_time;
        realtime           last_time;
        int unsigned       want_starts = 1;
        int unsigned       starts_at_end;

        `uvm_component_utils(drain_stale_settle_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk_nba", clk_nba_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk_nba'")
            add_log("fast", clk_vif, fast_quiet, 400);
            add_log("late", clk_nba_vif, 2, 400);
        endfunction

        virtual function void on_ready(uvm_phase phase, int unsigned call);
            if (call == 2) starts_at_end = lanes[1].starts[A2C_DUT_LANE];
            if (call != 1) return;
            fork
                begin
                    @(posedge clk_vif.clk);
                    first_tick = $realtime;
                    repeat (fast_quiet - 2) @(posedge clk_vif.clk);
                    @(negedge clk_nba_vif.clk);
                    start_time = $realtime;
                    late_traffic();
                end
            join_none
        endfunction

        // Runs at the falling edge before fast settles.
        virtual task late_traffic();
            start(1, A2C_DUT_LANE);
            clk_nba_vif.drive_edge();
            finish(1, A2C_DUT_LANE);
            repeat (20) clk_nba_vif.sample_edge();
            last_time = $realtime;
            start(1, A2C_MODEL_LANE);
            clk_nba_vif.drive_edge();
            finish(1, A2C_MODEL_LANE);
        endtask

        virtual function void check_phase(uvm_phase phase);
            realtime settle = first_tick + (fast_quiet - 1) * 10ns;
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("late started at %0t, fast settled at %0t; the drain ended at %0t with %0d of late's %0d transactions started",
                                            start_time, settle, ready_time[ready_time.size() - 1], starts_at_end, want_starts), UVM_NONE)
            check_calls(2);
            if (start_time != settle - 5ns) begin
                `uvm_error("LB_DRAIN", "late's lane did not start at the falling edge before fast settled, so the stale flag went untested")
            end
            if (ready_time[ready_time.size() - 1] <= last_time) begin
                `uvm_error("LB_DRAIN", "the drain ended before late's last transaction started")
            end
            if (starts_at_end != want_starts) begin
                `uvm_error("LB_DRAIN", $sformatf("late had started %0d transactions when the drain ended, expected %0d", starts_at_end, want_starts))
            end
        endfunction
    endclass : drain_stale_settle_test

    // As drain_stale_settle_test, with late's lanes making 20 transactions
    // in step, one at each falling edge from the same one on, each starting
    // and completing there. late is idle() at every rising edge, so only
    // the drain's re-check of late's start counts keeps it after fast
    // settles, and the drain must end only once the 20 are done.
    class drain_stale_settle_stream_test extends drain_stale_settle_test;
        `uvm_component_utils(drain_stale_settle_stream_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_starts = 20;
        endfunction

        virtual task late_traffic();
            for (int unsigned i = 0; i < want_starts; i++) begin
                if (i > 0) clk_nba_vif.sample_edge();
                last_time = $realtime;
                blip(1);
            end
        endtask
    endclass : drain_stale_settle_stream_test

    // One log on clk with a quiet window of 5 clocks, whose lanes make a
    // transaction at each of the 30 falling edges after the drop, each
    // starting and completing there. The log is idle() at every rising
    // edge, so only its starts keep it from settling: the drain must end
    // after the last transaction.
    class drain_stream_test extends lb_drain_base;
        realtime     last_time;
        int unsigned starts_at_end;

        `uvm_component_utils(drain_stream_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            add_log("log", clk_vif, 5, 400);
        endfunction

        virtual function void on_ready(uvm_phase phase, int unsigned call);
            if (call == 2) starts_at_end = lanes[0].starts[A2C_DUT_LANE];
            if (call != 1) return;
            fork
                repeat (30) begin
                    clk_vif.sample_edge();
                    last_time = $realtime;
                    blip(0);
                end
            join_none
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d transactions started when the drain ended %0t after the last", starts_at_end,
                                            ready_time[ready_time.size() - 1] - last_time), UVM_NONE)
            check_calls(2);
            if (starts_at_end != 30) begin
                `uvm_error("LB_DRAIN", $sformatf("the drain ended with %0d of the 30 transactions started", starts_at_end))
            end
        endfunction
    endclass : drain_stream_test

    // Log a on clk, with a quiet window of 30 clocks and a deadline of 50,
    // makes a transaction at every falling edge after the drop, as in
    // drain_stream_test, so the drain cuts it at its deadline, and stops at
    // the cut. Log b on clk, with a quiet window of 10 and a deadline of
    // 1000, holds one transaction its model lane replays 200 clocks after
    // the drop, so b holds the drain about 150 clocks past a's cut. When
    // that drain ends the test resumes the run phase for 5 clocks with one
    // transaction on b. a's DUT lane has not started a transaction for far
    // more than its quiet window, so the second drain must not re-cut it:
    // a ends uncut.
    class drain_cut_count_test extends lb_drain_base;
        int unsigned first_cut;

        `uvm_component_utils(drain_cut_count_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            add_log("a", clk_vif, 30, 50);
            add_log("b", clk_vif, 10, 1000);
        endfunction

        virtual task before_drop();
            clk_vif.sample_edge();
            start(1, A2C_DUT_LANE);
            clk_vif.drive_edge();
            finish(1, A2C_DUT_LANE);
        endtask

        virtual function void on_ready(uvm_phase phase, int unsigned call);
            if (call == 1) begin
                fork
                    forever begin
                        clk_vif.sample_edge();
                        if (logs[0].get_cut() != 0) break;
                        blip(0);
                    end
                    begin
                        repeat (200) clk_vif.sample_edge();
                        start(1, A2C_MODEL_LANE);
                        clk_vif.drive_edge();
                        finish(1, A2C_MODEL_LANE);
                    end
                join_none
            end
            if (call != 2) return;
            first_cut = logs[0].get_cut();
            phase.raise_objection(this, "one more transaction on b");
            fork
                begin
                    clk_vif.sample_edge();
                    blip(1);
                    repeat (5) clk_vif.sample_edge();
                    phase.drop_objection(this, "one more transaction on b");
                end
            join_none
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("a cut after %0d by the first drain, %0d at the end; the drains took %0t and %0t", first_cut,
                                            logs[0].get_cut(), ready_time[1] - ready_time[0], ready_time[ready_time.size() - 1] - ready_time[2]),
                      UVM_NONE)
            check_calls(4);
            if (first_cut == 0) `uvm_error("LB_DRAIN", "the first drain did not cut a")
            if (logs[0].get_cut() != 0) `uvm_error("LB_DRAIN", "the second drain re-cut a, whose DUT lane had long stopped")
        endfunction
    endclass : drain_cut_count_test

    // One log on clk8, gated in bursts with uneven gaps so it never has
    // three agreeing intervals, with a clock stop of 10 clocks, 105ns at
    // its shortest interval and longer than any gap. Its DUT lane starts a
    // transaction before the drop and stays inside it, and the model lane
    // never replays it. clk8 stops four bursts after the drop. The drain
    // must ride through the gaps, give the log up 105ns after clk8's last
    // rising edge with one A2C_DRAIN for the stopped clock, and the log
    // report the response it owes in one A2C_REPLAY.
    class drain_burst_clock_stop_test extends lb_drain_base;
        virtual a2c_clk_if clk8_vif;
        lb_id_counter      drains;
        realtime           waited;

        `uvm_component_utils(drain_burst_clock_stop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_REPLAY";
            want_errors = 1;
            want_text.push_back("uvm_test_top.burst: end of test with 1 responses the DUT lane recorded and the model lane never replayed, from transaction 1");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk8", clk8_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk8'")
            add_log("burst", clk8_vif, 5, 400);
            logs[0].clock_stop_cycles = 10;
            drains = lb_id_counter::type_id::create("drains");
            drains.id = "A2C_DRAIN";
            uvm_report_cb::add(null, drains);
        endfunction

        virtual task before_drop();
            start(0, A2C_DUT_LANE);
        endtask

        virtual function void on_ready(uvm_phase phase, int unsigned call);
            if (call == 2) waited = $realtime - clk8_vif.last_rise;
            if (call != 1) return;
            fork
                begin
                    repeat (12) @(posedge clk8_vif.clk);
                    lb_clk8_run = 0;
                end
                // Fails fast where a clock with no period would hold the
                // drain.
                begin
                    #5us;
                    if (ready_time.size() < 2) `uvm_fatal("LB_DRAIN", "the drain still holds 5us after the drop, so it never saw clk8 stop")
                end
            join_none
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("the drain ended %0t after clk8's last rising edge; %0d A2C_DRAIN: %p", waited, drains.warnings,
                                            drains.messages), UVM_NONE)
            check_calls(2);
            if (drains.warnings != 1 || !a2c_contains(drains.messages[0], "the clock stopped before the log settled")) begin
                `uvm_error("LB_DRAIN", $sformatf("expected one A2C_DRAIN for clk8's stop: %p", drains.messages))
            end
            if (waited < 104ns || waited > 106ns) `uvm_error("LB_DRAIN", $sformatf("the drain ended %0t after clk8 stopped, expected 105ns", waited))
        endfunction
    endclass : drain_burst_clock_stop_test

    // Two logs on clk that reach their deadline with a lane still inside a
    // transaction, which no quiet window fixes. both has both lanes inside
    // one; dut_only has its DUT lane inside one whose response the model
    // lane never replays. Each A2C_DRAIN must name the busy lanes, and
    // neither may blame the quiet window.
    class drain_busy_wording_test extends lb_drain_base;
        lb_id_counter drains;

        `uvm_component_utils(drain_busy_wording_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_REPLAY";
            want_errors = 1;
            want_text.push_back("uvm_test_top.dut_only: end of test with 1 responses the DUT lane recorded and the model lane never replayed, from transaction 1");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            add_log("both", clk_vif, 5, 30);
            add_log("dut_only", clk_vif, 5, 30);
            drains = lb_id_counter::type_id::create("drains");
            drains.id = "A2C_DRAIN";
            uvm_report_cb::add(null, drains);
        endfunction

        virtual task before_drop();
            start(0, A2C_DUT_LANE);
            start(0, A2C_MODEL_LANE);
            start(1, A2C_DUT_LANE);
        endtask

        virtual function void check_phase(uvm_phase phase);
            string want[2] = '{"the DUT lane (1 started, 0 done) and the model lane (1 started, 0 done) are inside a transaction",
                               "1 transactions the DUT lane recorded wait for the model lane, and the DUT lane (1 started, 0 done) is inside a transaction"};
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_DRAIN: %p", drains.warnings, drains.messages), UVM_NONE)
            check_calls(2);
            if (drains.warnings != 2) `uvm_error("LB_DRAIN", $sformatf("expected two A2C_DRAIN, got %0d", drains.warnings))
            foreach (want[i]) begin
                int unsigned n = 0;
                foreach (drains.messages[j]) n += a2c_contains(drains.messages[j], want[i]);
                if (n != 1) `uvm_error("LB_DRAIN", $sformatf("%0d A2C_DRAIN hold '%s', expected one: %p", n, want[i], drains.messages))
            end
            foreach (drains.messages[j]) begin
                if (a2c_contains(drains.messages[j], "drain_quiet_cycles")) begin
                    `uvm_error("LB_DRAIN", $sformatf("an A2C_DRAIN for a busy lane blames the quiet window: %s", drains.messages[j]))
                end
            end
        endfunction
    endclass : drain_busy_wording_test

    // A hand-written responder whose lanes complete two keys in opposite
    // orders across a cut. Log a on clk, with a quiet window of 30 clocks
    // and a deadline of 50, makes a transaction at every clock after the
    // drop until the drain cuts it, and its comparator, keyed by tag, gets
    // one item per lane per transaction: the next of key A, tag 0, on the
    // DUT lane and the next of key B, tag 1, on the model lane. After the
    // cut the DUT lane completes the B items and the model lane the A
    // items. The comparator must pair every A item the cut keeps and hold
    // every B item, leaving none unpaired.
    class drain_keyed_cut_test extends lb_drain_base;
        lb_keyed_cmp cmp;
        int unsigned sent;

        `uvm_component_utils(drain_keyed_cut_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            add_log("a", clk_vif, 30, 50);
            cmp = lb_keyed_cmp::type_id::create("cmp", this);
            logs[0].cmp = cmp;
        endfunction

        protected function rv_item_t item(bit [3:0] tag, int unsigned v);
            lb_data_t d;
            d.tag   = tag;
            d.value = 20'(v);
            return lb_rv_item(d);
        endfunction

        // The items after the cut arrive when the drain ends.
        virtual function void on_ready(uvm_phase phase, int unsigned call);
            if (call == 2) begin
                for (int unsigned i = 1; i <= sent; i++) cmp.write_a2c_dut(item(1, i));
                for (int unsigned i = 1; i <= sent; i++) cmp.write_a2c_model(item(0, i));
            end
            if (call != 1) return;
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (logs[0].get_cut() != 0) break;
                    blip(0);
                    sent++;
                    cmp.write_a2c_dut(item(0, sent));
                    cmp.write_a2c_model(item(1, sent));
                end
            join_none
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned cut = logs[0].get_cut();
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d transactions, a cut after %0d, %0d pairs", sent, cut, cmp.get_pairs()), UVM_NONE)
            check_calls(2);
            if (cut == 0) `uvm_error("LB_DRAIN", "the drain did not cut a")
            if (cmp.get_pairs() != cut) `uvm_error("LB_DRAIN", $sformatf("the comparator paired %0d items, expected the %0d the cut keeps", cmp.get_pairs(), cut))
        endfunction
    endclass : drain_keyed_cut_test

    // Keeps the text and severity of every A2C_CUT report.
    class lb_cut_catcher extends uvm_report_catcher;
        string       messages[$];
        uvm_severity severities[$];

        `uvm_object_utils(lb_cut_catcher)

        function new(string name = "lb_cut_catcher");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_id() == "A2C_CUT") begin
                messages.push_back(get_message());
                severities.push_back(get_severity());
            end
            return THROW;
        endfunction
    endclass : lb_cut_catcher

    // A master elsewhere declares the model lane dead before the drop, and
    // the drain then cuts two logs on clk at their deadline of 50 clocks.
    // a makes a transaction at every clock until its cut and none after,
    // so its cut drops nothing: a UVM_INFO A2C_CUT, which names no death.
    // b's DUT lane starts a transaction at every clock and its model lane
    // replays each five clocks later, so the DUT lane starts more while the
    // model lane catches up: an A2C_CUT warning, which names the death.
    class drain_cut_death_test extends lb_drain_base;
        lb_cut_catcher cuts;
        bit            stop;

        `uvm_component_utils(drain_cut_death_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            add_log("a", clk_vif, 30, 50);
            add_log("b", clk_vif, 30, 50);
            cuts = lb_cut_catcher::type_id::create("cuts");
            uvm_report_cb::add(null, cuts);
        endfunction

        virtual task before_drop();
            clk_vif.sample_edge();
            a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top");
        endtask

        virtual function void on_ready(uvm_phase phase, int unsigned call);
            if (call == 2) stop = 1;
            if (call != 1) return;
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (logs[0].get_cut() != 0) break;
                    blip(0);
                end
                forever begin
                    clk_vif.sample_edge();
                    if (stop) break;
                    start(1, A2C_DUT_LANE, 0);
                    finish(1, A2C_DUT_LANE);
                    if (lanes[1].starts[A2C_DUT_LANE] > 5) begin
                        start(1, A2C_MODEL_LANE, 0);
                        finish(1, A2C_MODEL_LANE);
                    end
                end
            join_none
        endfunction

        virtual function void report_phase(uvm_phase phase);
            string want[2] = '{"uvm_test_top.a: the drain cut the run after pair ", "uvm_test_top.b: the drain cut the run after pair "};
            uvm_severity sev[2] = '{UVM_INFO, UVM_WARNING};
            bit related[2] = '{0, 1};
            `uvm_info("LB_STATS", $sformatf("A2C_CUT: %p", cuts.messages), UVM_NONE)
            check_calls(2);
            foreach (want[k]) begin
                int unsigned n = 0;
                foreach (cuts.messages[i]) begin
                    if (!a2c_contains(cuts.messages[i], want[k])) continue;
                    n++;
                    if (cuts.severities[i] != sev[k]) begin
                        `uvm_error("LB_DRAIN", $sformatf("an A2C_CUT is %s, expected %s: %s", cuts.severities[i].name(), sev[k].name(), cuts.messages[i]))
                    end
                    if (a2c_contains(cuts.messages[i], "; the model lane of uvm_test_top was declared dead at ") != related[k]
                        || a2c_contains(cuts.messages[i], " (A2C_SKEW), which may be related") != related[k]) begin
                        `uvm_error("LB_DRAIN", $sformatf("the A2C_CUT %s the death: %s", related[k] ? "does not name" : "names", cuts.messages[i]))
                    end
                end
                if (n != 1) `uvm_error("LB_DRAIN", $sformatf("%0d A2C_CUT reports begin '%s', expected one: %p", n, want[k], cuts.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : drain_cut_death_test

    // Log a, on clk3 with a quiet window of 30 clocks, a deadline of 50 and
    // a catch-up of 40, starts a transaction on its DUT lane at every clock
    // from the drop to 5 clocks past its cut, and its model lane replays
    // none, so the drain cuts it and its lanes never reach the cut. A master
    // elsewhere declares the model lane dead 10 clocks into the catch-up.
    // The drain gives a up when the catch-up runs out or, with stop_clock,
    // when it finds clk3 stopped, which it does 15 clocks into the
    // catch-up. Log b, on clk, holds the drain past a second death, 300
    // clocks of clk after the drop, with a transaction its model lane
    // replays 400 clocks after the drop. a's A2C_REPLAY error for the cut
    // names the first death, which came before the give-up, and not the
    // second. Its A2C_CUT report, dated by the cut, names neither.
    class drain_catchup_death_test extends lb_drain_base;
        virtual a2c_clk_if clk3_vif;
        bit                stop_clock;
        lb_cut_catcher     cuts;

        `uvm_component_utils(drain_catchup_death_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_REPLAY";
            want_errors = 1;
            want_text.push_back("uvm_test_top.a: the drain cut the run after transaction ");
            want_text.push_back("; the model lane of uvm_test_top was declared dead at ");
            unwant_text.push_back("uvm_test_top.late");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if clk3")
            add_log("a", clk3_vif, 30, 50);
            add_log("b", clk_vif, 10, 1000);
            logs[0].drain_catchup_cycles = 40;
            logs[0].clock_stop_cycles    = 10;
            cuts = lb_cut_catcher::type_id::create("cuts");
            uvm_report_cb::add(null, cuts);
        endfunction

        virtual task before_drop();
            clk_vif.sample_edge();
            start(1, A2C_DUT_LANE);
            clk_vif.drive_edge();
            finish(1, A2C_DUT_LANE);
        endtask

        virtual function void on_ready(uvm_phase phase, int unsigned call);
            if (call != 1) return;
            fork
                begin
                    int unsigned past = 0;
                    while (past < 5) begin
                        clk3_vif.sample_edge();
                        if (logs[0].get_cut() != 0) past++;
                        start(0, A2C_DUT_LANE, 0);
                        finish(0, A2C_DUT_LANE);
                    end
                    repeat (5) clk3_vif.sample_edge();
                    a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top");
                    if (stop_clock) begin
                        repeat (5) clk3_vif.sample_edge();
                        lb_clk3_run = 0;
                    end
                end
                begin
                    repeat (300) clk_vif.sample_edge();
                    a2c_replay_drain::lane_dead(A2C_DUT_LANE, "uvm_test_top.late");
                end
                begin
                    repeat (400) clk_vif.sample_edge();
                    start(1, A2C_MODEL_LANE);
                    clk_vif.drive_edge();
                    finish(1, A2C_MODEL_LANE);
                end
            join_none
        endfunction

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("a cut after %0d; A2C_CUT: %p", logs[0].get_cut(), cuts.messages), UVM_NONE)
            check_calls(2);
            if (logs[0].get_cut() == 0 || logs[0].cut_reached()) begin
                `uvm_error("LB_DRAIN", "the drain did not cut a, or a's lanes reached the cut, so the catch-up's give-up went untested")
            end
            if (cuts.messages.size() != 1 || cuts.severities[0] != UVM_WARNING || a2c_contains(cuts.messages[0], "declared dead")) begin
                `uvm_error("LB_DRAIN", $sformatf("expected one A2C_CUT warning that names no death: %p", cuts.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : drain_catchup_death_test

    // As drain_catchup_death_test with clk3 stopping during the catch-up.
    class drain_catchup_stop_death_test extends drain_catchup_death_test;
        `uvm_component_utils(drain_catchup_stop_death_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            stop_clock = 1;
        endfunction
    endclass : drain_catchup_stop_death_test

    // A master declares the model lane dead, dated 10 clocks back. The
    // clause of an event 5 clocks back leaves the death out in the time
    // step it is declared and names it one clock later.
    class drain_same_step_death_test extends lb_drain_base;
        `uvm_component_utils(drain_same_step_death_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task before_drop();
            realtime period;
            realtime at;
            string   same;
            string   next;
            clk_vif.sample_edge();
            period = $realtime;
            clk_vif.sample_edge();
            period = $realtime - period;
            repeat (10) clk_vif.sample_edge();
            a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top.x", $realtime - 10 * period);
            at   = $realtime - 5 * period;
            same = a2c_replay_drain::death_context(at);
            clk_vif.sample_edge();
            next = a2c_replay_drain::death_context(at);
            if (same != "" || !a2c_contains(next, "the model lane of uvm_test_top.x began to trail at ")) begin
                `uvm_error("LB_DRAIN", $sformatf("the clause of an event before a death is '%s' in the death's time step and '%s' one clock later, expected empty and then naming it",
                                                 same, next))
            end
        endtask
    endclass : drain_same_step_death_test
