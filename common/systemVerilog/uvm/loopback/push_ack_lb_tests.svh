// push_ack agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

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
    // per transfer. Every transfer must arrive in order, and the clocks push
    // waited for ack must cover the whole delay range: 1 to 4.
    class push_ack_random_test extends pa_pair_test;
        int unsigned min_wait = '1;
        int unsigned max_wait;

        `uvm_component_utils(push_ack_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(pa_config_t cfg);
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
            `uvm_info("LB_STATS", $sformatf("%0d transfers, push waited %0d to %0d clocks", sb.matched, min_wait, max_wait),
                      UVM_NONE)
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

    // Mode B on pa and pa_model; lb_hs_mode_b has the checks. As A2C_SRC
    // the DUT lane's peer acks after 0 to 1 extra clocks and the model
    // lane's after 0 to 3; as A2C_DST the agent acks after 0 to 2.
    class pa_mode_b extends lb_hs_mode_b #(pa_agent_t, pa_item_t, pa_config_t, pa_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "pa";
        endfunction

        virtual function pa_item_t new_item(int unsigned i);
            pa_item_t it = pa_item_t::type_id::create("it");
            if (!it.randomize()) `uvm_fatal("LB_RAND", "push_ack item randomize failed")
            it.data.value = 20'(i);
            return it;
        endfunction

        virtual function void configure();
            peer_cfg.ack_delay_max       = 1;
            model_peer_cfg.ack_delay_max = 3;
            agent_cfg.ack_delay_max      = 2;
        endfunction

        virtual function void corrupt(pa_item_t it);
            it.data.tag = ~it.data.tag;
        endfunction
    endclass : pa_mode_b

    // The agent pushes each item on both lanes.
    class push_ack_mode_b_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_SRC;
            variant = LB_MATCH;
        endfunction
    endclass : push_ack_mode_b_test

    // The agent acks both lanes, replaying the DUT lane's delays.
    class push_ack_mode_b_dst_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_MATCH;
        endfunction
    endclass : push_ack_mode_b_dst_test

    // The model lane reaches every transfer first and waits for the DUT lane.
    class push_ack_mode_b_dst_model_leads_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_model_leads_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_MODEL_LEADS;
        endfunction
    endclass : push_ack_mode_b_dst_model_leads_test

    // The DUT lane makes one transfer more: the drain runs to its deadline and
    // the replay log reports the record the model lane never replayed.
    class push_ack_mode_b_dst_dut_extra_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_dut_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_DUT_EXTRA;
        endfunction
    endclass : push_ack_mode_b_dst_dut_extra_test

    // The model lane makes one transfer more, which it waits for until the
    // drain's deadline: one A2C_REPLAY.
    class push_ack_mode_b_dst_model_extra_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_model_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_MODEL_EXTRA;
        endfunction
    endclass : push_ack_mode_b_dst_model_extra_test

    // The test drops its objection when the DUT lane is done, before the model
    // lane starts its last transfer: the drain must hold the run phase until
    // the model lane has replayed it.
    class push_ack_mode_b_dst_drain_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_DRAIN;
        endfunction
    endclass : push_ack_mode_b_dst_drain_test

    // As push_ack_mode_b_dst_drain_test with a quiet window of one clock and
    // every ack 3 clocks late, and the drop once the DUT lane is idle, so
    // the drain cannot cut. Once the model lane has replayed its last
    // transfer, only its wait for that ack keeps the window from closing
    // before the transfer completes.
    class push_ack_mode_b_dst_drain_short_quiet_test extends push_ack_mode_b_dst_drain_test;
        `uvm_component_utils(push_ack_mode_b_dst_drain_short_quiet_test)

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

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (agent.drv.replay.get_cut() != 0) `uvm_error("LB_MODE_B", "the drain cut the run, so the quiet window went untested")
        endfunction
    endclass : push_ack_mode_b_dst_drain_short_quiet_test

    // As push_ack_mode_b_dst_drain_busy_test with no gaps, so the port
    // never rests from the drop to the end of the test.
    class push_ack_mode_b_dst_drain_busy_zero_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_drain_busy_zero_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_BUSY_ZERO;
        endfunction
    endclass : push_ack_mode_b_dst_drain_busy_zero_test

    // Two busy ports, each with its own replay log: pa as in
    // push_ack_mode_b_dst_drain_busy_zero_test, and pa2, whose peers keep
    // pushing with gaps of 0 to 3 clocks, the model lane's two clocks behind.
    // One drain serves both logs and cuts both at their deadline, so it must
    // end once both ports have completed the transfers their cuts keep, and
    // the run phase must end after that one drain.
    class push_ack_mode_b_dst_two_busy_test extends pa_mode_b;
        pa_config_t             agent2_cfg;
        pa_agent_t              agent2;
        pa_agent_t              peer2;
        pa_agent_t              model_peer2;
        lb_arrivals#(pa_item_t) arrivals2;
        lb_arrivals#(pa_item_t) model_arrivals2;
        pa_item_t               items2[$];
        pa_item_t               model_items2[$];

        `uvm_component_utils(push_ack_mode_b_dst_two_busy_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_BUSY_ZERO;
        endfunction

        // The clock of pa2's three agents.
        virtual function virtual a2c_clk_if pa2_clk();
            return clk_vif;
        endfunction

        protected function pa_config_t pa2_cfg(string name, pa_vif_t lane_vif, a2c_role_e lane_role, string lane_port);
            pa_config_t cfg = lane_cfg(name, lane_vif, lane_role, lane_port);
            cfg.clk_vif = pa2_clk();
            return cfg;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            pa_vif_t    vif2;
            pa_vif_t    model_vif2;
            super.build_phase(phase);
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa2", vif2)) `uvm_fatal("LB_CFG", "no interface pa2")
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa2_model", model_vif2)) `uvm_fatal("LB_CFG", "no interface pa2_model")
            agent2_cfg = pa2_cfg("agent2_cfg", vif2, A2C_DST, "pa2");
            agent2_cfg.model_vif     = model_vif2;
            agent2_cfg.ack_delay_max = 2;
            uvm_config_db#(pa_config_t)::set(this, "agent2", "cfg", agent2_cfg);
            uvm_config_db#(pa_config_t)::set(this, "peer2", "cfg", pa2_cfg("peer2_cfg", vif2, A2C_SRC, "pa2"));
            uvm_config_db#(pa_config_t)::set(this, "model_peer2", "cfg", pa2_cfg("model_peer2_cfg", model_vif2, A2C_SRC, "pa2_model"));
            agent2          = pa_agent_t::type_id::create("agent2", this);
            peer2           = pa_agent_t::type_id::create("peer2", this);
            model_peer2     = pa_agent_t::type_id::create("model_peer2", this);
            arrivals2       = lb_arrivals#(pa_item_t)::type_id::create("arrivals2", this);
            model_arrivals2 = lb_arrivals#(pa_item_t)::type_id::create("model_arrivals2", this);
            for (int unsigned i = 0; i < 11 * n_items; i++) begin
                pa_item_t it = new_item(i);
                items2.push_back(it);
                model_items2.push_back(copy(it));
                it.gap = $urandom_range(3, 0);
                model_items2[i].gap = it.gap + 2 * (i == 0);
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent2.mon.ap.connect(arrivals2.analysis_export);
            agent2.model_mon.ap.connect(model_arrivals2.analysis_export);
            agent2.drv.replay.drain_quiet_cycles    = drain_quiet;
            agent2.drv.replay.drain_deadline_cycles = drain_deadline;
            tracker.logs.push_back(agent2.drv.replay);
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_list_seq#(pa_item_t) s2 = lb_list_seq#(pa_item_t)::type_id::create("s2");
            lb_list_seq#(pa_item_t) m2 = lb_list_seq#(pa_item_t)::type_id::create("m2");
            s2.items = items2;
            m2.items = model_items2;
            fork
                s2.start(peer2.sqr);
                m2.start(model_peer2.sqr);
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("pa2: %0d and %0d transfers on the DUT and model lanes; %0d pairs; cut after %0d",
                                            arrivals2.items.size(), model_arrivals2.items.size(), agent2.model_cmp.get_pairs(),
                                            agent2.drv.replay.get_cut()), UVM_NONE)
            check_cut(agent2.drv.replay, 0, agent2.model_cmp.get_pairs(), arrivals2.items.size(), model_arrivals2.items.size());
            if (arrivals2.items.size() >= items2.size()) `uvm_error("LB_MODE_B", "pa2: the DUT lane's peer ran out of transfers, so the port paused")
            for (int unsigned i = 0; i < arrivals2.items.size() && i < model_arrivals2.items.size(); i++) begin
                if (!arrivals2.items[i].compare(model_arrivals2.items[i])) begin
                    `uvm_error("LB_MODE_B", $sformatf("pa2 transfer %0d: DUT lane %s, model lane %s", i, arrivals2.items[i].convert2string(),
                                                      model_arrivals2.items[i].convert2string()))
                end
            end
        endfunction
    endclass : push_ack_mode_b_dst_two_busy_test

    // As push_ack_mode_b_dst_two_busy_test with pa as in push_ack_mode_b_dst_test
    // and 20 transfers on pa2, whose model lane starts the last 60 clocks
    // after pa's model lane is done. When the test drops, pa is idle and
    // aligned and pa2's model lane is the only one busy, so the drain must
    // stay until it has replayed that transfer.
    class push_ack_mode_b_dst_two_drain_test extends push_ack_mode_b_dst_two_busy_test;
        `uvm_component_utils(push_ack_mode_b_dst_two_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_MATCH;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            items2       = items2[0:19];
            model_items2 = model_items2[0:19];
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_list_seq#(pa_item_t) s2 = lb_list_seq#(pa_item_t)::type_id::create("s2");
            lb_list_seq#(pa_item_t) m2 = lb_list_seq#(pa_item_t)::type_id::create("m2");
            lb_list_seq#(pa_item_t) last2 = lb_list_seq#(pa_item_t)::type_id::create("last2");
            s2.items    = items2;
            m2.items    = model_items2[0:18];
            last2.items = model_items2[19:19];
            fork
                s2.start(peer2.sqr);
                begin
                    m2.start(model_peer2.sqr);
                    wait (done[A2C_MODEL_LANE]);
                    repeat (60) clk_vif.sample_edge();
                    last2.start(model_peer2.sqr);
                end
            join_none
            pa_mode_b::run_phase(phase);
        endtask

        virtual function void check_phase(uvm_phase phase);
            pa_mode_b::check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("pa2: %0d and %0d transfers on the DUT and model lanes; %0d pairs", arrivals2.items.size(),
                                            model_arrivals2.items.size(), agent2.model_cmp.get_pairs()), UVM_NONE)
            if (arrivals2.items.size() != 20 || model_arrivals2.items.size() != 20 || agent2.model_cmp.get_pairs() != 20) begin
                `uvm_error("LB_MODE_B", "pa2: the drain ended before the model lane's last transfer")
            end
            if (ready_calls != 2) `uvm_error("LB_MODE_B", $sformatf("%0d phase_ready_to_end calls, expected 2", ready_calls))
        endfunction
    endclass : push_ack_mode_b_dst_two_drain_test

    // pa never pauses, so the drain cuts it at its deadline. pa2's peers
    // start at the drop and send 15 transfers with four idle clocks before
    // each and no ack delay, its model lane three clocks behind, and pa2's
    // model lane's peer then sends one transfer more two clocks after its
    // last. The model lane waits for it, so pa2 never settles, and its DUT
    // lane has long stopped at the deadline, so the drain gives pa2 up
    // there instead of cutting it: one A2C_DRAIN and one A2C_REPLAY.
    class push_ack_mode_b_dst_two_extra_test extends push_ack_mode_b_dst_two_busy_test;
        `uvm_component_utils(push_ack_mode_b_dst_two_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            drain_deadline = 400;
            agent2_cfg.ack_delay_max = 0;
            items2       = items2[0:14];
            model_items2 = model_items2[0:14];
            foreach (items2[i]) begin
                items2[i].gap       = 4;
                model_items2[i].gap = 4 + 3 * (i == 0);
            end
            model_items2.push_back(new_item(15));
            model_items2[15].gap = 2;
            want_errors = 1;
            want_text.push_back("uvm_test_top.agent2.drv.replay: the model lane waited for transaction 16, which the DUT lane never recorded");
        endfunction

        // Starts pa2's peers at the drop.
        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    lb_list_seq#(pa_item_t) s2 = lb_list_seq#(pa_item_t)::type_id::create("s2");
                    lb_list_seq#(pa_item_t) m2 = lb_list_seq#(pa_item_t)::type_id::create("m2");
                    s2.items = items2;
                    m2.items = model_items2;
                    while (arrivals.items.size() < n_items) clk_vif.sample_edge();
                    fork
                        s2.start(peer2.sqr);
                        m2.start(model_peer2.sqr);
                    join_none
                end
            join_none
            pa_mode_b::run_phase(phase);
        endtask

        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("pa: %0d and %0d transfers, cut after %0d; pa2: %0d and %0d transfers, %0d pairs, cut after %0d; the drain took %0d clocks",
                                            arrivals.items.size(), model_arrivals.items.size(), agent.drv.replay.get_cut(),
                                            arrivals2.items.size(), model_arrivals2.items.size(), agent2.model_cmp.get_pairs(),
                                            agent2.drv.replay.get_cut(), drain_clocks()), UVM_NONE)
            check_lane(A2C_DUT_LANE, arrivals);
            check_lane(A2C_MODEL_LANE, model_arrivals);
            check_cut(agent.drv.replay, n_items, agent.model_cmp.get_pairs(), arrivals.items.size(), model_arrivals.items.size());
            if (agent2.drv.replay.get_cut() != 0) `uvm_error("LB_MODE_B", "pa2: the drain cut a port whose DUT lane had stopped")
            if (arrivals2.items.size() != 15 || model_arrivals2.items.size() != 15 || agent2.model_cmp.get_pairs() != 15) begin
                `uvm_error("LB_MODE_B", "pa2: the lanes did not both complete the 15 transfers")
            end
            if (uvm_report_server::get_server().get_id_count("A2C_DRAIN") != 1) `uvm_error("LB_MODE_B", "expected one A2C_DRAIN warning, for pa2")
            check_cut_time(drain_clocks(), drain_quiet, drain_deadline);
        endfunction

        // The clock counter races the drain on each edge, so it may be slack off.
        protected function void check_drain(int unsigned want, int unsigned slack);
            if (drain_clocks() + slack < want || drain_clocks() > want + slack) begin
                `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected %0d", drain_clocks(), want))
            end
        endfunction
    endclass : push_ack_mode_b_dst_two_extra_test

    // As push_ack_mode_b_dst_two_extra_test with pa2 on clk2, three times
    // the period of pa's clock, three transfers on pa2 with no idle clocks
    // and the lanes in step, and deadlines of 200 clocks on pa and 100 on
    // pa2. The drain counts each log's clocks on its own clock, so it cuts
    // pa after 200 of pa's clocks and ends when it gives pa2 up, after 300.
    class push_ack_mode_b_dst_two_clock_test extends push_ack_mode_b_dst_two_extra_test;
        `uvm_component_utils(push_ack_mode_b_dst_two_clock_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function virtual a2c_clk_if pa2_clk();
            virtual a2c_clk_if clk2;
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk2", clk2)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk2'")
            return clk2;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            items2       = items2[0:2];
            model_items2 = model_items2[0:2];
            foreach (items2[i]) begin
                items2[i].gap       = 0;
                model_items2[i].gap = 0;
            end
            model_items2.push_back(new_item(3));
            model_items2[3].gap = 2;
            drain_deadline = 200;
            want_text[0] = "uvm_test_top.agent2.drv.replay: the model lane waited for transaction 4, which the DUT lane never recorded";
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent2.drv.replay.drain_deadline_cycles = 100;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            realtime cut_after = tracker.cut_time[agent.drv.replay] - drop_time;
            `uvm_info("LB_STATS", $sformatf("pa2: %0d and %0d transfers, %0d pairs; pa cut %0t after the drop; the drain took %0d clocks",
                                            arrivals2.items.size(), model_arrivals2.items.size(), agent2.model_cmp.get_pairs(), cut_after,
                                            drain_clocks()), UVM_NONE)
            check_cut(agent.drv.replay, n_items, agent.model_cmp.get_pairs(), arrivals.items.size(), model_arrivals.items.size());
            if (arrivals2.items.size() != 3 || model_arrivals2.items.size() != 3 || agent2.model_cmp.get_pairs() != 3) begin
                `uvm_error("LB_MODE_B", "pa2: the lanes did not both complete the 3 transfers")
            end
            // clk2's edges fall on every third of pa's.
            check_drain(300, 3);
            // The drop is at a falling edge of pa's 10ns clock.
            if (cut_after < 1980ns || cut_after > 2010ns) begin
                `uvm_error("LB_MODE_B", $sformatf("pa was cut %0t after the drop, not at its deadline of 200 of its own clocks", cut_after))
            end
        endfunction
    endclass : push_ack_mode_b_dst_two_clock_test

    // Counts the warnings and infos with one id, and keeps the warnings'
    // text.
    class lb_id_counter extends uvm_report_catcher;
        string       id;
        int unsigned warnings;
        int unsigned infos;
        string       messages[$];

        `uvm_object_utils(lb_id_counter)

        function new(string name = "lb_id_counter");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_id() == id && get_severity() == UVM_WARNING) begin
                warnings++;
                messages.push_back(get_message());
            end
            if (get_id() == id && get_severity() == UVM_INFO) infos++;
            return THROW;
        endfunction
    endclass : lb_id_counter

    // pa as in push_ack_mode_b_dst_drain_busy_zero_test, but on the
    // phase_ready_to_end() call that follows the first drain's cut, the
    // test raises its objection again for 50 clocks. The traffic after the
    // first cut must be compared, so the second drain undoes that cut. pa
    // has not paused since, so the second drain cuts it again on its first
    // clock rather than at its deadline.
    class push_ack_mode_b_dst_cut_resume_test extends pa_mode_b;
        int unsigned  first_cut;
        int unsigned  hold = 50;
        lb_id_counter cuts;
        // What the one A2C_CUT warning, for the last cut, must say.
        string        cut_text = "so this drain cut it again on its first clock";
        // The clocks of the third and fourth phase_ready_to_end() calls,
        // the start and the end of the second drain.
        int unsigned second_start;
        int unsigned second_end;

        `uvm_component_utils(push_ack_mode_b_dst_cut_resume_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_BUSY_ZERO;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            cuts = lb_id_counter::type_id::create("cuts");
            cuts.id = "A2C_CUT";
            uvm_report_cb::add(null, cuts);
        endfunction

        // Runs on the call that follows the first drain.
        virtual function void after_first_drain();
        endfunction

        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (phase.get_imp() != uvm_run_phase::get()) return;
            if (ready_calls == 3) second_start = clocks;
            if (ready_calls == 4) second_end = clocks;
            if (ready_calls != 2) return;
            first_cut = agent.drv.replay.get_cut();
            after_first_drain();
            phase.raise_objection(this, "after the first cut");
            fork
                begin
                    repeat (hold) clk_vif.sample_edge();
                    phase.drop_objection(this, "after the first cut");
                end
            join_none
        endfunction

        virtual function void check_second_drain(int unsigned took);
            // The cut, then the model lane a clock behind.
            if (took > 5) `uvm_error("LB_MODE_B", $sformatf("the second drain took %0d clocks, expected a cut on its first clock", took))
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned cut = agent.drv.replay.get_cut();
            `uvm_info("LB_STATS", $sformatf("first cut after %0d, last after %0d; %0d phase_ready_to_end calls; the second drain took %0d clocks",
                                            first_cut, cut, ready_calls, second_end - second_start), UVM_NONE)
            check_lane(A2C_DUT_LANE, arrivals);
            check_lane(A2C_MODEL_LANE, model_arrivals);
            check_cut(agent.drv.replay, n_items, agent.model_cmp.get_pairs(), arrivals.items.size(), model_arrivals.items.size());
            if (first_cut <= n_items) `uvm_error("LB_MODE_B", "the first drain did not cut the run")
            if (cut <= first_cut + 10) `uvm_error("LB_MODE_B", $sformatf("the last cut, after %0d, is not well past the first, after %0d", cut, first_cut))
            if (ready_calls < 4) `uvm_error("LB_MODE_B", $sformatf("%0d phase_ready_to_end calls, so the second drain never ended", ready_calls))
            check_second_drain(second_end - second_start);
            if (cuts.messages.size() != 1 || !a2c_contains(cuts.messages[0], cut_text)) begin
                `uvm_error("LB_MODE_B", $sformatf("expected one A2C_CUT warning saying '%s': %p", cut_text, cuts.messages))
            end
        endfunction
    endclass : push_ack_mode_b_dst_cut_resume_test

    // As push_ack_mode_b_dst_cut_resume_test, but pa's lanes both pause
    // for 40 clocks, more than the quiet window of 30, a few transfers after
    // the first drain, and the test holds for 60 clocks. pa has paused since
    // the first cut, so the second drain waits its whole deadline again
    // before it cuts.
    class push_ack_mode_b_dst_cut_pause_resume_test extends push_ack_mode_b_dst_cut_resume_test;
        `uvm_component_utils(push_ack_mode_b_dst_cut_pause_resume_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold     = 60;
            cut_text = "did not pause for drain_quiet_cycles (+a2c_drain_quiet_cycles) clocks before the deadline";
        endfunction

        // The peers take each item's gap when they fetch it, a transfer or
        // two ahead.
        virtual function void after_first_drain();
            int unsigned k = arrivals.items.size() + 5;
            items[k].gap       = 40;
            model_items[k].gap = 40;
        endfunction

        virtual function void check_second_drain(int unsigned took);
            if (took + 1 < drain_deadline) begin
                `uvm_error("LB_MODE_B", $sformatf("the second drain took %0d clocks, expected its deadline of %0d", took, drain_deadline))
            end
        endfunction
    endclass : push_ack_mode_b_dst_cut_pause_resume_test

    // The first drain expires with the model lane's late transfer pending,
    // and the test sends the last transfer after it: the model lane's start
    // since the expiry must bring a second drain that replays it. One more
    // transfer, sent after the second drain and late on the model lane, must
    // bring a third.
    class push_ack_mode_b_dst_after_expiry_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_after_expiry_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_AFTER_EXPIRY;
        endfunction
    endclass : push_ack_mode_b_dst_after_expiry_test

    // The model lane's peer pushes one item with different data: one
    // A2C_MODEL_CMP naming its pair.
    class push_ack_mode_b_dst_mismatch_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_MISMATCH;
        endfunction
    endclass : push_ack_mode_b_dst_mismatch_test

    // Both peers keep pushing after the test drops its objection, so the
    // drain's quiet window never comes: it must cut the run at its
    // deadline, after the transfers the DUT lane has started then, and end
    // once both lanes have completed them, with no A2C_REPLAY.
    class push_ack_mode_b_dst_drain_busy_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_drain_busy_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_BUSY;
        endfunction
    endclass : push_ack_mode_b_dst_drain_busy_test

    // Both peers send 60 transfers more after the drop, the model lane's a
    // clock behind, and stop, as a DMA tail does, well before the deadline.
    // One pause of 10 clocks idles the port for less than the quiet window.
    // The drain must wait out the tail and check all of it, with no cut.
    class push_ack_mode_b_dst_tail_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_tail_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_TAIL;
        endfunction
    endclass : push_ack_mode_b_dst_tail_test

    // pa as in push_ack_mode_b_dst_test, and pa2 on clk3, a gated clock of
    // twice pa's period. pa2's peers start at the drop and send five transfers
    // with no idle clocks and the lanes in step, and the test then stops clk3
    // with both lanes idle. pa2 has not been idle for its quiet window of 50
    // clocks, and its clock stop, set through the config_db, is 50 clocks too,
    // so the drain must see clk3 stop 50 and a half of its periods after its
    // last rising edge and settle pa2 then: no error.
    class push_ack_mode_b_dst_clock_stop_test extends push_ack_mode_b_dst_two_busy_test;
        int unsigned model_sends = 5;
        realtime     stop_time;
        realtime     end_time;

        `uvm_component_utils(push_ack_mode_b_dst_clock_stop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_MATCH;
        endfunction

        virtual function virtual a2c_clk_if pa2_clk();
            virtual a2c_clk_if clk3;
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            return clk3;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            items2       = items2[0:4];
            model_items2 = model_items2[0:model_sends - 1];
            foreach (items2[i]) items2[i].gap = 0;
            foreach (model_items2[i]) model_items2[i].gap = 0;
            uvm_config_db#(int unsigned)::set(this, "agent2.drv.replay", "a2c_clock_stop_cycles", 50);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent2.drv.replay.drain_quiet_cycles    = 50;
            agent2.drv.replay.drain_deadline_cycles = 1000;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    lb_list_seq#(pa_item_t) s2 = lb_list_seq#(pa_item_t)::type_id::create("s2");
                    lb_list_seq#(pa_item_t) m2 = lb_list_seq#(pa_item_t)::type_id::create("m2");
                    s2.items = items2;
                    m2.items = model_items2;
                    wait (dropped_at != 0);
                    fork
                        s2.start(peer2.sqr);
                        m2.start(model_peer2.sqr);
                    join_none
                    while (arrivals2.items.size() < 5 || model_arrivals2.items.size() < model_sends) agent2_cfg.clk_vif.sample_edge();
                    repeat (2) agent2_cfg.clk_vif.sample_edge();
                    lb_clk3_run = 0;
                    stop_time   = $realtime;
                end
            join_none
            pa_mode_b::run_phase(phase);
        endtask

        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (phase.get_imp() == uvm_run_phase::get() && ready_calls == 2) end_time = $realtime;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            realtime waited = end_time - stop_time;
            pa_mode_b::check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("pa2: %0d and %0d transfers, %0d pairs; the drain ended %0t after clk3 stopped", arrivals2.items.size(),
                                            model_arrivals2.items.size(), agent2.model_cmp.get_pairs(), waited), UVM_NONE)
            if (stop_time == 0 || stop_time < drop_time) `uvm_error("LB_MODE_B", "clk3 stopped before the drop, so the drain did not see it stop")
            // 50 and a half periods of 20ns after clk3's last rising edge,
            // which is at most a period before the stop.
            if (waited < 985ns || waited > 1011ns) begin
                `uvm_error("LB_MODE_B", $sformatf("the drain ended %0t after clk3 stopped, expected about 1010ns", waited))
            end
            if (arrivals2.items.size() != 5 || model_arrivals2.items.size() != model_sends) begin
                `uvm_error("LB_MODE_B", "pa2: the lanes did not complete their transfers before clk3 stopped")
            end
            if (agent2.model_cmp.get_pairs() != model_sends) begin
                `uvm_error("LB_MODE_B", $sformatf("pa2: model_cmp paired %0d transfers, expected %0d", agent2.model_cmp.get_pairs(), model_sends))
            end
            if (agent2.drv.replay.get_cut() != 0) `uvm_error("LB_MODE_B", "pa2: the drain cut the run")
            check_drain_warnings();
        endfunction

        virtual function void check_drain_warnings();
            if (uvm_report_server::get_server().get_id_count("A2C_DRAIN") != 0) `uvm_error("LB_MODE_B", "an A2C_DRAIN warning for a settled port")
        endfunction
    endclass : push_ack_mode_b_dst_clock_stop_test

    // As push_ack_mode_b_dst_clock_stop_test with the model lane one
    // transfer short when clk3 stops: the drain gives pa2 up with an
    // A2C_DRAIN warning, and the replay log reports the transfer it owes in
    // one A2C_REPLAY.
    class push_ack_mode_b_dst_clock_stop_owed_test extends push_ack_mode_b_dst_clock_stop_test;
        `uvm_component_utils(push_ack_mode_b_dst_clock_stop_owed_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            model_sends = 4;
            demote_id   = "A2C_REPLAY";
            want_errors = 1;
            want_text.push_back("uvm_test_top.agent2.drv.replay: end of test with 1 responses the DUT lane recorded and the model lane never replayed, from transaction 5");
        endfunction

        // The replay log reports the unpaired DUT lane transfer.
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent2.model_cmp.counted = 1;
        endfunction

        virtual function void check_drain_warnings();
            if (uvm_report_server::get_server().get_id_count("A2C_DRAIN") != 1) `uvm_error("LB_MODE_B", "expected one A2C_DRAIN warning, for pa2's stopped clock")
        endfunction
    endclass : push_ack_mode_b_dst_clock_stop_owed_test

    // As push_ack_mode_b_dst_drain_busy_zero_test, with the model lane's
    // peer stopping 50 transfers after the drop. The DUT lane is still
    // pushing at the deadline, so the drain cuts the run there, but the
    // model lane never completes the transfers the cut keeps: the drain
    // gives the log up when its catch-up, by default the deadline again,
    // runs out, and the log reports one A2C_REPLAY.
    class push_ack_mode_b_dst_cut_short_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_cut_short_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_BUSY_ZERO;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            model_items = model_items[0:n_items + 49];
            want_errors = 1;
            want_text.push_back("uvm_test_top.agent.drv.replay: the drain cut the run after transaction");
        endfunction

        // The replay log reports the shortfall.
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.counted = 1;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned cut = agent.drv.replay.get_cut();
            `uvm_info("LB_STATS", $sformatf("cut after %0d; %0d and %0d transfers on the DUT and model lanes; the drain took %0d clocks",
                                            cut, arrivals.items.size(), model_arrivals.items.size(), drain_clocks()), UVM_NONE)
            if (cut <= n_items + 50) `uvm_error("LB_MODE_B", $sformatf("the drain cut the run after transfer %0d, before the model lane stopped", cut))
            if (model_arrivals.items.size() != n_items + 50) `uvm_error("LB_MODE_B", "the model lane did not stop where its peer did")
            // The clock counter races the drain on each edge, so it may be one off.
            if (drain_clocks() + 1 < 2 * drain_deadline || drain_clocks() > 2 * drain_deadline + 1) begin
                `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected a cut at its deadline of %0d and the give-up as many clocks later",
                                                  drain_clocks(), drain_deadline))
            end
        endfunction
    endclass : push_ack_mode_b_dst_cut_short_test

    // As push_ack_mode_b_dst_drain_busy_zero_test, with one transfer more
    // on the model lane's peer, its sixth. The lanes' counts and timing
    // stay in step, but from that transfer on each model lane item pairs
    // with the DUT lane's item before it, so every pair from the sixth to
    // the cut mismatches: ten A2C_MODEL_CMP printed and one summary.
    class push_ack_mode_b_dst_cut_model_extra_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_cut_model_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_BUSY_ZERO;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            model_items.insert(5, new_item(100000));
            demoter.demote_id = "A2C_MODEL_CMP";
            want_errors       = 11;
            want_text.push_back("uvm_test_top.agent.model_cmp: pair 6: DUT");
            want_text.push_back("uvm_test_top.agent.model_cmp: ");
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned pairs = agent.model_cmp.get_pairs();
            `uvm_info("LB_STATS", $sformatf("cut after %0d; %0d pairs", agent.drv.replay.get_cut(), pairs), UVM_NONE)
            check_cut(agent.drv.replay, n_items, pairs, arrivals.items.size(), model_arrivals.items.size());
        endfunction
    endclass : push_ack_mode_b_dst_cut_model_extra_test

    // pa in its tail, as in push_ack_mode_b_dst_tail_test, and pa2 on clk3
    // with a clock stop of 5 clocks, a quiet window of 10 and a deadline of
    // 100. clk3 stops at the drop with pa2 idle, so the drain settles pa2 on
    // the stop. clk3 runs again once pa's model lane has completed its
    // tail, and pa2's DUT lane makes two transfers at once. pa2's model lane
    // makes them only after pa has settled, so only a watch of pa2 resumed
    // with its clock keeps the drain until they are replayed: no error, and
    // both pairs compared.
    class push_ack_mode_b_dst_clock_resume_test extends push_ack_mode_b_dst_two_busy_test;
        int unsigned model_sends = 2;
        int unsigned pa2_stop = 5;
        realtime     resume_time;

        `uvm_component_utils(push_ack_mode_b_dst_clock_resume_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_TAIL;
        endfunction

        virtual function virtual a2c_clk_if pa2_clk();
            virtual a2c_clk_if clk3;
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            return clk3;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            items2       = items2[0:1];
            model_items2 = model_items2[0:model_sends - 1];
            foreach (items2[i]) items2[i].gap = 0;
            foreach (model_items2[i]) model_items2[i].gap = 0;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent2.drv.replay.drain_quiet_cycles    = 10;
            agent2.drv.replay.drain_deadline_cycles = 100;
            agent2.drv.replay.clock_stop_cycles     = pa2_stop;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    lb_list_seq#(pa_item_t) s2 = lb_list_seq#(pa_item_t)::type_id::create("s2");
                    lb_list_seq#(pa_item_t) m2 = lb_list_seq#(pa_item_t)::type_id::create("m2");
                    s2.items = items2;
                    m2.items = model_items2;
                    wait (drop_time != 0);
                    lb_clk3_run = 0;
                    while (model_arrivals.items.size() < n_items + 60) clk_vif.sample_edge();
                    lb_clk3_run = 1;
                    resume_time = $realtime;
                    fork
                        s2.start(peer2.sqr);
                    join_none
                    // pa settles drain_quiet clocks after its lanes go idle.
                    repeat (drain_quiet + 5) clk_vif.sample_edge();
                    m2.start(model_peer2.sqr);
                end
            join_none
            pa_mode_b::run_phase(phase);
        endtask

        virtual function void check_phase(uvm_phase phase);
            pa_mode_b::check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("pa2: %0d and %0d transfers, %0d pairs; clk3 ran again %0t after the drop", arrivals2.items.size(),
                                            model_arrivals2.items.size(), agent2.model_cmp.get_pairs(), resume_time - drop_time), UVM_NONE)
            // The drain sees clk3 stop 110ns after its last rising edge.
            if (resume_time == 0 || resume_time - drop_time < 200ns) `uvm_error("LB_MODE_B", "clk3 ran again before the drain saw it stop")
            if (arrivals2.items.size() != 2 || model_arrivals2.items.size() != model_sends) begin
                `uvm_error("LB_MODE_B", "pa2: the lanes did not complete their transfers before the run phase ended")
            end
            if (agent2.model_cmp.get_pairs() != model_sends) begin
                `uvm_error("LB_MODE_B", $sformatf("pa2: model_cmp paired %0d transfers, expected %0d", agent2.model_cmp.get_pairs(), model_sends))
            end
            if (agent2.drv.replay.get_cut() != 0) `uvm_error("LB_MODE_B", "pa2: the drain cut the run")
            check_drain_warnings();
        endfunction

        virtual function void check_drain_warnings();
            if (uvm_report_server::get_server().get_id_count("A2C_DRAIN") != 0) `uvm_error("LB_MODE_B", "an A2C_DRAIN warning for a settled port")
        endfunction
    endclass : push_ack_mode_b_dst_clock_resume_test

    // As push_ack_mode_b_dst_clock_resume_test with pa2's model lane one
    // transfer short: the resumed watch keeps the drain to pa2's deadline
    // and gives it up there with an A2C_DRAIN warning, and the replay log
    // reports the second transfer in one A2C_REPLAY.
    class push_ack_mode_b_dst_clock_resume_owed_test extends push_ack_mode_b_dst_clock_resume_test;
        `uvm_component_utils(push_ack_mode_b_dst_clock_resume_owed_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            model_sends = 1;
            demote_id   = "A2C_REPLAY";
            want_errors = 1;
            want_text.push_back("uvm_test_top.agent2.drv.replay: end of test with 1 responses the DUT lane recorded and the model lane never replayed, from transaction 2");
        endfunction

        // The replay log reports the unpaired DUT lane transfer.
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent2.model_cmp.counted = 1;
        endfunction

        virtual function void check_drain_warnings();
            if (uvm_report_server::get_server().get_id_count("A2C_DRAIN") != 1) `uvm_error("LB_MODE_B", "expected one A2C_DRAIN warning, for pa2's deadline")
        endfunction
    endclass : push_ack_mode_b_dst_clock_resume_owed_test

    // As push_ack_mode_b_dst_drain_busy_zero_test: the drain's cut drops
    // transfers, which is one A2C_CUT warning.
    class push_ack_mode_b_dst_cut_warning_test extends pa_mode_b;
        lb_id_counter cuts;
        bit           cut_expected;

        `uvm_component_utils(push_ack_mode_b_dst_cut_warning_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_BUSY_ZERO;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            cuts = lb_id_counter::type_id::create("cuts");
            cuts.id = "A2C_CUT";
            uvm_report_cb::add(null, cuts);
            if (cut_expected) uvm_config_db#(bit)::set(this, "agent.drv.replay", "a2c_drain_cut_expected", 1'b1);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_CUT warnings, %0d infos", cuts.warnings, cuts.infos), UVM_NONE)
            if (cuts.warnings != !cut_expected || cuts.infos != cut_expected) begin
                `uvm_error("LB_MODE_B", $sformatf("expected %0d A2C_CUT warning and %0d info, got %0d and %0d", !cut_expected, cut_expected,
                                                  cuts.warnings, cuts.infos))
            end
            super.report_phase(phase);
        endfunction
    endclass : push_ack_mode_b_dst_cut_warning_test

    // As push_ack_mode_b_dst_cut_warning_test with a2c_drain_cut_expected
    // set on the log through the config_db: the cut is one A2C_CUT info.
    class push_ack_mode_b_dst_cut_expected_test extends push_ack_mode_b_dst_cut_warning_test;
        `uvm_component_utils(push_ack_mode_b_dst_cut_expected_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            cut_expected = 1;
        endfunction
    endclass : push_ack_mode_b_dst_cut_expected_test

    // A drain deadline of 19 clocks under a quiet window of 20, both set
    // through the config_db, is one A2C_CFG error at the start of
    // simulation.
    class push_ack_mode_b_dst_cfg_deadline_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_cfg_deadline_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role        = A2C_DST;
            variant     = LB_MATCH;
            demote_id   = "A2C_CFG";
            want_errors = 1;
            want_text.push_back("uvm_test_top.agent.drv.replay: drain_deadline_cycles (+a2c_drain_deadline_cycles), 19, is below drain_quiet_cycles (+a2c_drain_quiet_cycles), 20");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            uvm_config_db#(int unsigned)::set(this, "agent.drv.replay", "a2c_drain_quiet_cycles", 20);
            uvm_config_db#(int unsigned)::set(this, "agent.drv.replay", "a2c_drain_deadline_cycles", 19);
        endfunction

        // As lb_hs_mode_b's, but the log keeps what the config_db gave it.
        virtual function void connect_phase(uvm_phase phase);
            agent.mon.ap.connect(arrivals.analysis_export);
            agent.model_mon.ap.connect(model_arrivals.analysis_export);
            tracker.logs.push_back(agent.drv.replay);
        endfunction
    endclass : push_ack_mode_b_dst_cfg_deadline_test

    // A replay log with no clk_vif is one A2C_CFG error, and the drain
    // leaves it out. The lanes are done at the drop, so nothing is owed.
    class push_ack_mode_b_dst_cfg_no_clock_test extends pa_mode_b;
        `uvm_component_utils(push_ack_mode_b_dst_cfg_no_clock_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role        = A2C_DST;
            variant     = LB_MATCH;
            demote_id   = "A2C_CFG";
            want_errors = 1;
            want_text.push_back("uvm_test_top.agent.drv.replay: the replay log has no clk_vif, so the end-of-test drain cannot watch it");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.drv.replay.clk_vif = null;
            tracker.logs.delete();
        endfunction
    endclass : push_ack_mode_b_dst_cfg_no_clock_test

    // As push_ack_mode_b_dst_clock_resume_test with pa2's clock stop at its
    // default of 1000 clocks. pa2's peers start at the drop, its model lane
    // eight clocks behind, and clk3 pauses for 15 of its periods, more than
    // pa2's quiet window of 10, once pa2's DUT lane has made both transfers
    // and before its model lane has. The pause is far short of the clock
    // stop, so the drain must go on watching pa2 through it: no A2C_DRAIN,
    // and both pairs compared.
    class push_ack_mode_b_dst_clock_slow_test extends push_ack_mode_b_dst_clock_resume_test;
        int unsigned pending_at_pause;

        `uvm_component_utils(push_ack_mode_b_dst_clock_slow_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            pa2_stop = 1000;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            model_items2[0].gap = 8;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    lb_list_seq#(pa_item_t) s2 = lb_list_seq#(pa_item_t)::type_id::create("s2");
                    lb_list_seq#(pa_item_t) m2 = lb_list_seq#(pa_item_t)::type_id::create("m2");
                    s2.items = items2;
                    m2.items = model_items2;
                    wait (drop_time != 0);
                    fork
                        s2.start(peer2.sqr);
                        m2.start(model_peer2.sqr);
                    join_none
                    while (arrivals2.items.size() < 2) agent2_cfg.clk_vif.sample_edge();
                    pending_at_pause = agent2.drv.replay.pending();
                    lb_clk3_run = 0;
                    #300ns;
                    lb_clk3_run = 1;
                    resume_time = $realtime;
                end
            join_none
            pa_mode_b::run_phase(phase);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (pending_at_pause == 0) `uvm_error("LB_MODE_B", "pa2's model lane had caught up before the pause, so the pause went untested")
        endfunction
    endclass : push_ack_mode_b_dst_clock_slow_test

    // pa as in push_ack_mode_b_dst_test, and pa2 on clk5, which never rises,
    // so none of pa2's agents gets past reset. The drain must take clk5 as
    // stopped and settle pa2 at once: no error, and an end well before the
    // timeout.
    class push_ack_mode_b_dst_clock_never_test extends push_ack_mode_b_dst_two_busy_test;
        `uvm_component_utils(push_ack_mode_b_dst_clock_never_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_MATCH;
        endfunction

        virtual function virtual a2c_clk_if pa2_clk();
            virtual a2c_clk_if clk5;
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk5", clk5)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk5'")
            return clk5;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            uvm_top.set_timeout(200us, 1);
        endfunction

        virtual task run_phase(uvm_phase phase);
            pa_mode_b::run_phase(phase);
        endtask

        virtual function void check_phase(uvm_phase phase);
            pa_mode_b::check_phase(phase);
            if (arrivals2.items.size() != 0 || model_arrivals2.items.size() != 0) `uvm_error("LB_MODE_B", "pa2 transferred on a clock that never rose")
            if (uvm_report_server::get_server().get_id_count("A2C_DRAIN") != 0) `uvm_error("LB_MODE_B", "an A2C_DRAIN warning for pa2, which was idle")
        endfunction
    endclass : push_ack_mode_b_dst_clock_never_test

    // As push_ack_mode_b_dst_clock_resume_test, with pa's quiet window at
    // 120 clocks so it holds the drain, and pa2's deadline at 40. clk3 runs
    // 50 clocks past the drop, so pa2 settles on its quiet window and
    // passes its deadline settled, then stops for 10 periods and runs
    // again, and pa2's lanes make their transfers at once, the model lane's
    // three clocks behind. The resumed watch must give pa2 a new deadline:
    // no A2C_DRAIN, and both pairs compared.
    class push_ack_mode_b_dst_clock_resume_late_test extends push_ack_mode_b_dst_clock_resume_test;
        `uvm_component_utils(push_ack_mode_b_dst_clock_resume_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            drain_quiet = 120;
            model_items2[0].gap = 3;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent2.drv.replay.drain_deadline_cycles = 40;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    lb_list_seq#(pa_item_t) s2 = lb_list_seq#(pa_item_t)::type_id::create("s2");
                    lb_list_seq#(pa_item_t) m2 = lb_list_seq#(pa_item_t)::type_id::create("m2");
                    s2.items = items2;
                    m2.items = model_items2;
                    wait (drop_time != 0);
                    repeat (50) agent2_cfg.clk_vif.sample_edge();
                    lb_clk3_run = 0;
                    #200ns;
                    lb_clk3_run = 1;
                    resume_time = $realtime;
                    fork
                        s2.start(peer2.sqr);
                        m2.start(model_peer2.sqr);
                    join_none
                end
            join_none
            pa_mode_b::run_phase(phase);
        endtask
    endclass : push_ack_mode_b_dst_clock_resume_late_test

    // As push_ack_mode_b_dst_cfg_deadline_test, with the window set again
    // as int and the deadline as uvm_config_int, the type
    // +uvm_set_config_int uses, over the int unsigned values the parent
    // sets: the A2C_CFG must name the int and uvm_config_int values.
    class push_ack_mode_b_dst_cfg_types_test extends push_ack_mode_b_dst_cfg_deadline_test;
        `uvm_component_utils(push_ack_mode_b_dst_cfg_types_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_text[0] = "uvm_test_top.agent.drv.replay: drain_deadline_cycles (+a2c_drain_deadline_cycles), 18, is below drain_quiet_cycles (+a2c_drain_quiet_cycles), 21";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            uvm_config_db#(int)::set(this, "agent.drv.replay", "a2c_drain_quiet_cycles", 21);
            uvm_config_int::set(this, "agent.drv.replay", "a2c_drain_deadline_cycles", 18);
        endfunction
    endclass : push_ack_mode_b_dst_cfg_types_test

    // As push_ack_mode_b_dst_drain_test, as a hand-written test may be
    // written: the peers, which stand in for the two DUTs, run in
    // run_phase(), and the test raises and drops its one objection in
    // main_phase(). UVM 1.2 calls the run phase's phase_ready_to_end() only
    // once the runtime phases after main_phase() have run, which here takes
    // no time, so the drain must still start at the drop and hold the end
    // of the test until the model lane has made its late transfer.
    class push_ack_mode_b_dst_main_phase_test extends push_ack_mode_b_dst_drain_test;
        realtime first_ready;

        `uvm_component_utils(push_ack_mode_b_dst_main_phase_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            clk_vif.wait_reset_release();
            fork
                send(peer, items, A2C_DUT_LANE);
                send(model_peer, model_items, A2C_MODEL_LANE);
            join_none
            forever begin
                clk_vif.sample_edge();
                clocks++;
            end
        endtask

        virtual task main_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            wait_drop();
            pending_at_drop = agent.drv.replay.pending();
            dropped_at      = clocks;
            drop_time       = $realtime;
            phase.drop_objection(this);
        endtask

        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (phase.get_imp() == uvm_run_phase::get() && ready_calls == 1) first_ready = $realtime;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("main_phase() dropped at %0t; the run phase's first phase_ready_to_end() came %0t later",
                                            drop_time, first_ready - drop_time), UVM_NONE)
            if (drop_time == 0 || first_ready != drop_time) begin
                `uvm_error("LB_MODE_B", "the run phase did not become ready to end at main_phase()'s drop, so the drain did not start there")
            end
        endfunction
    endclass : push_ack_mode_b_dst_main_phase_test
