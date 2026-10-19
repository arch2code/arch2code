// push_ack agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard, the monitor log and the base test.

    typedef push_ack_agent #(.data_t(lb_data_t)) pa_agent_t;
    typedef pa_agent_t::item_t pa_item_t;
    typedef pa_agent_t::config_t pa_config_t;
    typedef virtual push_ack_if #(.data_t(lb_data_t)) pa_vif_t;

    // Each item carries its sequence number in value, so a lost, repeated or
    // reordered transfer shows as a scoreboard mismatch.
    class pa_seq extends uvm_sequence #(pa_item_t);
        int unsigned              n;
        int unsigned              max_gap;
        lb_scoreboard#(pa_item_t) sb;

        `uvm_object_utils(pa_seq)

        function new(string name = "pa_seq");
            super.new(name);
        endfunction

        virtual task body();
            pa_item_t it;
            for (int unsigned i = 0; i < n; i++) begin
                it = pa_item_t::type_id::create("it");
                start_item(it);
                if (!it.randomize()) `uvm_fatal("LB_RAND", "push_ack item randomize failed")
                it.data.value = 20'(i);
                it.gap        = $urandom_range(max_gap, 0);
                sb.expected.push_back(it);
                finish_item(it);
            end
        endtask
    endclass : pa_seq

    // Builds a push_ack src agent and a dst agent on one interface, with the
    // dst agent's monitor feeding a scoreboard.
    virtual class pa_pair_test extends lb_base_test;
        pa_agent_t                src;
        pa_agent_t                dst;
        lb_scoreboard#(pa_item_t) sb;
        pa_config_t               dst_cfg;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(pa_config_t cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            pa_config_t src_cfg;
            pa_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa", vif)) `uvm_fatal("LB_CFG", "no virtual push_ack_if 'pa'")
            src_cfg = pa_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "pa";
            dst_cfg = pa_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "pa";
            configure_dst(dst_cfg);
            uvm_config_db#(pa_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(pa_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = pa_agent_t::type_id::create("src", this);
            dst = pa_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(pa_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        task send(int unsigned n);
            pa_seq seq = pa_seq::type_id::create("seq");
            seq.n       = n;
            seq.max_gap = 2;
            seq.sb      = sb;
            seq.start(src.sqr);
        endtask
    endclass : pa_pair_test

    // The dst agent acks 0 to 3 extra clocks after it samples push, drawn
    // per transfer. Every transfer must arrive in order, the src and dst
    // monitors must report the same beats at the same times, and the clocks
    // push waited for ack must cover the whole delay range: 1 to 4.
    class push_ack_random_test extends pa_pair_test;
        lb_monitor_log#(pa_item_t) src_log;
        lb_monitor_log#(pa_item_t) dst_log;
        int unsigned               min_wait = '1;
        int unsigned               max_wait;

        `uvm_component_utils(push_ack_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(pa_config_t cfg);
            cfg.ack_delay_min = 0;
            cfg.ack_delay_max = 3;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            src_log = lb_monitor_log#(pa_item_t)::type_id::create("src_log", this);
            dst_log = lb_monitor_log#(pa_item_t)::type_id::create("dst_log", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            src.mon.ap.connect(src_log.analysis_export);
            dst.mon.ap.connect(dst_log.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                watch_waits();
            join_none
            send(n_items);
            wait_matched(sb, n_items, 20 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        protected task watch_waits();
            int unsigned run = 0;
            forever begin
                clk_vif.sample_edge();
                if (dst_cfg.vif.push !== 1'b1) begin
                    run = 0;
                end else if (dst_cfg.vif.ack !== 1'b1) begin
                    run++;
                end else begin
                    if (run < min_wait) min_wait = run;
                    if (run > max_wait) max_wait = run;
                    run = 0;
                end
            end
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d transfers, src and dst monitors %0d and %0d beats, push waited %0d to %0d clocks",
                                            sb.matched, src_log.items.size(), dst_log.items.size(), min_wait, max_wait),
                      UVM_NONE)
            src_log.compare_with(dst_log);
            if (min_wait != 1 || max_wait != 4) begin
                `uvm_error("LB_ACK_DELAY", $sformatf("ack delay 0 to 3 should make push wait 1 to 4 clocks, it waited %0d to %0d",
                                                     min_wait, max_wait))
            end
        endfunction
    endclass : push_ack_random_test

    // The dst agent's monitor feeds an a2c_txn_counter that expects exactly
    // the transfers sent; any shortfall or excess is an A2C_TXN_COUNT error.
    class push_ack_counter_test extends pa_pair_test;
        a2c_txn_counter #(pa_item_t) counter;

        `uvm_component_utils(push_ack_counter_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            counter = a2c_txn_counter#(pa_item_t)::type_id::create("counter", this);
            counter.port_name = "pa";
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            dst.mon.ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            counter.expect_count(n_items);
            send(n_items);
            counter.wait_for_count(clk_vif, 20 * n_items, 50);
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d transfers counted and matched", sb.matched), UVM_NONE)
        endfunction
    endclass : push_ack_counter_test

    // A passive monitor watches pins the test drives by hand: a transfer
    // after one wait, push dropped before ack, data changed before ack and
    // then a transfer, ack with no push, a transfer acked in its first clock
    // and two back to back. Expects exactly two A2C_HOLD and one A2C_PROTO
    // report, demoted to info, and the five transfers reported.
    class push_ack_monitor_checks_test extends lb_base_test;
        pa_agent_t                obs;
        lb_scoreboard#(pa_item_t) sb;
        pa_vif_t                  vif;

        `uvm_component_utils(push_ack_monitor_checks_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            pa_config_t cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa", vif)) `uvm_fatal("LB_CFG", "no virtual push_ack_if 'pa'")
            cfg = pa_config_t::type_id::create("cfg");
            cfg.vif       = vif;
            cfg.clk_vif   = clk_vif;
            cfg.is_active = UVM_PASSIVE;
            cfg.role      = A2C_DST;
            cfg.port_name = "pa";
            uvm_config_db#(pa_config_t)::set(this, "obs", "cfg", cfg);
            obs = pa_agent_t::type_id::create("obs", this);
            sb  = lb_scoreboard#(pa_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            obs.mon.ap.connect(sb.imp);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
        endfunction

        // One clock per call: the pins as the next rising edge sees them.
        task drive(bit push, int unsigned value, bit ack);
            vif.push <= push;
            vif.data <= lb_data_t'(value);
            vif.ack  <= ack;
            clk_vif.drive_edge();
        endtask

        function void expect_transfer(int unsigned value);
            pa_item_t it = pa_item_t::type_id::create("it");
            it.data = lb_data_t'(value);
            sb.expected.push_back(it);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            drive(0, 0, 0);
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            expect_transfer(1);
            expect_transfer(4);
            expect_transfer(5);
            expect_transfer(6);
            expect_transfer(7);
            drive(1, 1, 0);  // transfer after one wait
            drive(1, 1, 1);
            drive(0, 0, 0);
            drive(1, 2, 0);  // push dropped before ack
            drive(0, 2, 0);
            drive(1, 3, 0);  // data changed before ack, then the transfer
            drive(1, 4, 0);
            drive(1, 4, 1);
            drive(0, 0, 0);
            drive(0, 0, 1);  // ack with no push
            drive(0, 0, 0);
            drive(1, 5, 1);  // acked in its first clock
            drive(1, 6, 1);  // back to back
            drive(1, 7, 1);
            drive(0, 0, 0);
            repeat (2) clk_vif.drive_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned hold  = srv.get_id_count("A2C_HOLD");
            int unsigned proto = srv.get_id_count("A2C_PROTO");
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_HOLD, %0d A2C_PROTO, %0d transfers reported", hold, proto, sb.matched),
                      UVM_NONE)
            if (hold != 2) `uvm_error("LB_CHECKS", $sformatf("expected 2 A2C_HOLD reports, got %0d", hold))
            if (proto != 1) `uvm_error("LB_CHECKS", $sformatf("expected 1 A2C_PROTO report, got %0d", proto))
            if (sb.matched != 5) `uvm_error("LB_CHECKS", $sformatf("expected 5 transfers reported, got %0d", sb.matched))
        endfunction
    endclass : push_ack_monitor_checks_test
