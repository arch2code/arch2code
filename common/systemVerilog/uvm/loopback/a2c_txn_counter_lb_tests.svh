// Loopback tests of a2c_txn_counter and a2c_error_demoter, on a rdy_vld
// link. Included in a2c_uvm_loopback_pkg after rdy_vld_lb_tests.svh.

    // A rdy_vld src agent drives a dst agent whose monitor feeds an
    // a2c_txn_counter. The test sends n_items - late transactions and waits
    // for n_items + expect_delta, unless skip_wait is set. With second_wait
    // set it then sends n_items more and waits for them with the count
    // right. With late set it sends the late transactions after the first
    // wait and waits again with no expect_count(). An a2c_error_demoter
    // catches every A2C_TXN_COUNT, and the test checks how many the counter
    // raised by the end of the first wait, by the end of the last wait and by
    // the end of check_phase. With the expected count right, none is raised.
    class txn_count_clean_test extends lb_base_test;
        rv_agent_t                     src;
        rv_agent_t                     dst;
        lb_scoreboard#(rv_item_t)      sb;
        a2c_txn_counter #(rv_item_t)   counter;
        lb_recording_demoter           demoter;
        uvm_analysis_port #(rv_item_t) model_ap;
        int                            expect_delta = 0;
        // With dual set, the counter also counts a model lane that this test
        // feeds n_items - late + model_delta synthetic items, more slowly
        // than the DUT lane delivers its own.
        bit                            dual = 0;
        int                            model_delta = 0;
        bit                            skip_wait = 0;
        bit                            second_wait = 0;
        int unsigned                   late = 0;
        int unsigned                   want[3] = '{0, 0, 0};
        int unsigned                   got[3];

        `uvm_component_utils(txn_count_clean_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t src_cfg;
            rv_config_t dst_cfg;
            rv_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            src_cfg = rv_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "rv";
            dst_cfg = rv_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "rv";
            dst_cfg.ready_pct = 50;
            uvm_config_db#(rv_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(rv_config_t)::set(this, "dst", "cfg", dst_cfg);
            src   = rv_agent_t::type_id::create("src", this);
            dst   = rv_agent_t::type_id::create("dst", this);
            sb    = lb_scoreboard#(rv_item_t)::type_id::create("sb", this);
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv";
            counter.dual      = dual;
            if (dual) model_ap = new("model_ap", this);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
            dst.mon.ap.connect(counter.analysis_export);
            if (dual) model_ap.connect(counter.model_export);
        endfunction

        task feed_model(int unsigned n);
            repeat (n) begin
                rv_item_t it = rv_item_t::type_id::create("it");
                repeat ($urandom_range(8, 0)) clk_vif.sample_edge();
                model_ap.write(it);
            end
        endtask

        task send_and_wait(int unsigned n_send, int unsigned expected);
            rv_seq seq = rv_seq::type_id::create("seq");
            seq.n       = n_send;
            seq.max_gap = 2;
            seq.sb      = sb;
            if (expected > 0) counter.expect_count(expected);
            if (dual) begin
                fork
                    feed_model(int'(n_send) + model_delta);
                join_none
            end
            seq.start(src.sqr);
            if (!skip_wait) counter.wait_for_count(clk_vif, 20 * n_items, 50);
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            send_and_wait(n_items - late, n_items + expect_delta);
            got[0] = demoter.demoted;
            if (second_wait) send_and_wait(n_items, n_items);
            if (late) send_and_wait(late, 0);
            got[1] = demoter.demoted;
            // Lets a transaction still in flight arrive before check_phase.
            repeat (50) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        // report_phase follows check_phase, so the counter's
        // check_phase reports are counted by now.
        virtual function void report_phase(uvm_phase phase);
            got[2] = demoter.demoted;
            `uvm_info("LB_STATS", $sformatf("%0d transactions, first wait expected %0d; A2C_TXN_COUNT by the first wait %0d, by the last %0d, by check_phase %0d",
                                            sb.matched, int'(n_items) + expect_delta, got[0], got[1], got[2]), UVM_NONE)
            if (got != want) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected %0d, %0d and %0d A2C_TXN_COUNT by the first wait, the last wait and check_phase",
                                                 want[0], want[1], want[2]))
            end
            super.report_phase(phase);
        endfunction
    endclass : txn_count_clean_test

    // Two transactions more expected than sent: the wait reports them at its
    // deadline, and check_phase does not report them again.
    class txn_count_missing_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_missing_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = 2;
            want         = '{1, 1, 1};
        endfunction
    endclass : txn_count_missing_test

    // One transaction fewer expected than sent: the wait reports the extra
    // transaction at the end of its quiet window, and check_phase does not
    // report it again.
    class txn_count_extra_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = -1;
            want         = '{1, 1, 1};
        endfunction
    endclass : txn_count_extra_test

    // One transaction fewer expected than sent and no wait: check_phase
    // reports the extra transaction.
    class txn_count_unwaited_extra_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_unwaited_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = -1;
            skip_wait    = 1;
            want         = '{0, 0, 1};
        endfunction
    endclass : txn_count_unwaited_extra_test

    // A failing wait, one transaction extra, then a passing one on the same
    // counter: only the first reports.
    class txn_count_twice_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_twice_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = -1;
            second_wait  = 1;
            want         = '{1, 1, 1};
        endfunction
    endclass : txn_count_twice_test

    // One transaction short in the first of two waited batches, as when the
    // DUT drops one in frame 1: the first wait reports it, and the second
    // batch's expect_count() writes it off, so the second batch counts whole.
    class txn_count_dropped_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_dropped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = 1;
            second_wait  = 1;
            want         = '{1, 1, 1};
        endfunction
    endclass : txn_count_dropped_test

    // The last transaction arrives after the first wait's deadline: the
    // wait reports it missing, and when it arrives it is late, not extra, so
    // neither the second wait nor check_phase reports it again.
    class txn_count_late_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            late = 1;
            want = '{1, 1, 1};
        endfunction
    endclass : txn_count_late_test

    // The exact text of a Mode A shortfall: no lane is named.
    class txn_count_mode_a_text_test extends txn_count_missing_test;
        `uvm_component_utils(txn_count_mode_a_text_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            string want_text = $sformatf("rv: deadline of %0d clocks passed: expected %0d transactions, received %0d (2 missing)",
                                         20 * n_items, n_items + 2, n_items);
            if (demoter.messages.size() != 1 || demoter.messages[0] != want_text) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected the one message '%s', got %p", want_text, demoter.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : txn_count_mode_a_text_test

    // Both lanes reach the count. The model lane finishes after the DUT
    // lane, so a wait that ran the quiet window on the DUT lane alone would
    // report the model lane short.
    class txn_count_dual_clean_test extends txn_count_clean_test;
        string want_lane = "";

        `uvm_component_utils(txn_count_dual_clean_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dual = 1;
        endfunction

        // Every report names want_lane and none names the other lane.
        virtual function void report_phase(uvm_phase phase);
            string       other = "DUT lane";
            int unsigned named = demoter.count({"rv ", want_lane, ": "});
            if (want_lane == "DUT lane") other = "model lane";
            if (want_lane != "" && (named != demoter.messages.size() || demoter.count(other) != 0)) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected every A2C_TXN_COUNT to name the %s, got %p", want_lane, demoter.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : txn_count_dual_clean_test

    // The model lane delivers two fewer than expected: one shortfall, on the
    // model lane.
    class txn_count_dual_model_short_test extends txn_count_dual_clean_test;
        `uvm_component_utils(txn_count_dual_model_short_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            model_delta = -2;
            want_lane   = "model lane";
            want        = '{1, 1, 1};
        endfunction
    endclass : txn_count_dual_model_short_test

    // The DUT lane delivers two fewer than expected: one shortfall, on the
    // DUT lane.
    class txn_count_dual_dut_short_test extends txn_count_dual_clean_test;
        `uvm_component_utils(txn_count_dual_dut_short_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = 2;
            model_delta  = 2;
            want_lane    = "DUT lane";
            want         = '{1, 1, 1};
        endfunction
    endclass : txn_count_dual_dut_short_test

    // The model lane delivers one more than expected: one excess at the end
    // of the quiet window, on the model lane.
    class txn_count_dual_model_extra_test extends txn_count_dual_clean_test;
        `uvm_component_utils(txn_count_dual_model_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            model_delta = 1;
            want_lane   = "model lane";
            want        = '{1, 1, 1};
        endfunction
    endclass : txn_count_dual_model_extra_test

    // Both lanes two short: the wait reports each lane once, and
    // check_phase adds nothing.
    class txn_count_dual_both_short_test extends txn_count_dual_clean_test;
        `uvm_component_utils(txn_count_dual_both_short_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = 2;
            want         = '{2, 2, 2};
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (demoter.count("rv DUT lane: deadline") != 1 || demoter.count("rv model lane: deadline") != 1) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected one shortfall per lane, got %p", demoter.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : txn_count_dual_both_short_test

    // A transaction on model_export with dual clear is one A2C_CFG error.
    class txn_count_model_without_dual_test extends lb_base_test;
        a2c_txn_counter #(rv_item_t)   counter;
        uvm_analysis_port #(rv_item_t) model_ap;
        lb_recording_demoter           demoter;

        `uvm_component_utils(txn_count_model_without_dual_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv";
            model_ap = new("model_ap", this);
            demoter  = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_CFG";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            model_ap.connect(counter.model_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            model_ap.write(rv_item_t::type_id::create("it"));
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            string want_text = "rv: model_export received a transaction, but dual is not set";
            if (demoter.messages.size() != 1 || demoter.messages[0] != want_text) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected the one A2C_CFG '%s', got %p", want_text, demoter.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : txn_count_model_without_dual_test

    // A counter on clk3 with a clock stop of 10 clocks expects three
    // transactions and gets two, and clk3 stops five clocks into
    // wait_for_count(). The wait must return ten and a half periods after
    // clk3's last falling edge, far short of its deadline, with one
    // A2C_TXN_COUNT naming the stop, and check_phase must not report the
    // shortfall again.
    class txn_count_clock_stop_test extends lb_base_test;
        a2c_txn_counter #(rv_item_t)   counter;
        uvm_analysis_port #(rv_item_t) ap;
        lb_recording_demoter           demoter;
        virtual a2c_clk_if             clk3_vif;
        realtime                       stop_time;
        realtime                       end_time;

        `uvm_component_utils(txn_count_clock_stop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name         = "rv";
            counter.clock_stop_cycles = 10;
            ap = new("ap", this);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk3_vif.wait_reset_release();
            counter.expect_count(3);
            repeat (2) ap.write(rv_item_t::type_id::create("it"));
            fork
                begin
                    repeat (5) clk3_vif.sample_edge();
                    lb_clk3_run = 0;
                    stop_time   = $realtime;
                end
            join_none
            counter.wait_for_count(clk3_vif, 1000, 10);
            end_time = $realtime;
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            realtime waited = end_time - stop_time;
            `uvm_info("LB_STATS", $sformatf("the wait returned %0t after clk3 stopped; %0d A2C_TXN_COUNT", waited, demoter.demoted), UVM_NONE)
            if (demoter.demoted != 1 || demoter.count("rv: the clock stopped after 5 clocks: expected 3 transactions, received 2 (1 missing)") != 1) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected one A2C_TXN_COUNT for the stopped clock: %p", demoter.messages))
            end
            // clk3 stopped at a falling edge, and its period is 20ns.
            if (waited < 209ns || waited > 211ns) `uvm_error("LB_TXN_COUNT", $sformatf("the wait returned %0t after clk3 stopped, expected 210ns", waited))
            super.report_phase(phase);
        endfunction
    endclass : txn_count_clock_stop_test

    // A counter on clk4, which has no reset, waits from clk4's first rising
    // edge, before clk4 has a period. It expects two transactions, has one,
    // and gets the other ten of clk's clocks into the wait, short of one
    // clk4 period: no A2C_TXN_COUNT, as clk4 has not stopped.
    class txn_count_slow_clock_test extends lb_base_test;
        a2c_txn_counter #(rv_item_t)   counter;
        uvm_analysis_port #(rv_item_t) ap;
        lb_recording_demoter           demoter;
        virtual a2c_clk_if             clk4_vif;
        int unsigned                   expected = 2;
        string                         want_text = "";
        // Waits from time 0, before clk4 has risen, instead.
        bit                            unstarted;

        `uvm_component_utils(txn_count_slow_clock_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk4", clk4_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk4'")
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv";
            ap = new("ap", this);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            if (!unstarted) clk4_vif.wait_reset_release();
            counter.expect_count(expected);
            ap.write(rv_item_t::type_id::create("it"));
            fork
                begin
                    repeat (10) clk_vif.sample_edge();
                    ap.write(rv_item_t::type_id::create("it"));
                end
            join_none
            counter.wait_for_count(clk4_vif, 1000, 2);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_TXN_COUNT: %p", demoter.demoted, demoter.messages), UVM_NONE)
            if (want_text == "" && demoter.demoted != 0) `uvm_error("LB_TXN_COUNT", $sformatf("expected no A2C_TXN_COUNT: %p", demoter.messages))
            if (want_text != "" && (demoter.demoted != 1 || demoter.count(want_text) != 1)) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected the one A2C_TXN_COUNT '%s': %p", want_text, demoter.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : txn_count_slow_clock_test

    // As txn_count_slow_clock_test expecting one transaction: the second is
    // extra, and the quiet window, which waits for clk4's edges, must report
    // it.
    class txn_count_slow_clock_extra_test extends txn_count_slow_clock_test;
        `uvm_component_utils(txn_count_slow_clock_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expected  = 1;
            want_text = "rv: by the end of the quiet window received 2 transactions, expected 1 (1 extra)";
        endfunction
    endclass : txn_count_slow_clock_extra_test

    // As txn_count_slow_clock_test from time 0, before clk4 first rises at
    // 250ns: a clock that has not started yet has not stopped, so no
    // A2C_TXN_COUNT.
    class txn_count_unstarted_clock_test extends txn_count_slow_clock_test;
        `uvm_component_utils(txn_count_unstarted_clock_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            unstarted = 1;
        endfunction
    endclass : txn_count_unstarted_clock_test

    // A counter on clk3 with a clock stop of 10 clocks, set through the
    // config_db, expects three transactions and gets two. clk3 stops low
    // for 1us, runs one more cycle and stops low again, and the wait starts
    // then. The rising edge after the long gap must not make the gap clk3's
    // period, so the wait must return ten and a half periods of 20ns after
    // clk3's last falling edge with one A2C_TXN_COUNT, not ten and a half
    // gaps.
    class txn_count_clock_restop_test extends lb_base_test;
        a2c_txn_counter #(rv_item_t)   counter;
        uvm_analysis_port #(rv_item_t) ap;
        lb_recording_demoter           demoter;
        virtual a2c_clk_if             clk3_vif;
        realtime                       stop_time;
        realtime                       end_time;

        `uvm_component_utils(txn_count_clock_restop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            uvm_config_db#(int unsigned)::set(this, "counter", "a2c_clock_stop_cycles", 10);
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv";
            ap = new("ap", this);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk3_vif.wait_reset_release();
            counter.expect_count(3);
            repeat (2) ap.write(rv_item_t::type_id::create("it"));
            clk3_vif.sample_edge();
            lb_clk3_run = 0;
            #1us;
            lb_clk3_run = 1;
            clk3_vif.sample_edge();
            lb_clk3_run = 0;
            stop_time = $realtime;
            counter.wait_for_count(clk3_vif, 1000, 10);
            end_time = $realtime;
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            realtime waited = end_time - stop_time;
            `uvm_info("LB_STATS", $sformatf("the wait returned %0t after clk3 stopped again; %0d A2C_TXN_COUNT", waited, demoter.demoted), UVM_NONE)
            if (demoter.demoted != 1 || demoter.count("rv: the clock stopped after 0 clocks: expected 3 transactions, received 2 (1 missing)") != 1) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected one A2C_TXN_COUNT for the stopped clock: %p", demoter.messages))
            end
            if (waited < 209ns || waited > 211ns) `uvm_error("LB_TXN_COUNT", $sformatf("the wait returned %0t after clk3 stopped again, expected 210ns", waited))
            super.report_phase(phase);
        endfunction
    endclass : txn_count_clock_restop_test

    // A counter on clk3 with a quiet window of 0 clocks and the default
    // clock stop expects three transactions and has two. clk3 pauses for
    // five periods, and the third arrives two clocks after it runs again.
    // A pause far short of the clock stop is no stop: no A2C_TXN_COUNT.
    class txn_count_clock_pause_test extends lb_base_test;
        a2c_txn_counter #(rv_item_t)   counter;
        uvm_analysis_port #(rv_item_t) ap;
        lb_recording_demoter           demoter;
        virtual a2c_clk_if             clk3_vif;

        `uvm_component_utils(txn_count_clock_pause_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv";
            ap = new("ap", this);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk3_vif.wait_reset_release();
            counter.expect_count(3);
            repeat (2) ap.write(rv_item_t::type_id::create("it"));
            fork
                begin
                    clk3_vif.sample_edge();
                    lb_clk3_run = 0;
                    #100ns;
                    lb_clk3_run = 1;
                    repeat (2) clk3_vif.sample_edge();
                    ap.write(rv_item_t::type_id::create("it"));
                end
            join_none
            counter.wait_for_count(clk3_vif, 1000, 0);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_TXN_COUNT: %p", demoter.demoted, demoter.messages), UVM_NONE)
            if (demoter.demoted != 0) `uvm_error("LB_TXN_COUNT", $sformatf("expected no A2C_TXN_COUNT: %p", demoter.messages))
            super.report_phase(phase);
        endfunction
    endclass : txn_count_clock_pause_test

    // A counter on clk6 with a clock stop of 10 clocks. clk6 slows from a
    // 10ns period to 1us, a hundred times longer, and after five rising
    // edges at the new rate the counter expects three transactions, has
    // two, and gets the third three clocks into its wait. The wait must
    // judge the slow clock by its new period: no A2C_TXN_COUNT. A period
    // that only shrinks would stay at 10ns and read clk6 as stopped.
    class txn_count_clock_drop_test extends lb_base_test;
        a2c_txn_counter #(rv_item_t)   counter;
        uvm_analysis_port #(rv_item_t) ap;
        lb_recording_demoter           demoter;
        virtual a2c_clk_if             clk6_vif;

        `uvm_component_utils(txn_count_clock_drop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk6", clk6_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk6'")
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name         = "rv";
            counter.clock_stop_cycles = 10;
            ap = new("ap", this);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk6_vif.wait_reset_release();
            repeat (5) clk6_vif.sample_edge();
            lb_clk6_half_ns = 500;
            repeat (5) @(posedge clk6_vif.clk);
            counter.expect_count(3);
            repeat (2) ap.write(rv_item_t::type_id::create("it"));
            fork
                begin
                    repeat (3) clk6_vif.sample_edge();
                    ap.write(rv_item_t::type_id::create("it"));
                end
            join_none
            counter.wait_for_count(clk6_vif, 1000, 2);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("clk6's period %0.3f ns; %0d A2C_TXN_COUNT: %p", clk6_vif.period, demoter.demoted, demoter.messages),
                      UVM_NONE)
            if (demoter.demoted != 0) `uvm_error("LB_TXN_COUNT", $sformatf("expected no A2C_TXN_COUNT: %p", demoter.messages))
            super.report_phase(phase);
        endfunction
    endclass : txn_count_clock_drop_test

    // A counter on clk7, of a 20ns period, with a clock stop of one clock
    // and a quiet window of 0. It expects three transactions and has two.
    // clk7 gets a runt pulse 0.5ns after a falling edge, so its rising
    // edges come 10.5ns and 9.5ns apart once, and the third transaction
    // arrives four clocks later. The two short intervals must not become
    // the period, which would make the stop limit 1.5 of them, under 20ns:
    // no A2C_TXN_COUNT.
    class txn_count_clock_runt_test extends lb_base_test;
        a2c_txn_counter #(rv_item_t)   counter;
        uvm_analysis_port #(rv_item_t) ap;
        lb_recording_demoter           demoter;
        virtual a2c_clk_if             clk7_vif;

        `uvm_component_utils(txn_count_clock_runt_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk7", clk7_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk7'")
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name         = "rv";
            counter.clock_stop_cycles = 1;
            ap = new("ap", this);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk7_vif.wait_reset_release();
            repeat (5) clk7_vif.sample_edge();
            counter.expect_count(3);
            repeat (2) ap.write(rv_item_t::type_id::create("it"));
            fork
                begin
                    clk7_vif.sample_edge();
                    lb_clk7_runt = 1;
                    repeat (5) clk7_vif.sample_edge();
                    ap.write(rv_item_t::type_id::create("it"));
                end
            join_none
            counter.wait_for_count(clk7_vif, 1000, 0);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("clk7's period %0.3f ns; %0d A2C_TXN_COUNT: %p", clk7_vif.period, demoter.demoted, demoter.messages),
                      UVM_NONE)
            if (demoter.demoted != 0) `uvm_error("LB_TXN_COUNT", $sformatf("expected no A2C_TXN_COUNT: %p", demoter.messages))
            super.report_phase(phase);
        endfunction
    endclass : txn_count_clock_runt_test

    // A counter on clk8, gated in bursts of three edges 10ns apart with
    // uneven gaps, so it never has three agreeing intervals and only the
    // shortest interval gives it a period. The clock stop is 10 clocks,
    // 105ns, longer than any gap. The counter expects three transactions
    // and has two, and clk8 stops four bursts into the wait. The wait must
    // ride through the gaps and return 105ns after clk8's last falling
    // edge with one A2C_TXN_COUNT naming the stop.
    class txn_count_burst_clock_stop_test extends lb_base_test;
        a2c_txn_counter #(rv_item_t)   counter;
        uvm_analysis_port #(rv_item_t) ap;
        lb_recording_demoter           demoter;
        virtual a2c_clk_if             clk8_vif;
        realtime                       waited;

        `uvm_component_utils(txn_count_burst_clock_stop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk8", clk8_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk8'")
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name         = "rv";
            counter.clock_stop_cycles = 10;
            ap = new("ap", this);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk8_vif.wait_reset_release();
            counter.expect_count(3);
            repeat (2) ap.write(rv_item_t::type_id::create("it"));
            fork
                begin
                    repeat (12) clk8_vif.sample_edge();
                    lb_clk8_run = 0;
                end
            join_none
            // Fails fast where a clock with no period would hang the wait.
            fork
                begin
                    fork
                        counter.wait_for_count(clk8_vif, 1000, 10);
                        begin
                            #5us;
                            `uvm_fatal("LB_TXN_COUNT", "the wait has not returned 5us after it started, so it never saw clk8 stop")
                        end
                    join_any
                    disable fork;
                end
            join
            waited = $realtime - clk8_vif.last_fall;
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("the wait returned %0t after clk8's last falling edge, period %0.3f ns; %0d A2C_TXN_COUNT: %p",
                                            waited, clk8_vif.period, demoter.demoted, demoter.messages), UVM_NONE)
            if (demoter.demoted != 1 || demoter.count("rv: the clock stopped after 12 clocks: expected 3 transactions, received 2 (1 missing)") != 1) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected one A2C_TXN_COUNT for the stopped clock: %p", demoter.messages))
            end
            if (waited < 104ns || waited > 106ns) `uvm_error("LB_TXN_COUNT", $sformatf("the wait returned %0t after clk8 stopped, expected 105ns", waited))
            super.report_phase(phase);
        endfunction
    endclass : txn_count_burst_clock_stop_test
