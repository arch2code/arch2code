// axi4_stream agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    // Four bytes, so tstrb and tkeep are four bits wide.
    typedef struct packed {
        logic [7:0] b3;
        logic [7:0] b2;
        logic [7:0] b1;
        logic [7:0] b0;
    } lb_tdata_t;
    typedef logic [3:0] lb_tid_t;
    typedef logic [2:0] lb_tdest_t;
    typedef logic [1:0] lb_tuser_t;

    typedef axi4_stream_agent #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis_agent_t;
    typedef axis_agent_t::item_t axis_item_t;
    typedef axis_agent_t::config_t axis_config_t;
    typedef virtual axi4_stream_if #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis_vif_t;

    class axis_seq extends uvm_sequence #(axis_item_t);
        int unsigned                n;
        lb_scoreboard#(axis_item_t) sb;

        `uvm_object_utils(axis_seq)

        function new(string name = "axis_seq");
            super.new(name);
        endfunction

        // Every fourth item sets tstrb and tkeep; the rest keep the all-ones
        // default.
        virtual task body();
            axis_item_t it;
            for (int unsigned i = 0; i < n; i++) begin
                it = axis_item_t::type_id::create("it");
                start_item(it);
                if (!it.randomize()) `uvm_fatal("LB_RAND", "axi4_stream item randomize failed")
                if (i % 4 == 3) begin
                    it.tstrb = $urandom();
                    it.tkeep = $urandom();
                end
                it.gap = $urandom_range(2, 0);
                sb.expected.push_back(it);
                finish_item(it);
            end
        endtask
    endclass : axis_seq

    // An axi4_stream src agent drives a dst agent whose tready is random.
    // Checks every field of every beat, and that tstrb and tkeep are all ones
    // on beats that do not set them.
    class axi4_stream_test extends lb_base_test;
        axis_agent_t                src;
        axis_agent_t                dst;
        lb_scoreboard#(axis_item_t) sb;
        axis_config_t               dst_cfg;
        int unsigned                stalls;
        int unsigned                all_ones;

        `uvm_component_utils(axi4_stream_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            axis_config_t src_cfg;
            axis_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis", vif)) `uvm_fatal("LB_CFG", "no virtual axi4_stream_if 'axis'")
            src_cfg = axis_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "axis";
            dst_cfg = axis_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "axis";
            dst_cfg.ready_pct = 50;
            uvm_config_db#(axis_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(axis_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = axis_agent_t::type_id::create("src", this);
            dst = axis_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(axis_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        virtual task run_phase(uvm_phase phase);
            axis_seq seq = axis_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n  = n_items;
            seq.sb = sb;
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (dst_cfg.vif.tvalid === 1'b1 && dst_cfg.vif.tready !== 1'b1) stalls++;
                    if (dst_cfg.vif.tvalid === 1'b1 && dst_cfg.vif.tready === 1'b1
                        && &dst_cfg.vif.tstrb === 1'b1 && &dst_cfg.vif.tkeep === 1'b1) all_ones++;
                end
            join_none
            seq.start(src.sqr);
            wait_matched(sb, n_items, 100 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d beats, %0d stalled clocks, %0d beats with all-ones tstrb and tkeep",
                                            sb.matched, stalls, all_ones), UVM_NONE)
            if (stalls == 0) `uvm_error("LB_NO_STALL", "tready never held a beat back, so back-pressure was not exercised")
            if (all_ones < n_items / 2) `uvm_error("LB_STRB", "under half the beats carried all-ones tstrb and tkeep")
        endfunction
    endclass : axi4_stream_test

    typedef a2c_txn_counter #(axis_item_t) axis_counter_t;

    // Mode B. The agent under test has axis as its DUT lane and axis_model
    // as its model lane, and each lane has a single-lane peer of the other
    // role. As A2C_SRC the agent sends n_items beats to two dst peers, tready
    // 50% on axis and 80% on axis_model. As A2C_DST it gives both lanes one
    // random tready, against two src peers that send the same beats with
    // different gaps. Each lane must deliver every beat once, in order, and a
    // dual counter on the agent's two monitors must see n_items on each. The
    // lanes' tvalid must differ on some clocks, and on the A2C_DST role their
    // tready never.
    class axi4_stream_mode_b_test extends lb_mode_b_base;
        a2c_role_e                  role = A2C_SRC;
        axis_agent_t                agent;
        axis_agent_t                peer;
        axis_agent_t                model_peer;
        axis_vif_t                  vif;
        axis_vif_t                  model_vif;
        lb_scoreboard#(axis_item_t) sb;
        lb_scoreboard#(axis_item_t) model_sb;
        axis_counter_t              counter;
        axis_item_t                 items[$];
        axis_item_t                 model_items[$];
        int unsigned                valid_skew;
        int unsigned                ready_skew;

        `uvm_component_utils(axi4_stream_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function axis_config_t lane_cfg(string name, axis_vif_t lane_vif, a2c_role_e lane_role, string port);
            axis_config_t cfg = axis_config_t::type_id::create(name);
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
            axis_config_t agent_cfg;
            axis_config_t peer_cfg;
            axis_config_t model_peer_cfg;
            a2c_role_e    peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            super.build_phase(phase);
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis", vif)) `uvm_fatal("LB_CFG", "no virtual axi4_stream_if 'axis'")
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis_model", model_vif)) begin
                `uvm_fatal("LB_CFG", "no virtual axi4_stream_if 'axis_model'")
            end
            for (int unsigned i = 0; i < n_items; i++) begin
                axis_item_t it = axis_item_t::type_id::create("it");
                axis_item_t m;
                if (!it.randomize()) `uvm_fatal("LB_RAND", "axi4_stream item randomize failed")
                if (i % 4 == 3) begin
                    it.tstrb = $urandom();
                    it.tkeep = $urandom();
                end
                it.gap = $urandom_range(1, 0);
                $cast(m, it.clone());
                m.gap = $urandom_range(4, 0);
                items.push_back(it);
                model_items.push_back(m);
            end
            build_streams();
            agent_cfg = lane_cfg("agent_cfg", vif, role, "axis");
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lane_cfg("peer_cfg", vif, peer_role, "axis");
            model_peer_cfg = lane_cfg("model_peer_cfg", model_vif, peer_role, "axis_model");
            if (role == A2C_SRC) begin
                peer_cfg.ready_pct       = 50;
                model_peer_cfg.ready_pct = 80;
            end else begin
                agent_cfg.ready_pct = 50;
            end
            uvm_config_db#(axis_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(axis_config_t)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(axis_config_t)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent      = axis_agent_t::type_id::create("agent", this);
            peer       = axis_agent_t::type_id::create("peer", this);
            model_peer = axis_agent_t::type_id::create("model_peer", this);
            sb         = lb_scoreboard#(axis_item_t)::type_id::create("sb", this);
            model_sb   = lb_scoreboard#(axis_item_t)::type_id::create("model_sb", this);
            sb.expected = items;
            if (role == A2C_SRC) model_sb.expected = items;
            else model_sb.expected = model_items;
            counter = axis_counter_t::type_id::create("counter", this);
            counter.port_name = "axis";
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

        protected task send(axis_agent_t src, axis_item_t list[$]);
            lb_list_seq#(axis_item_t) seq = lb_list_seq#(axis_item_t)::type_id::create("seq");
            seq.items = list;
            seq.start(src.sqr);
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (vif.tvalid !== model_vif.tvalid) valid_skew++;
                    if (vif.tready !== model_vif.tready) ready_skew++;
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
            `uvm_info("LB_STATS", $sformatf("%0d beats on the DUT lane and %0d on the model lane; tvalid differed on %0d clocks, tready on %0d",
                                            sb.matched, model_sb.matched, valid_skew, ready_skew), UVM_NONE)
            if (valid_skew == 0) `uvm_error("LB_MODE_B", "the lanes' tvalid never differed, so per-lane completion went untested")
            if (role == A2C_SRC) begin
                if (agent.has_child("model_cmp")) `uvm_error("LB_MODE_B", "the A2C_SRC agent built a comparator")
            end else begin
                if (ready_skew != 0) `uvm_error("LB_MODE_B", $sformatf("the lanes' tready differed on %0d clocks", ready_skew))
                if (agent.model_cmp == null) `uvm_error("LB_MODE_B", "the A2C_DST agent built no comparator")
                else if (agent.model_cmp.get_pairs() != n_items) begin
                    `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d beats, expected %0d", agent.model_cmp.get_pairs(), n_items))
                end
            end
        endfunction
    endclass : axi4_stream_mode_b_test

    class axi4_stream_mode_b_dst_test extends axi4_stream_mode_b_test;
        `uvm_component_utils(axi4_stream_mode_b_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role = A2C_DST;
        endfunction
    endclass : axi4_stream_mode_b_dst_test

    // The model lane's peer sends one beat with a different tdest: one
    // A2C_MODEL_CMP naming the pair, with both beats printed.
    class axi4_stream_mode_b_mismatch_test extends axi4_stream_mode_b_dst_test;
        `uvm_component_utils(axi4_stream_mode_b_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            int unsigned k = $urandom_range(n_items - 1, 0);
            model_items[k].tdest = ~model_items[k].tdest;
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT %s, model %s", k + 1,
                                          items[k].convert2string(), model_items[k].convert2string()));
        endfunction
    endclass : axi4_stream_mode_b_mismatch_test
