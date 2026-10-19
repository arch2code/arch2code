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
        a2c_error_demoter              demoter;
        int                            expect_delta = 0;
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
            demoter = a2c_error_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
            dst.mon.ap.connect(counter.analysis_export);
        endfunction

        task send_and_wait(int unsigned n_send, int unsigned expected);
            rv_seq seq = rv_seq::type_id::create("seq");
            seq.n       = n_send;
            seq.max_gap = 2;
            seq.sb      = sb;
            if (expected > 0) counter.expect_count(expected);
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
