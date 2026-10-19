// rdy_vld agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef rdy_vld_agent #(.data_t(lb_data_t)) rv_agent_t;
    typedef rv_agent_t::item_t rv_item_t;
    typedef rv_agent_t::config_t rv_config_t;
    typedef virtual rdy_vld_if #(.data_t(lb_data_t)) rv_vif_t;

    class rv_seq extends uvm_sequence #(rv_item_t);
        int unsigned              n;
        int unsigned              max_gap;
        lb_scoreboard#(rv_item_t) sb;

        `uvm_object_utils(rv_seq)

        function new(string name = "rv_seq");
            super.new(name);
        endfunction

        virtual task body();
            rv_item_t it;
            repeat (n) begin
                it = rv_item_t::type_id::create("it");
                start_item(it);
                if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
                it.gap = $urandom_range(max_gap, 0);
                sb.expected.push_back(it);
                finish_item(it);
            end
        endtask
    endclass : rv_seq

    // A rdy_vld src agent drives a dst agent whose rdy is random, so beats
    // stall. Checks every beat arrives in order and counts stalled clocks and
    // rdy level changes, which tell random ready from burst ready.
    class rdy_vld_random_test extends lb_base_test;
        rv_agent_t                src;
        rv_agent_t                dst;
        lb_scoreboard#(rv_item_t) sb;
        rv_config_t               dst_cfg;
        int unsigned              stalls;
        int unsigned              toggles;
        int unsigned              clocks;

        `uvm_component_utils(rdy_vld_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(rv_config_t cfg);
            cfg.ready_pct = 50;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t src_cfg;
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
            configure_dst(dst_cfg);
            uvm_config_db#(rv_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(rv_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = rv_agent_t::type_id::create("src", this);
            dst = rv_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(rv_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        virtual task run_phase(uvm_phase phase);
            rv_seq seq = rv_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n       = n_items;
            seq.max_gap = 2;
            seq.sb      = sb;
            clk_vif.wait_reset_release();
            fork
                watch_rdy();
            join_none
            seq.start(src.sqr);
            wait_matched(sb, n_items, 100 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        protected task watch_rdy();
            logic last_rdy = dst_cfg.vif.rdy;
            forever begin
                clk_vif.sample_edge();
                clocks++;
                if (dst_cfg.vif.vld === 1'b1 && dst_cfg.vif.rdy !== 1'b1) stalls++;
                if (dst_cfg.vif.rdy !== last_rdy) toggles++;
                last_rdy = dst_cfg.vif.rdy;
            end
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d beats, %0d stalled clocks, rdy changed on %0d of %0d clocks",
                                            sb.matched, stalls, toggles, clocks), UVM_NONE)
            if (stalls == 0) `uvm_error("LB_NO_STALL", "rdy never held a beat back, so back-pressure was not exercised")
            // ready_pct 50 changes rdy on about half the clocks.
            if (toggles * 100 < clocks * 35) `uvm_error("LB_READY_MODE", "rdy changed on under 35% of clocks")
        endfunction
    endclass : rdy_vld_random_test

    class rdy_vld_burst_test extends rdy_vld_random_test;
        `uvm_component_utils(rdy_vld_burst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(rv_config_t cfg);
            cfg.ready_pct = 50;
            cfg.burst     = 1;
            cfg.burst_max = 8;
        endfunction

        // Runs of 1 to 8 clocks, each level drawn afresh, change rdy on about
        // one clock in nine.
        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d beats, %0d stalled clocks, rdy changed on %0d of %0d clocks",
                                            sb.matched, stalls, toggles, clocks), UVM_NONE)
            if (stalls == 0) `uvm_error("LB_NO_STALL", "rdy never held a beat back, so back-pressure was not exercised")
            if (toggles * 100 > clocks * 20) `uvm_error("LB_READY_MODE", "rdy changed on over 20% of clocks, so it did not hold runs")
        endfunction
    endclass : rdy_vld_burst_test

    typedef a2c_txn_counter #(rv_item_t) rv_counter_t;

    // Mode B. The agent under test has rv as its DUT lane and rv_model as
    // its model lane, and each lane has a single-lane peer of the other role.
    // As A2C_SRC the agent sends n_items beats to two dst peers, random ready
    // on rv and burst ready on rv_model. As A2C_DST it gives both lanes one
    // random rdy, against two src peers that send the same beats with
    // different gaps. Each lane must deliver every beat once, in order, and a
    // dual counter on the agent's two monitors must see n_items on each. The
    // lanes' vld must differ on some clocks, and on the A2C_DST role their
    // rdy never. With no_backpressure set, every config declares
    // backpressure: false with ready_pct 0, so a dst driver that does not
    // hold rdy high stalls the run. As A2C_SRC both lanes then transfer
    // every beat on the same clock and their vld must never differ.
    class rdy_vld_mode_b_test extends lb_mode_b_base;
        a2c_role_e                role = A2C_SRC;
        bit                       no_backpressure = 0;
        rv_agent_t                agent;
        rv_agent_t                peer;
        rv_agent_t                model_peer;
        rv_vif_t                  vif;
        rv_vif_t                  model_vif;
        lb_scoreboard#(rv_item_t) sb;
        lb_scoreboard#(rv_item_t) model_sb;
        rv_counter_t              counter;
        rv_item_t                 items[$];
        rv_item_t                 model_items[$];
        int unsigned              vld_skew;
        int unsigned              rdy_skew;

        `uvm_component_utils(rdy_vld_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function rv_config_t lane_cfg(string name, rv_vif_t lane_vif, a2c_role_e lane_role, string port);
            rv_config_t cfg = rv_config_t::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = port;
            return cfg;
        endfunction

        // Edits model_items and the expectations.
        virtual function void build_streams();
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t agent_cfg;
            rv_config_t peer_cfg;
            rv_config_t model_peer_cfg;
            a2c_role_e  peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            super.build_phase(phase);
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv_model'")
            for (int unsigned i = 0; i < n_items; i++) begin
                rv_item_t it = rv_item_t::type_id::create("it");
                rv_item_t m;
                if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
                it.gap = $urandom_range(1, 0);
                $cast(m, it.clone());
                m.gap = $urandom_range(4, 0);
                items.push_back(it);
                model_items.push_back(m);
            end
            build_streams();
            agent_cfg = lane_cfg("agent_cfg", vif, role, "rv");
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lane_cfg("peer_cfg", vif, peer_role, "rv");
            model_peer_cfg = lane_cfg("model_peer_cfg", model_vif, peer_role, "rv_model");
            if (role == A2C_SRC) begin
                peer_cfg.ready_pct       = 50;
                model_peer_cfg.ready_pct = 50;
                model_peer_cfg.burst     = 1;
            end else begin
                agent_cfg.ready_pct = 50;
            end
            if (no_backpressure) begin
                rv_config_t cfgs[3] = '{agent_cfg, peer_cfg, model_peer_cfg};
                foreach (cfgs[i]) begin
                    cfgs[i].no_backpressure = 1;
                    cfgs[i].ready_pct       = 0;
                end
            end
            uvm_config_db#(rv_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(rv_config_t)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(rv_config_t)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent      = rv_agent_t::type_id::create("agent", this);
            peer       = rv_agent_t::type_id::create("peer", this);
            model_peer = rv_agent_t::type_id::create("model_peer", this);
            sb         = lb_scoreboard#(rv_item_t)::type_id::create("sb", this);
            model_sb   = lb_scoreboard#(rv_item_t)::type_id::create("model_sb", this);
            sb.expected = items;
            if (role == A2C_SRC) model_sb.expected = items;
            else model_sb.expected = model_items;
            counter = rv_counter_t::type_id::create("counter", this);
            counter.port_name = "rv";
            counter.dual      = 1;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (role == A2C_SRC) begin
                peer.mon.ap.connect(sb.imp);
                model_peer.mon.ap.connect(model_sb.imp);
            end else begin
                agent.mon.ap.connect(sb.imp);
                agent.model_mon.ap.connect(model_sb.imp);
            end
            agent.mon.ap.connect(counter.analysis_export);
            agent.model_mon.ap.connect(counter.model_export);
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
                forever begin
                    clk_vif.sample_edge();
                    if (vif.vld !== model_vif.vld) vld_skew++;
                    if (vif.rdy !== model_vif.rdy) rdy_skew++;
                end
            join_none
            counter.expect_count(n_items);
            if (role == A2C_SRC) begin
                send(agent, items);
            end else begin
                fork
                    send(peer, items);
                    send(model_peer, model_items);
                join
            end
            counter.wait_for_count(clk_vif, 100 * n_items, 10);
            wait_matched(sb, n_items, 10);
            wait_matched(model_sb, n_items, 10);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d beats on the DUT lane and %0d on the model lane; vld differed on %0d clocks, rdy on %0d",
                                            sb.matched, model_sb.matched, vld_skew, rdy_skew), UVM_NONE)
            if (role == A2C_SRC && no_backpressure) begin
                if (vld_skew != 0) `uvm_error("LB_MODE_B", $sformatf("the lanes' vld differed on %0d clocks with neither lane stalling", vld_skew))
            end else if (vld_skew == 0) begin
                `uvm_error("LB_MODE_B", "the lanes' vld never differed, so per-lane completion went untested")
            end
            if (role == A2C_SRC) begin
                if (agent.has_child("model_cmp")) `uvm_error("LB_MODE_B", "the A2C_SRC agent built a comparator")
            end else begin
                if (rdy_skew != 0) `uvm_error("LB_MODE_B", $sformatf("the lanes' rdy differed on %0d clocks", rdy_skew))
                if (agent.model_cmp == null) `uvm_error("LB_MODE_B", "the A2C_DST agent built no comparator")
                else if (agent.model_cmp.get_pairs() != n_items) begin
                    `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d beats, expected %0d", agent.model_cmp.get_pairs(), n_items))
                end
            end
        endfunction
    endclass : rdy_vld_mode_b_test

    class rdy_vld_mode_b_dst_test extends rdy_vld_mode_b_test;
        `uvm_component_utils(rdy_vld_mode_b_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role = A2C_DST;
        endfunction
    endclass : rdy_vld_mode_b_dst_test

    class rdy_vld_mode_b_no_bp_test extends rdy_vld_mode_b_test;
        `uvm_component_utils(rdy_vld_mode_b_no_bp_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            no_backpressure = 1;
        endfunction
    endclass : rdy_vld_mode_b_no_bp_test

    class rdy_vld_mode_b_no_bp_dst_test extends rdy_vld_mode_b_dst_test;
        `uvm_component_utils(rdy_vld_mode_b_no_bp_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            no_backpressure = 1;
        endfunction
    endclass : rdy_vld_mode_b_no_bp_dst_test

    // The model lane's peer sends one beat with different data: one
    // A2C_MODEL_CMP naming the pair, with both beats printed.
    class rdy_vld_mode_b_mismatch_test extends rdy_vld_mode_b_dst_test;
        `uvm_component_utils(rdy_vld_mode_b_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            int unsigned k = $urandom_range(n_items - 1, 0);
            model_items[k].data.value = ~model_items[k].data.value;
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT %s, model %s", k + 1,
                                          items[k].convert2string(), model_items[k].convert2string()));
        endfunction
    endclass : rdy_vld_mode_b_mismatch_test
