// Tests of how a Mode B run completes: a counter that takes the model
// lane's count as the DUT lane's expectation, and a comparator that
// compared no pair. Included in a2c_uvm_loopback_pkg after the agents'
// tests, whose typedefs they use.

    // Mode B on rv and rv_model, the agent the A2C_DST side, with no count
    // declared: the counter has expect_from_model set, so the model lane's
    // count is the DUT lane's expectation. The model lane's peer runs with
    // longer gaps, so wait_for_count() must hold until the model lane's last
    // beat and a quiet window after it. With dut_short set the DUT lane's
    // peer sends two beats fewer, which the counter reports as two missing
    // on the DUT lane.
    class lb_expect_from_model_test extends lb_mode_b_base;
        bit                       dut_short = 0;
        rv_agent_t                agent;
        rv_agent_t                peer;
        rv_agent_t                model_peer;
        rv_counter_t              counter;
        rv_item_t                 items[$];
        rv_item_t                 model_items[$];
        lb_arrivals#(rv_item_t)   model_arrivals;
        int unsigned              model_at_return;

        `uvm_component_utils(lb_expect_from_model_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_items = 40;
        endfunction

        protected function rv_config_t lane_cfg(string name, rv_vif_t lane_vif, a2c_role_e lane_role, string port);
            rv_config_t cfg = rv_config_t::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = port;
            return cfg;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_vif_t    vif;
            rv_vif_t    model_vif;
            rv_config_t agent_cfg;
            if (dut_short) begin
                demote_id   = "A2C_TXN_COUNT";
                want_errors = 1;
                want_text.push_back("rv DUT lane");
                want_text.push_back("2 missing");
            end
            super.build_phase(phase);
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv_model'")
            for (int unsigned i = 0; i < n_items; i++) begin
                rv_item_t it = rv_item_t::type_id::create("it");
                rv_item_t m;
                if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
                it.gap = 0;
                $cast(m, it.clone());
                m.gap = $urandom_range(6, 2);
                if (!dut_short || i < n_items - 2) items.push_back(it);
                model_items.push_back(m);
            end
            agent_cfg = lane_cfg("agent_cfg", vif, A2C_DST, "rv");
            agent_cfg.model_vif = model_vif;
            uvm_config_db#(rv_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(rv_config_t)::set(this, "peer", "cfg", lane_cfg("peer_cfg", vif, A2C_SRC, "rv"));
            uvm_config_db#(rv_config_t)::set(this, "model_peer", "cfg", lane_cfg("model_peer_cfg", model_vif, A2C_SRC, "rv_model"));
            uvm_config_db#(bit)::set(this, "counter", "a2c_expect_from_model", 1'b1);
            agent      = rv_agent_t::type_id::create("agent", this);
            peer       = rv_agent_t::type_id::create("peer", this);
            model_peer = rv_agent_t::type_id::create("model_peer", this);
            counter    = rv_counter_t::type_id::create("counter", this);
            counter.port_name = "rv";
            counter.dual      = 1;
            model_arrivals = lb_arrivals#(rv_item_t)::type_id::create("model_arrivals", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            agent.mon.ap.connect(counter.analysis_export);
            agent.model_mon.ap.connect(counter.model_export);
            agent.model_mon.ap.connect(model_arrivals.analysis_export);
        endfunction

        protected task send(rv_agent_t src, rv_item_t list[$]);
            lb_list_seq#(rv_item_t) seq = lb_list_seq#(rv_item_t)::type_id::create("seq");
            seq.items = list;
            seq.start(src.sqr);
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                send(peer, items);
                send(model_peer, model_items);
            join_none
            counter.wait_for_count(clk_vif, 100 * n_items, 20);
            model_at_return = model_arrivals.items.size();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (!counter.expect_from_model) `uvm_error("LB_COMPLETION", "the counter did not read a2c_expect_from_model")
            if (counter.declared() != 0) `uvm_error("LB_COMPLETION", $sformatf("the test declared %0d transactions", counter.declared()))
            if (model_at_return != n_items) begin
                `uvm_error("LB_COMPLETION", $sformatf("wait_for_count() returned after %0d of the model lane's %0d beats", model_at_return, n_items))
            end
            if (agent.model_cmp.get_pairs() != n_items - (dut_short ? 2 : 0)) begin
                `uvm_error("LB_COMPLETION", $sformatf("model_cmp paired %0d beats", agent.model_cmp.get_pairs()))
            end
        endfunction
    endclass : lb_expect_from_model_test

    class lb_expect_from_model_short_test extends lb_expect_from_model_test;
        `uvm_component_utils(lb_expect_from_model_short_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dut_short = 1;
        endfunction

        // The DUT lane's last two beats never come, so the model lane's are
        // left unpaired; the counter reported the shortfall.
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.counted = 1;
        endfunction
    endclass : lb_expect_from_model_short_test

    // Mode B on rv and rv_model with the agent the A2C_DST side and idle
    // sources on both lanes: its model_cmp compares no pair, which check_phase reports
    // as one A2C_NO_PAIRS error. With waive set the test sets
    // a2c_allow_no_pairs on the comparator, and no error comes.
    class lb_no_pairs_test extends lb_mode_b_base;
        bit        waive = 0;
        rv_agent_t agent;
        rv_agent_t peer;
        rv_agent_t model_peer;

        `uvm_component_utils(lb_no_pairs_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_vif_t    vif;
            rv_vif_t    model_vif;
            rv_config_t cfg;
            demote_id   = "A2C_NO_PAIRS";
            want_errors = waive ? 0 : 1;
            if (!waive) want_text.push_back("agent.model_cmp: the test compared no pair");
            super.build_phase(phase);
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv_model'")
            cfg = rv_config_t::type_id::create("cfg");
            cfg.vif       = vif;
            cfg.model_vif = model_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = A2C_DST;
            cfg.port_name = "rv";
            uvm_config_db#(rv_config_t)::set(this, "agent", "cfg", cfg);
            uvm_config_db#(rv_config_t)::set(this, "peer", "cfg", src_cfg("peer_cfg", vif, "rv"));
            uvm_config_db#(rv_config_t)::set(this, "model_peer", "cfg", src_cfg("model_peer_cfg", model_vif, "rv_model"));
            if (waive) uvm_config_db#(bit)::set(this, "agent.model_cmp", "a2c_allow_no_pairs", 1'b1);
            agent      = rv_agent_t::type_id::create("agent", this);
            peer       = rv_agent_t::type_id::create("peer", this);
            model_peer = rv_agent_t::type_id::create("model_peer", this);
        endfunction

        protected function rv_config_t src_cfg(string name, rv_vif_t lane_vif, string port);
            rv_config_t c = rv_config_t::type_id::create(name);
            c.vif       = lane_vif;
            c.clk_vif   = clk_vif;
            c.role      = A2C_SRC;
            c.port_name = port;
            return c;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            repeat (20) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask
    endclass : lb_no_pairs_test

    class lb_no_pairs_waived_test extends lb_no_pairs_test;
        `uvm_component_utils(lb_no_pairs_waived_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            waive = 1;
        endfunction
    endclass : lb_no_pairs_waived_test
