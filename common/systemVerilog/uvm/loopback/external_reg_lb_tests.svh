// external_reg agent loopback tests, included in a2c_uvm_loopback_pkg after
// the scoreboard and the base test.

    typedef external_reg_agent #(.data_t(lb_data_t)) er_agent_t;
    typedef er_agent_t::item_t er_item_t;
    typedef er_agent_t::config_t er_config_t;
    typedef virtual external_reg_if #(.data_t(lb_data_t)) er_vif_t;

    // Sends each item of items as it is.
    class er_seq extends uvm_sequence #(er_item_t);
        er_item_t items[$];

        `uvm_object_utils(er_seq)

        function new(string name = "er_seq");
            super.new(name);
        endfunction

        virtual task body();
            foreach (items[i]) begin
                start_item(items[i]);
                finish_item(items[i]);
            end
        endtask
    endclass : er_seq

    // A src agent and a dst agent on er. The dst agent's monitor feeds sb with
    // its writes and level_sb with its rdata levels.
    virtual class er_pair_test extends lb_base_test;
        er_agent_t                src;
        er_agent_t                dst;
        er_config_t               dst_cfg;
        lb_scoreboard#(er_item_t) sb;
        lb_scoreboard#(er_item_t) level_sb;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(er_config_t cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            er_config_t src_cfg;
            er_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(er_vif_t)::get(this, "", "er", vif)) `uvm_fatal("LB_CFG", "no virtual external_reg_if 'er'")
            src_cfg = er_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "er";
            dst_cfg = er_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "er";
            configure_dst(dst_cfg);
            uvm_config_db#(er_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(er_config_t)::set(this, "dst", "cfg", dst_cfg);
            src      = er_agent_t::type_id::create("src", this);
            dst      = er_agent_t::type_id::create("dst", this);
            sb       = lb_scoreboard#(er_item_t)::type_id::create("sb", this);
            level_sb = lb_scoreboard#(er_item_t)::type_id::create("level_sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
            dst.mon.rdata_ap.connect(level_sb.imp);
        endfunction

        function er_item_t write_item(bit [1:0] write, lb_data_t wdata, int unsigned gap);
            er_item_t it = er_item_t::type_id::create("it");
            it.write = write;
            it.wdata = wdata;
            it.gap   = gap;
            return it;
        endfunction

        function void expect_level(lb_data_t value);
            er_item_t it = er_item_t::type_id::create("level");
            it.write = '0;
            it.rdata = value;
            level_sb.expected.push_back(it);
        endfunction
    endclass : er_pair_test

    // n_items writes with strobes 1, 2 and 3 and gaps of 0 to 2 clocks, so
    // some go out back to back. The dst agent loads each one, so after the
    // reset value 0 the rdata levels the monitor reports are the written
    // words in order, and each must be on rdata at the sample one clock
    // after its write.
    class external_reg_strobe_test extends er_pair_test;
        int unsigned one_clock;

        `uvm_component_utils(external_reg_strobe_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected task watch_one_clock(er_vif_t vif);
            bit       pending;
            lb_data_t want;
            forever begin
                clk_vif.sample_edge();
                if (pending) begin
                    if (vif.rdata === want) begin
                        one_clock++;
                    end else begin
                        `uvm_error("LB_ER", $sformatf("rdata is 0x%0h one clock after the write of 0x%0h", vif.rdata, want))
                    end
                end
                pending = vif.write !== '0;
                want    = vif.wdata;
            end
        endtask

        virtual task run_phase(uvm_phase phase);
            er_seq       seq = er_seq::type_id::create("seq");
            lb_data_t    level = '0;
            int unsigned back_to_back;
            phase.raise_objection(this);
            expect_level('0);
            for (int unsigned i = 0; i < n_items; i++) begin
                lb_data_t    wdata = lb_data_t'($urandom());
                int unsigned gap = $urandom_range(2, 0);
                if (wdata == level) wdata = ~wdata;
                if (gap == 0) back_to_back++;
                seq.items.push_back(write_item(2'($urandom_range(3, 1)), wdata, gap));
                sb.expected.push_back(seq.items[i]);
                expect_level(wdata);
                level = wdata;
            end
            clk_vif.wait_reset_release();
            fork
                watch_one_clock(src.cfg.vif);
            join_none
            seq.start(src.sqr);
            wait_matched(sb, n_items, 4 * n_items);
            wait_matched(level_sb, n_items + 1, 10);
            // The last level and the watcher's check share a sample edge.
            clk_vif.drive_edge();
            disable fork;
            if (one_clock != n_items) begin
                `uvm_error("LB_ER", $sformatf("%0d writes, %0d on rdata one clock later", n_items, one_clock))
            end
            `uvm_info("LB_STATS", $sformatf("%0d writes, %0d back to back, %0d rdata levels, %0d one clock after their write",
                                            sb.matched, back_to_back, level_sb.matched, one_clock), UVM_NONE)
            phase.drop_objection(this);
        endtask
    endclass : external_reg_strobe_test

    // The dst agent holds rdata at cfg.value with update_on_write off. The
    // test sets four values, with a write between each, and rdata must take
    // each value and nothing the writes carried.
    class external_reg_level_test extends er_pair_test;
        `uvm_component_utils(external_reg_level_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(er_config_t cfg);
            cfg.update_on_write = 0;
            cfg.value           = lb_data_t'(24'h11_2233);
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_data_t values[4] = '{lb_data_t'(24'h44_5566), lb_data_t'(24'h77_8899), lb_data_t'(24'h0), lb_data_t'(24'hAA_BBCC)};
            phase.raise_objection(this);
            expect_level(dst_cfg.value);
            foreach (values[i]) expect_level(values[i]);
            clk_vif.wait_reset_release();
            foreach (values[i]) begin
                er_seq seq = er_seq::type_id::create("seq");
                seq.items.push_back(write_item(2'b01, ~values[i], 0));
                sb.expected.push_back(seq.items[0]);
                seq.start(src.sqr);
                repeat (3) clk_vif.drive_edge();
                dst_cfg.value = values[i];
                repeat (3) clk_vif.drive_edge();
            end
            wait_matched(sb, 4, 10);
            wait_matched(level_sb, 5, 10);
            `uvm_info("LB_STATS", $sformatf("%0d writes, %0d rdata levels", sb.matched, level_sb.matched), UVM_NONE)
            phase.drop_objection(this);
        endtask
    endclass : external_reg_level_test

    // Mode B on er and er_model. agent has er as its DUT lane and er_model as
    // its model lane; each lane has a single-lane peer of the other role,
    // and every dst loads its writes.
    //
    // As A2C_SRC the agent sends n_writes writes, each followed by four quiet
    // clocks and a call to model_cmp.stable_point(), which pairs the two
    // lanes' latest rdata levels: one pair after reset and one per write,
    // all matching.
    //
    // As A2C_DST both peers send the same writes, each lane with its own
    // gaps. model_cmp must pair every write, and each lane's rdata must take
    // its own lane's words in order. After the writes the test sets
    // cfg.value once, and both lanes must take that level.
    class external_reg_mode_b_test extends lb_mode_b_base;
        a2c_role_e                role = A2C_SRC;
        int unsigned              n_writes = 40;
        int unsigned              mismatch_at;
        er_agent_t                agent;
        er_agent_t                peer;
        er_agent_t                model_peer;
        er_config_t               agent_cfg;
        er_config_t               peer_cfg;
        er_config_t               model_peer_cfg;
        er_seq                    seq;
        er_seq                    model_seq;
        lb_scoreboard#(er_item_t) level_sb;
        lb_scoreboard#(er_item_t) model_level_sb;
        lb_data_t                 last_value = lb_data_t'(24'h12_3456);

        `uvm_component_utils(external_reg_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected function er_config_t lane_cfg(string name, er_vif_t lane_vif, a2c_role_e lane_role, string port);
            er_config_t cfg = er_config_t::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = port;
            return cfg;
        endfunction

        protected function er_item_t write_item(lb_data_t wdata, int unsigned gap);
            er_item_t it = er_item_t::type_id::create("it");
            it.write = 2'($urandom_range(3, 1));
            it.wdata = wdata;
            it.gap   = gap;
            return it;
        endfunction

        protected function void expect_level(lb_scoreboard#(er_item_t) sb, lb_data_t value);
            er_item_t it = er_item_t::type_id::create("level");
            it.write = '0;
            it.rdata = value;
            sb.expected.push_back(it);
        endfunction

        // Edits the model lane's writes.
        virtual function void build_streams();
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_role_e peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            er_vif_t   vif;
            er_vif_t   model_vif;
            lb_data_t  level = '0;
            super.build_phase(phase);
            if (!uvm_config_db#(er_vif_t)::get(this, "", "er", vif)) `uvm_fatal("LB_CFG", "no virtual external_reg_if 'er'")
            if (!uvm_config_db#(er_vif_t)::get(this, "", "er_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual external_reg_if 'er_model'")
            agent_cfg = lane_cfg("agent_cfg", vif, role, "er");
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lane_cfg("peer_cfg", vif, peer_role, "er");
            model_peer_cfg = lane_cfg("model_peer_cfg", model_vif, peer_role, "er_model");
            seq       = er_seq::type_id::create("seq");
            model_seq = er_seq::type_id::create("model_seq");
            for (int unsigned i = 0; i < n_writes; i++) begin
                lb_data_t wdata = lb_data_t'($urandom());
                er_item_t m;
                if (wdata == level) wdata = ~wdata;
                level = wdata;
                seq.items.push_back(write_item(wdata, $urandom_range(2, 0)));
                $cast(m, seq.items[i].clone());
                if (role == A2C_DST) m.gap = $urandom_range(2, 0);
                model_seq.items.push_back(m);
            end
            if (level == last_value) last_value = ~last_value;
            build_streams();
            uvm_config_db#(er_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(er_config_t)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(er_config_t)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent          = er_agent_t::type_id::create("agent", this);
            peer           = er_agent_t::type_id::create("peer", this);
            model_peer     = er_agent_t::type_id::create("model_peer", this);
            level_sb       = lb_scoreboard#(er_item_t)::type_id::create("level_sb", this);
            model_level_sb = lb_scoreboard#(er_item_t)::type_id::create("model_level_sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (role == A2C_SRC) return;
            agent.mon.rdata_ap.connect(level_sb.imp);
            agent.model_mon.rdata_ap.connect(model_level_sb.imp);
        endfunction

        protected function a2c_status_comparator#(er_item_t) rdata_cmp();
            void'($cast(rdata_cmp, agent.model_cmp));
        endfunction

        protected task run_src();
            a2c_status_comparator#(er_item_t) cmp = rdata_cmp();
            er_seq one = er_seq::type_id::create("one");
            repeat (4) clk_vif.sample_edge();
            cmp.stable_point();
            foreach (seq.items[i]) begin
                one.items.delete();
                one.items.push_back(seq.items[i]);
                one.start(agent.sqr);
                repeat (4) clk_vif.sample_edge();
                if (i + 1 == mismatch_at) begin
                    model_peer_cfg.value = ~model_peer_cfg.value;
                    repeat (2) clk_vif.sample_edge();
                end
                cmp.stable_point();
            end
        endtask

        protected virtual task run_dst();
            foreach (seq.items[i]) begin
                expect_level(level_sb, seq.items[i].wdata);
                expect_level(model_level_sb, model_seq.items[i].wdata);
            end
            expect_level(level_sb, last_value);
            expect_level(model_level_sb, last_value);
            fork
                seq.start(peer.sqr);
                model_seq.start(model_peer.sqr);
            join
            repeat (4) clk_vif.sample_edge();
            agent_cfg.value = last_value;
            wait_matched(level_sb, n_writes + 2, 10);
            wait_matched(model_level_sb, n_writes + 2, 10);
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            if (role == A2C_DST) begin
                // The reset level 0 on both lanes.
                expect_level(level_sb, '0);
                expect_level(model_level_sb, '0);
            end
            clk_vif.wait_reset_release();
            if (role == A2C_SRC) run_src();
            else run_dst();
            repeat (2) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            int unsigned want = (role == A2C_SRC) ? n_writes + 1 : n_writes;
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d writes; model_cmp paired %0d; %0d and %0d rdata levels on the DUT and model lanes",
                                            n_writes, agent.model_cmp.get_pairs(), level_sb.matched, model_level_sb.matched), UVM_NONE)
            if (agent.model_cmp.get_pairs() != want) begin
                `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d, expected %0d", agent.model_cmp.get_pairs(), want))
            end
        endfunction
    endclass : external_reg_mode_b_test

    // The model lane's register changes once after a write, so the next
    // stable point pairs different levels: one A2C_MODEL_CMP.
    class external_reg_mode_b_mismatch_test extends external_reg_mode_b_test;
        `uvm_component_utils(external_reg_mode_b_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            mismatch_at = $urandom_range(n_writes, 1);
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT ", mismatch_at + 1));
        endfunction
    endclass : external_reg_mode_b_mismatch_test

    class external_reg_mode_b_dst_test extends external_reg_mode_b_test;
        `uvm_component_utils(external_reg_mode_b_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role = A2C_DST;
        endfunction
    endclass : external_reg_mode_b_dst_test

    // The model lane's peer sends different data in one write: one
    // A2C_MODEL_CMP, and the model lane's rdata takes that data where the
    // DUT lane's takes its own.
    class external_reg_mode_b_dst_mismatch_test extends external_reg_mode_b_dst_test;
        `uvm_component_utils(external_reg_mode_b_dst_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            int unsigned k = $urandom_range(n_writes - 2, 1);
            lb_data_t    w = ~model_seq.items[k].wdata;
            // The corrupt word must still change the model lane's level on
            // both sides of it.
            while (w == model_seq.items[k - 1].wdata || w == model_seq.items[k + 1].wdata) w++;
            model_seq.items[k].wdata = w;
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT ", k + 1));
        endfunction
    endclass : external_reg_mode_b_dst_mismatch_test

    // As external_reg_mode_b_dst_test, with the model lane's last write 60
    // clocks late and the drop as soon as the DUT lane's peer is done, with
    // no wait for the model lane. The drain must hold the run phase until
    // the model lane has made that write: every write paired, each lane's
    // levels as sent, and no error.
    class external_reg_mode_b_dst_drain_test extends external_reg_mode_b_dst_test;
        int unsigned pending_at_drop;

        `uvm_component_utils(external_reg_mode_b_dst_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            model_seq.items[n_writes - 1].gap = 60;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.drv.replay.drain_quiet_cycles    = 20;
            agent.drv.replay.drain_deadline_cycles = 400;
        endfunction

        protected virtual task run_dst();
            foreach (seq.items[i]) begin
                expect_level(level_sb, seq.items[i].wdata);
                expect_level(model_level_sb, model_seq.items[i].wdata);
            end
            fork
                model_seq.start(model_peer.sqr);
            join_none
            seq.start(peer.sqr);
            pending_at_drop = agent.drv.replay.pending();
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (pending_at_drop == 0) `uvm_error("LB_MODE_B", "the model lane had made every write at the drop, so the drain went untested")
        endfunction
    endclass : external_reg_mode_b_dst_drain_test

    // Both peers keep writing after the DUT lane has made n_writes writes
    // and the test drops, with idle clocks repeating 0 to 2 and the model
    // lane three clocks behind, so the DUT lane writes past the cut while
    // the model lane catches up. The drain must cut the run at its deadline
    // and end once both lanes have made the writes the cut keeps, which
    // model_cmp pairs exactly: no error. The levels go unchecked.
    class external_reg_mode_b_dst_drain_busy_test extends external_reg_mode_b_dst_test;
        `uvm_component_utils(external_reg_mode_b_dst_drain_busy_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            for (int unsigned i = n_writes; i < 50 * n_writes; i++) begin
                er_item_t m;
                seq.items.push_back(write_item(lb_data_t'($urandom()), 0));
                $cast(m, seq.items[i].clone());
                model_seq.items.push_back(m);
            end
            foreach (seq.items[i]) begin
                seq.items[i].gap       = i % 3;
                model_seq.items[i].gap = i % 3 + 3 * (i == 0);
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            agent.drv.replay.drain_quiet_cycles    = 30;
            agent.drv.replay.drain_deadline_cycles = 300;
            tracker.logs.push_back(agent.drv.replay);
        endfunction

        protected virtual task run_dst();
            level_sb.expected.delete();
            model_level_sb.expected.delete();
            fork
                seq.start(peer.sqr);
                model_seq.start(model_peer.sqr);
            join_none
            while (agent.drv.lane_starts(A2C_DUT_LANE) < n_writes) clk_vif.sample_edge();
        endtask

        virtual function void check_phase(uvm_phase phase);
            int unsigned dut = agent.drv.lane_done(A2C_DUT_LANE);
            int unsigned model = agent.drv.lane_done(A2C_MODEL_LANE);
            `uvm_info("LB_STATS", $sformatf("cut after %0d; %0d and %0d writes on the DUT and model lanes; %0d pairs", agent.drv.replay.get_cut(),
                                            dut, model, agent.model_cmp.get_pairs()), UVM_NONE)
            check_cut(agent.drv.replay, n_writes, agent.model_cmp.get_pairs(), dut, model);
            if (dut >= seq.items.size()) `uvm_error("LB_MODE_B", "the DUT lane's peer ran out of writes, so the port paused")
        endfunction
    endclass : external_reg_mode_b_dst_drain_busy_test
