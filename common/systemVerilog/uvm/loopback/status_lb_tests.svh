// status agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef status_agent #(.data_t(lb_data_t)) st_agent_t;
    typedef st_agent_t::item_t st_item_t;
    typedef st_agent_t::config_t st_config_t;
    typedef virtual status_if #(.data_t(lb_data_t)) st_vif_t;

    // A status src agent holds data at its config value and a passive dst
    // agent reports each change. The test changes the value every few clocks
    // and checks every value is reported once, in order.
    class status_test extends lb_base_test;
        st_agent_t                src;
        st_agent_t                dst;
        lb_scoreboard#(st_item_t) sb;
        st_config_t               src_cfg;

        `uvm_component_utils(status_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            st_config_t dst_cfg;
            st_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(st_vif_t)::get(this, "", "st", vif)) `uvm_fatal("LB_CFG", "no virtual status_if 'st'")
            src_cfg = st_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "st";
            src_cfg.value     = lb_data_t'($urandom());
            dst_cfg = st_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "st";
            uvm_config_db#(st_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(st_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = st_agent_t::type_id::create("src", this);
            dst = st_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(st_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        function void expect_value(lb_data_t value);
            st_item_t it = st_item_t::type_id::create("it");
            it.data = value;
            sb.expected.push_back(it);
        endfunction

        // The value driven through reset is the first one reported.
        virtual task run_phase(uvm_phase phase);
            lb_data_t next;
            int unsigned changes = n_items / 8;
            phase.raise_objection(this);
            expect_value(src_cfg.value);
            clk_vif.wait_reset_release();
            repeat (changes) begin
                repeat ($urandom_range(5, 2)) clk_vif.sample_edge();
                do next = lb_data_t'($urandom()); while (next === src_cfg.value);
                expect_value(next);
                src_cfg.value = next;
            end
            wait_matched(sb, changes + 1, 10);
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d values reported", sb.matched), UVM_NONE)
        endfunction
    endclass : status_test

    // Mode B. The agent under test has st as its DUT lane and st_model as
    // its model lane.
    //
    // As A2C_SRC the agent holds one level on both lanes and the test
    // changes it as status_test does. Passive dst peers must each report
    // every value once, in order, and the lanes must carry the same value on
    // every clock.
    //
    // As A2C_DST, src peers on the two lanes move through the same
    // n_items / 8 values. Per value, one peer moves first and the other one
    // to five clocks later, and on every other value the model lane's peer
    // passes through an intermediate value first. Once both lanes have
    // settled the test calls model_cmp.stable_point(). Under the default
    // stable policy each call pairs the two latest values, and every pair
    // must match: one after reset and one per value.
    class status_mode_b_test extends lb_mode_b_base;
        a2c_role_e                role = A2C_SRC;
        st_agent_t                agent;
        st_agent_t                peer;
        st_agent_t                model_peer;
        st_config_t               agent_cfg;
        st_config_t               peer_cfg;
        st_config_t               model_peer_cfg;
        st_vif_t                  vif;
        st_vif_t                  model_vif;
        lb_scoreboard#(st_item_t) sb;
        lb_scoreboard#(st_item_t) model_sb;
        int unsigned              changes;
        int unsigned              differ;
        // A2C_DST: the stable point after value mismatch_at, counting from
        // 1, finds the model lane on a different value; 0 for none.
        int unsigned              mismatch_at;

        `uvm_component_utils(status_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function st_config_t lane_cfg(string name, st_vif_t lane_vif, a2c_role_e lane_role, string port);
            st_config_t cfg = st_config_t::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = port;
            return cfg;
        endfunction

        // A value of the sequence the peers move through.
        virtual function lb_data_t next_value();
            return lb_data_t'($urandom());
        endfunction

        // The value the model lane's peer passes through before v.
        virtual function lb_data_t intermediate(lb_data_t v);
            v.value = ~v.value;
            return v;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_role_e peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            super.build_phase(phase);
            if (!uvm_config_db#(st_vif_t)::get(this, "", "st", vif)) `uvm_fatal("LB_CFG", "no virtual status_if 'st'")
            if (!uvm_config_db#(st_vif_t)::get(this, "", "st_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual status_if 'st_model'")
            changes = n_items / 8;
            agent_cfg = lane_cfg("agent_cfg", vif, role, "st");
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lane_cfg("peer_cfg", vif, peer_role, "st");
            model_peer_cfg = lane_cfg("model_peer_cfg", model_vif, peer_role, "st_model");
            if (role == A2C_SRC) begin
                agent_cfg.value = next_value();
            end else begin
                peer_cfg.value       = next_value();
                model_peer_cfg.value = peer_cfg.value;
            end
            uvm_config_db#(st_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(st_config_t)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(st_config_t)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent      = st_agent_t::type_id::create("agent", this);
            peer       = st_agent_t::type_id::create("peer", this);
            model_peer = st_agent_t::type_id::create("model_peer", this);
            sb         = lb_scoreboard#(st_item_t)::type_id::create("sb", this);
            model_sb   = lb_scoreboard#(st_item_t)::type_id::create("model_sb", this);
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

        function void expect_value(lb_scoreboard#(st_item_t) to, lb_data_t value);
            st_item_t it = st_item_t::type_id::create("it");
            it.data = value;
            to.expected.push_back(it);
        endfunction

        protected task run_src();
            lb_data_t next;
            expect_value(sb, agent_cfg.value);
            expect_value(model_sb, agent_cfg.value);
            repeat (changes) begin
                repeat ($urandom_range(5, 2)) clk_vif.sample_edge();
                do next = next_value(); while (next === agent_cfg.value);
                expect_value(sb, next);
                expect_value(model_sb, next);
                agent_cfg.value = next;
            end
        endtask

        // Moves one peer's value, and its scoreboard's expectation with it.
        protected function void move(st_config_t cfg, lb_scoreboard#(st_item_t) to, lb_data_t value);
            if (value === cfg.value) return;
            expect_value(to, value);
            cfg.value = value;
        endfunction

        protected task run_dst();
            lb_data_t v;
            lb_data_t model_v;
            expect_value(sb, peer_cfg.value);
            expect_value(model_sb, model_peer_cfg.value);
            repeat (3) clk_vif.sample_edge();
            agent.model_cmp.stable_point();
            for (int unsigned i = 1; i <= changes; i++) begin
                bit model_first = $urandom_range(1, 0);
                do v = next_value(); while (v === peer_cfg.value || v === model_peer_cfg.value);
                model_v = v;
                if (i == mismatch_at) model_v.value = ~model_v.value;
                if (model_first) move(model_peer_cfg, model_sb, model_v);
                else move(peer_cfg, sb, v);
                repeat ($urandom_range(5, 1)) clk_vif.sample_edge();
                if (i % 2 == 0) begin
                    move(model_peer_cfg, model_sb, intermediate(model_v));
                    repeat (2) clk_vif.sample_edge();
                end
                move(model_peer_cfg, model_sb, model_v);
                move(peer_cfg, sb, v);
                repeat (3) clk_vif.sample_edge();
                agent.model_cmp.stable_point();
            end
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
            if (role == A2C_SRC) run_src();
            else run_dst();
            wait_matched(sb, sb.matched + sb.expected.size(), 10);
            wait_matched(model_sb, model_sb.matched + model_sb.expected.size(), 10);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d values on the DUT lane and %0d on the model lane; the lanes differed on %0d clocks",
                                            sb.matched, model_sb.matched, differ), UVM_NONE)
            if (role == A2C_SRC) begin
                if (differ != 0) `uvm_error("LB_MODE_B", $sformatf("the lanes carried different values on %0d clocks", differ))
                if (agent.has_child("model_cmp")) `uvm_error("LB_MODE_B", "the A2C_SRC agent built a comparator")
                return;
            end
            if (differ == 0) `uvm_error("LB_MODE_B", "the lanes never differed, so the stable policy saw no intermediate value")
            check_pairs();
        endfunction

        virtual function void check_pairs();
            if (agent.model_cmp.get_pairs() != changes + 1) begin
                `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d values, expected %0d", agent.model_cmp.get_pairs(), changes + 1))
            end
        endfunction
    endclass : status_mode_b_test

    class status_mode_b_dst_test extends status_mode_b_test;
        `uvm_component_utils(status_mode_b_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role = A2C_DST;
        endfunction
    endclass : status_mode_b_dst_test

    // The model lane settles on a different value once: one A2C_MODEL_CMP
    // from that stable point.
    class status_mode_b_mismatch_test extends status_mode_b_dst_test;
        `uvm_component_utils(status_mode_b_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            mismatch_at = $urandom_range(changes, 1);
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT ", mismatch_at + 1));
        endfunction
    endclass : status_mode_b_mismatch_test

    // The bounds policy on the agent's own comparator, with no subclass.
    // Every value lies within lo..hi but one intermediate value of the model
    // lane: one A2C_MODEL_CMP naming the model lane.
    class status_mode_b_bounds_test extends status_mode_b_dst_test;
        localparam bit [63:0] LO = 64'h50_0000;
        localparam bit [63:0] HI = 64'h5f_ffff;
        int unsigned          outside_at;
        int unsigned          moves;

        `uvm_component_utils(status_mode_b_bounds_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_data_t next_value();
            lb_data_t v = lb_data_t'($urandom());
            v.tag = 4'h5;
            return v;
        endfunction

        virtual function lb_data_t intermediate(lb_data_t v);
            v.value = ~v.value;
            if (++moves == outside_at) begin
                v.tag = 4'ha;
                want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: model value %p is outside 0x%0h..0x%0h", v, LO, HI));
            end
            return v;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            outside_at  = $urandom_range(changes / 2, 1);
            want_errors = 1;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.policy = A2C_STATUS_BOUNDS;
            agent.model_cmp.lo     = LO;
            agent.model_cmp.hi     = HI;
        endfunction

        virtual function void check_pairs();
            if (want_text.size() != 1) `uvm_error("LB_MODE_B", "the out-of-range value was never driven")
        endfunction
    endclass : status_mode_b_bounds_test

    // The bounds policy with every two-state value within lo..hi, and lo
    // above 0. One intermediate value of the model lane is all X, which
    // value() would read as 0, outside the bounds: one A2C_XZ naming the
    // model lane and no A2C_MODEL_CMP.
    class status_mode_b_bounds_xz_test extends status_mode_b_dst_test;
        localparam bit [63:0] LO = 64'h50_0000;
        localparam bit [63:0] HI = 64'h5f_ffff;
        int unsigned          x_at;
        int unsigned          moves;

        `uvm_component_utils(status_mode_b_bounds_xz_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_XZ";
        endfunction

        virtual function lb_data_t next_value();
            lb_data_t v = lb_data_t'($urandom());
            v.tag = 4'h5;
            return v;
        endfunction

        virtual function lb_data_t intermediate(lb_data_t v);
            v.value = ~v.value;
            if (++moves == x_at) begin
                v = 'x;
                want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: model value %p has X or Z", v));
            end
            return v;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            x_at        = $urandom_range(changes / 2, 1);
            want_errors = 1;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.policy = A2C_STATUS_BOUNDS;
            agent.model_cmp.lo     = LO;
            agent.model_cmp.hi     = HI;
        endfunction

        virtual function void check_pairs();
            if (want_text.size() != 1) `uvm_error("LB_MODE_B", "the X value was never driven")
        endfunction
    endclass : status_mode_b_bounds_xz_test
