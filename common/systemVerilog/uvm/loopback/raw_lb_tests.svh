// raw agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef raw_agent #(.data_t(lb_data_t)) raw_agent_t;
    typedef raw_agent_t::item_t raw_item_t;
    typedef raw_agent_t::config_t raw_config_t;
    typedef virtual raw_if #(.data_t(lb_data_t)) raw_vif_t;

    class raw_seq extends uvm_sequence #(raw_item_t);
        int unsigned               n;
        lb_scoreboard#(raw_item_t) sb;

        `uvm_object_utils(raw_seq)

        function new(string name = "raw_seq");
            super.new(name);
        endfunction

        // Every item is expected before the first goes out, so a clock that
        // repeats an item meets the next one in the scoreboard. A non-zero
        // value keeps the first item apart from the idle value.
        virtual task body();
            raw_item_t items[$];
            raw_item_t it;
            repeat (n) begin
                it = raw_item_t::type_id::create("it");
                if (!it.randomize() with { data.value != 0; }) `uvm_fatal("LB_RAND", "raw item randomize failed")
                items.push_back(it);
                sb.expected.push_back(it);
            end
            foreach (items[i]) begin
                start_item(items[i]);
                finish_item(items[i]);
            end
        endtask
    endclass : raw_seq

    // A raw src agent puts one item on data per clock and a passive dst
    // agent reports data every clock. Checks the items arrive on consecutive
    // clocks in order.
    class raw_test extends lb_base_test;
        raw_agent_t                src;
        raw_agent_t                dst;
        lb_scoreboard#(raw_item_t) sb;

        `uvm_component_utils(raw_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            raw_config_t src_cfg;
            raw_config_t dst_cfg;
            raw_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(raw_vif_t)::get(this, "", "raw", vif)) `uvm_fatal("LB_CFG", "no virtual raw_if 'raw'")
            src_cfg = raw_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "raw";
            dst_cfg = raw_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "raw";
            uvm_config_db#(raw_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(raw_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = raw_agent_t::type_id::create("src", this);
            dst = raw_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(raw_item_t)::type_id::create("sb", this);
            sb.free_running = 1;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        virtual task run_phase(uvm_phase phase);
            raw_seq seq = raw_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n  = n_items;
            seq.sb = sb;
            clk_vif.wait_reset_release();
            seq.start(src.sqr);
            wait_matched(sb, n_items, 10);
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d items on consecutive clocks", sb.matched), UVM_NONE)
        endfunction
    endclass : raw_test

    // Mode B. The agent under test has raw as its DUT lane and raw_model as
    // its model lane. As A2C_SRC it puts n_items words on both lanes, one per
    // clock; passive dst peers report each lane, and the two lanes must carry
    // the same word on every clock. As A2C_DST it monitors both lanes against
    // two src peers whose words differ in every tag, and the run must end
    // with no error, because raw is not compared. Neither role builds a
    // comparator.
    class raw_mode_b_test extends lb_mode_b_base;
        a2c_role_e                 role = A2C_SRC;
        raw_agent_t                agent;
        raw_agent_t                peer;
        raw_agent_t                model_peer;
        raw_vif_t                  vif;
        raw_vif_t                  model_vif;
        lb_scoreboard#(raw_item_t) sb;
        lb_scoreboard#(raw_item_t) model_sb;
        raw_item_t                 items[$];
        raw_item_t                 model_items[$];
        int unsigned               differ;

        `uvm_component_utils(raw_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function raw_config_t lane_cfg(string name, raw_vif_t lane_vif, a2c_role_e lane_role, string port);
            raw_config_t cfg = raw_config_t::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = port;
            return cfg;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            raw_config_t agent_cfg;
            a2c_role_e   peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            super.build_phase(phase);
            if (!uvm_config_db#(raw_vif_t)::get(this, "", "raw", vif)) `uvm_fatal("LB_CFG", "no virtual raw_if 'raw'")
            if (!uvm_config_db#(raw_vif_t)::get(this, "", "raw_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual raw_if 'raw_model'")
            // A non-zero value keeps each word apart from the idle value.
            for (int unsigned i = 0; i < n_items; i++) begin
                raw_item_t it = raw_item_t::type_id::create("it");
                raw_item_t m;
                if (!it.randomize() with { data.value != 0; }) `uvm_fatal("LB_RAND", "raw item randomize failed")
                $cast(m, it.clone());
                m.data.tag = ~m.data.tag;
                items.push_back(it);
                model_items.push_back(m);
            end
            agent_cfg = lane_cfg("agent_cfg", vif, role, "raw");
            agent_cfg.model_vif = model_vif;
            uvm_config_db#(raw_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(raw_config_t)::set(this, "peer", "cfg", lane_cfg("peer_cfg", vif, peer_role, "raw"));
            uvm_config_db#(raw_config_t)::set(this, "model_peer", "cfg", lane_cfg("model_peer_cfg", model_vif, peer_role, "raw_model"));
            agent      = raw_agent_t::type_id::create("agent", this);
            peer       = raw_agent_t::type_id::create("peer", this);
            model_peer = raw_agent_t::type_id::create("model_peer", this);
            sb         = lb_scoreboard#(raw_item_t)::type_id::create("sb", this);
            model_sb   = lb_scoreboard#(raw_item_t)::type_id::create("model_sb", this);
            sb.free_running       = 1;
            model_sb.free_running = 1;
            sb.expected = items;
            if (role == A2C_SRC) model_sb.expected = items;
            else model_sb.expected = model_items;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (role == A2C_SRC) begin
                peer.mon.ap.connect(sb.imp);
                model_peer.mon.ap.connect(model_sb.imp);
            end else begin
                agent.mon.ap.connect(sb.imp);
                agent.model_mon.ap.connect(model_sb.imp);
            end
        endfunction

        protected task send(raw_agent_t src, raw_item_t list[$]);
            lb_list_seq#(raw_item_t) seq = lb_list_seq#(raw_item_t)::type_id::create("seq");
            seq.items = list;
            seq.start(src.sqr);
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (vif.data !== model_vif.data) differ++;
                end
            join_none
            if (role == A2C_SRC) begin
                send(agent, items);
            end else begin
                fork
                    send(peer, items);
                    send(model_peer, model_items);
                join
            end
            wait_matched(sb, n_items, 10);
            wait_matched(model_sb, n_items, 10);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d words on the DUT lane and %0d on the model lane; the lanes differed on %0d clocks",
                                            sb.matched, model_sb.matched, differ), UVM_NONE)
            if (agent.model_mon == null) `uvm_error("LB_MODE_B", "the agent built no model_mon")
            if (agent.has_child("model_cmp")) `uvm_error("LB_MODE_B", "the raw agent built a comparator")
            if (role == A2C_SRC && differ != 0) `uvm_error("LB_MODE_B", $sformatf("the lanes carried different words on %0d clocks", differ))
            if (role == A2C_DST && differ == 0) `uvm_error("LB_MODE_B", "the lanes never differed, so nothing tested that raw is not compared")
        endfunction
    endclass : raw_mode_b_test

    class raw_mode_b_dst_test extends raw_mode_b_test;
        `uvm_component_utils(raw_mode_b_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role = A2C_DST;
        endfunction
    endclass : raw_mode_b_dst_test
