// notify_ack agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test. An event has no payload, so the scoreboard
// counts events.

    typedef notify_ack_agent na_agent_t;
    typedef na_agent_t::item_t na_item_t;
    typedef na_agent_t::config_t na_config_t;
    typedef virtual notify_ack_if na_vif_t;

    class na_seq extends uvm_sequence #(na_item_t);
        int unsigned              n;
        int unsigned              max_gap;
        lb_scoreboard#(na_item_t) sb;

        `uvm_object_utils(na_seq)

        function new(string name = "na_seq");
            super.new(name);
        endfunction

        virtual task body();
            na_item_t it;
            repeat (n) begin
                it = na_item_t::type_id::create("it");
                start_item(it);
                it.gap = $urandom_range(max_gap, 0);
                sb.expected.push_back(it);
                finish_item(it);
            end
        endtask
    endclass : na_seq

    // Builds a notify_ack src agent and a dst agent on one interface, with the
    // dst agent's monitor feeding a scoreboard.
    virtual class na_pair_test extends lb_base_test;
        na_agent_t                src;
        na_agent_t                dst;
        lb_scoreboard#(na_item_t) sb;
        na_config_t               dst_cfg;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(na_config_t cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            na_config_t src_cfg;
            na_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(na_vif_t)::get(this, "", "na", vif)) `uvm_fatal("LB_CFG", "no virtual notify_ack_if 'na'")
            src_cfg = na_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "na";
            dst_cfg = na_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "na";
            configure_dst(dst_cfg);
            uvm_config_db#(na_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(na_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = na_agent_t::type_id::create("src", this);
            dst = na_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(na_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        task send(int unsigned n);
            na_seq seq = na_seq::type_id::create("seq");
            seq.n       = n;
            seq.max_gap = 2;
            seq.sb      = sb;
            seq.start(src.sqr);
        endtask
    endclass : na_pair_test

    // The dst agent acks 0 to 3 extra clocks after it samples notify, drawn
    // per event. Every event must arrive, and the clocks notify waited for
    // ack must cover the whole delay range: 1 to 4.
    class notify_ack_random_test extends na_pair_test;
        int unsigned min_wait = '1;
        int unsigned max_wait;

        `uvm_component_utils(notify_ack_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(na_config_t cfg);
            cfg.ack_delay_min = 0;
            cfg.ack_delay_max = 3;
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
                if (dst_cfg.vif.notify !== 1'b1) begin
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
            `uvm_info("LB_STATS", $sformatf("%0d events, notify waited %0d to %0d clocks", sb.matched, min_wait, max_wait),
                      UVM_NONE)
            if (min_wait != 1 || max_wait != 4) begin
                `uvm_error("LB_ACK_DELAY", $sformatf("ack delay 0 to 3 should make notify wait 1 to 4 clocks, it waited %0d to %0d",
                                                     min_wait, max_wait))
            end
        endfunction
    endclass : notify_ack_random_test

    // The dst agent's monitor feeds an a2c_txn_counter that expects exactly
    // the events sent; any shortfall or excess is an A2C_TXN_COUNT error.
    class notify_ack_counter_test extends na_pair_test;
        a2c_txn_counter #(na_item_t) counter;

        `uvm_component_utils(notify_ack_counter_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            counter = a2c_txn_counter#(na_item_t)::type_id::create("counter", this);
            counter.port_name = "na";
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
            `uvm_info("LB_STATS", $sformatf("%0d events counted and matched", sb.matched), UVM_NONE)
        endfunction
    endclass : notify_ack_counter_test

    // A passive monitor watches pins the test drives by hand: an event after
    // one wait, notify dropped before ack, ack with no notify, an event acked
    // in its first clock and two back to back. Expects exactly one A2C_HOLD
    // and one A2C_PROTO report, demoted to info, and the four events
    // reported.
    class notify_ack_monitor_checks_test extends lb_base_test;
        na_agent_t                obs;
        lb_scoreboard#(na_item_t) sb;
        na_vif_t                  vif;

        `uvm_component_utils(notify_ack_monitor_checks_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            na_config_t cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(na_vif_t)::get(this, "", "na", vif)) `uvm_fatal("LB_CFG", "no virtual notify_ack_if 'na'")
            cfg = na_config_t::type_id::create("cfg");
            cfg.vif       = vif;
            cfg.clk_vif   = clk_vif;
            cfg.is_active = UVM_PASSIVE;
            cfg.role      = A2C_DST;
            cfg.port_name = "na";
            uvm_config_db#(na_config_t)::set(this, "obs", "cfg", cfg);
            obs = na_agent_t::type_id::create("obs", this);
            sb  = lb_scoreboard#(na_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            obs.mon.ap.connect(sb.imp);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
        endfunction

        // One clock per call: the pins as the next rising edge sees them.
        task drive(bit notify, bit ack);
            vif.notify <= notify;
            vif.ack    <= ack;
            clk_vif.drive_edge();
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            drive(0, 0);
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            repeat (4) sb.expected.push_back(na_item_t::type_id::create("it"));
            drive(1, 0);  // event after one wait
            drive(1, 1);
            drive(0, 0);
            drive(1, 0);  // notify dropped before ack
            drive(0, 0);
            drive(0, 1);  // ack with no notify
            drive(0, 0);
            drive(1, 1);  // acked in its first clock
            drive(1, 1);  // back to back
            drive(1, 1);
            drive(0, 0);
            repeat (2) clk_vif.drive_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned hold  = srv.get_id_count("A2C_HOLD");
            int unsigned proto = srv.get_id_count("A2C_PROTO");
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_HOLD, %0d A2C_PROTO, %0d events reported", hold, proto, sb.matched),
                      UVM_NONE)
            if (hold != 1) `uvm_error("LB_CHECKS", $sformatf("expected 1 A2C_HOLD report, got %0d", hold))
            if (proto != 1) `uvm_error("LB_CHECKS", $sformatf("expected 1 A2C_PROTO report, got %0d", proto))
            if (sb.matched != 4) `uvm_error("LB_CHECKS", $sformatf("expected 4 events reported, got %0d", sb.matched))
        endfunction
    endclass : notify_ack_monitor_checks_test

    // Mode B on na and na_model; lb_hs_mode_b has the checks. As A2C_SRC
    // the DUT lane's peer acks after 0 to 1 extra clocks and the model
    // lane's after 0 to 3; as A2C_DST the agent acks after 0 to 2. An event
    // has no payload, so model_cmp checks only the count.
    class na_mode_b extends lb_hs_mode_b #(na_agent_t, na_item_t, na_config_t, na_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "na";
        endfunction

        virtual function na_item_t new_item(int unsigned i);
            return na_item_t::type_id::create("it");
        endfunction

        virtual function void configure();
            peer_cfg.ack_delay_max       = 1;
            model_peer_cfg.ack_delay_max = 3;
            agent_cfg.ack_delay_max      = 2;
        endfunction
    endclass : na_mode_b

    // The agent notifies each item on both lanes.
    class notify_ack_mode_b_test extends na_mode_b;
        `uvm_component_utils(notify_ack_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_SRC;
            variant = LB_MATCH;
        endfunction
    endclass : notify_ack_mode_b_test

    // The agent acks both lanes, replaying the DUT lane's delays.
    class notify_ack_mode_b_dst_test extends na_mode_b;
        `uvm_component_utils(notify_ack_mode_b_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_MATCH;
        endfunction
    endclass : notify_ack_mode_b_dst_test

    // The model lane reaches every event first and waits for the DUT lane.
    class notify_ack_mode_b_dst_model_leads_test extends na_mode_b;
        `uvm_component_utils(notify_ack_mode_b_dst_model_leads_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_MODEL_LEADS;
        endfunction
    endclass : notify_ack_mode_b_dst_model_leads_test

    // The DUT lane makes one event more: the drain runs to its deadline and
    // the replay log reports the record the model lane never replayed.
    class notify_ack_mode_b_dst_dut_extra_test extends na_mode_b;
        `uvm_component_utils(notify_ack_mode_b_dst_dut_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_DUT_EXTRA;
        endfunction
    endclass : notify_ack_mode_b_dst_dut_extra_test

    // The model lane makes one event more, which it waits for until the
    // drain's deadline: one A2C_REPLAY.
    class notify_ack_mode_b_dst_model_extra_test extends na_mode_b;
        `uvm_component_utils(notify_ack_mode_b_dst_model_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_MODEL_EXTRA;
        endfunction
    endclass : notify_ack_mode_b_dst_model_extra_test

    // The test drops its objection when the DUT lane is done, before the model
    // lane starts its last event: the drain must hold the run phase until
    // the model lane has replayed it.
    class notify_ack_mode_b_dst_drain_test extends na_mode_b;
        `uvm_component_utils(notify_ack_mode_b_dst_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_DRAIN;
        endfunction
    endclass : notify_ack_mode_b_dst_drain_test

    // As notify_ack_mode_b_dst_drain_test with a quiet window of one clock
    // and every ack 3 clocks late, and the drop once the DUT lane is idle.
    // Once the model lane has replayed its last event, only its wait for
    // that ack keeps the window from closing before the event completes.
    class notify_ack_mode_b_dst_drain_short_quiet_test extends notify_ack_mode_b_dst_drain_test;
        `uvm_component_utils(notify_ack_mode_b_dst_drain_short_quiet_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            drain_quiet = 1;
        endfunction

        virtual function void configure();
            super.configure();
            agent_cfg.ack_delay_min = 3;
            agent_cfg.ack_delay_max = 3;
        endfunction

        virtual task wait_drop();
            super.wait_drop();
            repeat (2) clk_vif.sample_edge();
        endtask
    endclass : notify_ack_mode_b_dst_drain_short_quiet_test

    // Both peers keep sending after the test drops its objection, so the
    // drain's quiet window never comes: it must cut the run at its deadline
    // and end once both lanes have completed what the cut keeps, with no
    // A2C_REPLAY.
    class notify_ack_mode_b_dst_drain_busy_test extends na_mode_b;
        `uvm_component_utils(notify_ack_mode_b_dst_drain_busy_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_BUSY;
        endfunction
    endclass : notify_ack_mode_b_dst_drain_busy_test

    // The first drain expires with the model lane's late event pending,
    // and the test sends the last event after it: the model lane's start
    // since the expiry must bring a second drain that replays it. One more
    // event, sent after the second drain and late on the model lane, must
    // bring a third.
    class notify_ack_mode_b_dst_after_expiry_test extends na_mode_b;
        `uvm_component_utils(notify_ack_mode_b_dst_after_expiry_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_AFTER_EXPIRY;
        endfunction
    endclass : notify_ack_mode_b_dst_after_expiry_test
