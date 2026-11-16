// Mode B with agents that a2c does not provide, compared by a2c_mode_b_port:
// hand-written rdy_vld sources and sinks that implement only
// a2c_mode_b_agent, two of them on a2c_lane_driver, and one test per way of
// breaking the contract. Included in a2c_uvm_loopback_pkg after the rdy_vld
// and push_ack tests, whose typedefs and sequences it uses.

    // How a test breaks the contract, if it does.
    typedef enum {LB_FA_NONE, LB_FA_NOT_AGENT, LB_FA_NULL_AP, LB_FA_SAME_AP, LB_FA_NO_WATCHDOG, LB_FA_ONE_LANE,
                  LB_FA_MISLABELLED, LB_FA_UNSTEPPED, LB_FA_UNCONFIGURED, LB_FA_LOG_NO_DRIVER,
                  LB_FA_LOG_NO_CLK} lb_fa_fault_e;

    // Writes each transfer on its pin set and never calls
    // a2c_joint_watch::handshake(), as a vendor monitor would not.
    class lb_foreign_monitor extends uvm_monitor;
        rv_vif_t                      vif;
        virtual a2c_clk_if            clk_vif;
        uvm_analysis_port #(rv_item_t) ap;

        `uvm_component_utils(lb_foreign_monitor)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            rv_item_t it;
            clk_vif.wait_reset_release();
            forever begin
                clk_vif.sample_edge();
                if (vif.vld !== 1'b1 || vif.rdy !== 1'b1) continue;
                it = rv_item_t::type_id::create("it");
                it.data = vif.data;
                ap.write(it);
            end
        endtask
    endclass : lb_foreign_monitor

    // Puts each item on both lanes and completes it once every live lane
    // has transferred it, stepping its watchdog once per clock. fault
    // decides whether it builds, configures and steps the watchdog.
    class lb_foreign_driver extends uvm_driver #(rv_item_t) implements a2c_lane_waits;
        rv_vif_t           vif[2];
        virtual a2c_clk_if clk_vif;
        string             port;
        lb_fa_fault_e      fault;
        a2c_lane_watchdog  wd;

        `uvm_component_utils(lb_foreign_driver)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (fault inside {LB_FA_NO_WATCHDOG, LB_FA_MISLABELLED}) return;
            wd = new(this, port, (fault == LB_FA_ONE_LANE) ? 1 : 2, "item", "every open and later item completes at once");
        endfunction

        virtual function string waiting_for(a2c_lane_e l);
            return {"the transfer of ", req.convert2string()};
        endfunction

        protected function bit live(int l);
            return wd == null || !wd.dead[l];
        endfunction

        virtual task run_phase(uvm_phase phase);
            bit pending[2];
            bit took[2];
            bit stepped = wd != null && fault != LB_FA_UNSTEPPED;
            if (wd != null && fault != LB_FA_UNCONFIGURED) wd.configure(clk_vif);
            foreach (vif[l]) vif[l].vld <= 1'b0;
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            forever begin
                seq_item_port.get_next_item(req);
                if (stepped) wd.begin_item();
                foreach (vif[l]) begin
                    pending[l] = live(l);
                    if (!pending[l]) continue;
                    vif[l].vld  <= 1'b1;
                    vif[l].data <= req.data;
                end
                while (pending[A2C_DUT_LANE] || pending[A2C_MODEL_LANE]) begin
                    clk_vif.sample_edge();
                    foreach (vif[l]) begin
                        took[l]     = pending[l] && vif[l].rdy === 1'b1;
                        pending[l] &= !took[l];
                    end
                    if (stepped) wd.step(took, pending);
                    clk_vif.drive_edge();
                    foreach (vif[l]) if (took[l]) vif[l].vld <= 1'b0;
                end
                seq_item_port.item_done();
            end
        endtask
    endclass : lb_foreign_driver

    // The test sets the pins, the clock, the port name and fault before the
    // agent's build_phase.
    class lb_foreign_agent extends uvm_agent implements a2c_mode_b_agent #(rv_item_t);
        rv_vif_t                    vif[2];
        virtual a2c_clk_if          clk_vif;
        string                      port;
        lb_fa_fault_e               fault;
        lb_foreign_driver           drv;
        uvm_sequencer #(rv_item_t)  sqr;
        lb_foreign_monitor          mons[2];

        `uvm_component_utils(lb_foreign_agent)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            drv = lb_foreign_driver::type_id::create("drv", this);
            sqr = uvm_sequencer#(rv_item_t)::type_id::create("sqr", this);
            drv.vif     = vif;
            drv.clk_vif = clk_vif;
            drv.port    = port;
            drv.fault   = fault;
            foreach (mons[l]) begin
                mons[l] = lb_foreign_monitor::type_id::create($sformatf("mon%0d", l), this);
                mons[l].vif     = vif[l];
                mons[l].clk_vif = clk_vif;
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            drv.seq_item_port.connect(sqr.seq_item_export);
        endfunction

        virtual function uvm_analysis_port #(rv_item_t) lane_ap(a2c_lane_e l);
            if (fault == LB_FA_NULL_AP && l == A2C_MODEL_LANE) return null;
            if (fault == LB_FA_SAME_AP) return mons[A2C_DUT_LANE].ap;
            return mons[l].ap;
        endfunction

        virtual function a2c_lane_watchdog lane_watchdog();
            return drv.wd;
        endfunction

        virtual function a2c_replay_log_base lane_replay();
            return null;
        endfunction

        virtual function bit lanes_in_lock_step();
            return 0;
        endfunction
    endclass : lb_foreign_agent

    // A source an author writes on a2c_lane_driver: the base's master loop
    // with the pin hooks of rdy_vld.
    class lb_lane_source extends a2c_lane_driver #(rv_item_t, rv_vif_t, rv_config_t);
        `uvm_component_utils(lb_lane_source)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected virtual function void raise_request(int l);
            lane[l].vld  <= 1'b1;
            lane[l].data <= req.data;
        endfunction

        protected virtual function void drop_request(int l);
            lane[l].vld <= 1'b0;
        endfunction

        protected virtual function bit request_held(int l);
            return lane[l].vld === 1'b1;
        endfunction

        protected virtual function bit request_taken(int l);
            return lane[l].rdy === 1'b1;
        endfunction
    endclass : lb_lane_source

    // A sink an author writes on a2c_lane_driver: the base's responder
    // cycle raises rdy for one clock per beat after a delay the DUT lane
    // draws and records, which the model lane replays.
    class lb_lane_sink extends a2c_lane_driver #(rv_item_t, rv_vif_t, rv_config_t);
        `uvm_component_utils(lb_lane_sink)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected virtual function bit request_seen(int l);
            return lane[l].vld === 1'b1;
        endfunction

        protected virtual task respond(output bit r, output int unsigned delay, output bit at_edge);
            r       = 1'b1;
            delay   = $urandom_range(2, 0);
            at_edge = 0;
        endtask

        protected virtual function void idle_response(int l);
            lane[l].rdy <= 1'b0;
        endfunction

        protected virtual function void drive_response(int l, bit r);
            lane[l].rdy <= 1'b1;
        endfunction

        protected virtual function void end_response(int l);
            lane[l].rdy <= 1'b0;
        endfunction
    endclass : lb_lane_sink

    // A foreign agent whose driver is lb_lane_source on A2C_SRC and
    // lb_lane_sink on A2C_DST. The test sets cfg before the agent's
    // build_phase; fault breaks the sink's replay log.
    class lb_foreign_lane_agent extends uvm_agent implements a2c_mode_b_agent #(rv_item_t);
        rv_config_t                                          cfg;
        lb_fa_fault_e                                        fault;
        a2c_lane_driver #(rv_item_t, rv_vif_t, rv_config_t) drv;
        uvm_sequencer #(rv_item_t)                           sqr;
        lb_foreign_monitor                                   mons[2];

        `uvm_component_utils(lb_foreign_lane_agent)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_vif_t pins[2];
            super.build_phase(phase);
            pins = '{cfg.vif, cfg.model_vif};
            if (cfg.role == A2C_SRC) begin
                drv = lb_lane_source::type_id::create("drv", this);
                sqr = uvm_sequencer#(rv_item_t)::type_id::create("sqr", this);
            end else begin
                drv = lb_lane_sink::type_id::create("drv", this);
            end
            drv.cfg = cfg;
            foreach (mons[l]) begin
                mons[l] = lb_foreign_monitor::type_id::create($sformatf("mon%0d", l), this);
                mons[l].vif     = pins[l];
                mons[l].clk_vif = cfg.clk_vif;
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (sqr != null) drv.seq_item_port.connect(sqr.seq_item_export);
            if (fault == LB_FA_LOG_NO_DRIVER) drv.replay.driver = null;
            if (fault == LB_FA_LOG_NO_CLK) drv.replay.clk_vif = null;
        endfunction

        virtual function uvm_analysis_port #(rv_item_t) lane_ap(a2c_lane_e l);
            return mons[l].ap;
        endfunction

        virtual function a2c_lane_watchdog lane_watchdog();
            return drv.wd;
        endfunction

        virtual function a2c_replay_log_base lane_replay();
            return drv.replay;
        endfunction

        virtual function bit lanes_in_lock_step();
            return 0;
        endfunction
    endclass : lb_foreign_lane_agent

    // Sends n random rdy_vld items on sqr.
    task automatic lb_send_rv(uvm_sequencer #(rv_item_t) sqr, int unsigned n);
        lb_list_seq#(rv_item_t) seq = lb_list_seq#(rv_item_t)::type_id::create("seq");
        for (int unsigned i = 0; i < n; i++) begin
            rv_item_t it = rv_item_t::type_id::create("it");
            if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
            seq.items.push_back(it);
        end
        seq.start(sqr);
    endtask

    // The foreign source sends n_items beats to an a2c rdy_vld sink on each
    // lane, each with random rdy, and a2c_mode_b_port pairs every beat. Its
    // watchdog takes model_cmp from the port. A test that sets fault expects
    // the one A2C_MODE_B_CONTRACT its want_text names, demoted, and
    // want_pairs pairs.
    class mode_b_foreign_agent_test extends lb_mode_b_base;
        lb_foreign_agent             agent;
        rv_agent_t                   sinks[2];
        a2c_mode_b_port #(rv_item_t) port;
        lb_fa_fault_e                fault;
        int unsigned                 want_pairs;

        `uvm_component_utils(mode_b_foreign_agent_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_MODE_B_CONTRACT";
            n_items   = 100;
        endfunction

        // At build_phase, before the agents: a test's own expectations and
        // knobs.
        virtual function void configure();
        endfunction

        // At build_phase: the sink config of lane l.
        virtual function void configure_sink(int l, rv_config_t cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            string pins[2] = '{"rv", "rv_model"};
            if (fault != LB_FA_NONE) want_errors = 1;
            want_pairs = (fault inside {LB_FA_NOT_AGENT, LB_FA_NULL_AP, LB_FA_SAME_AP}) ? 0 : n_items;
            configure();
            super.build_phase(phase);
            agent = lb_foreign_agent::type_id::create("agent", this);
            port  = a2c_mode_b_port#(rv_item_t)::type_id::create("port", this);
            port.agent    = agent;
            agent.clk_vif = clk_vif;
            agent.port    = "rv";
            agent.fault   = fault;
            foreach (sinks[l]) begin
                rv_config_t cfg = rv_config_t::type_id::create($sformatf("sink%0d_cfg", l));
                if (!uvm_config_db#(rv_vif_t)::get(this, "", pins[l], cfg.vif)) `uvm_fatal("LB_CFG", {"no virtual rdy_vld_if ", pins[l]})
                agent.vif[l]  = cfg.vif;
                cfg.clk_vif   = clk_vif;
                cfg.role      = A2C_DST;
                cfg.port_name = pins[l];
                cfg.ready_pct = 50;
                configure_sink(l, cfg);
                uvm_config_db#(rv_config_t)::set(this, $sformatf("sink%0d", l), "cfg", cfg);
                sinks[l] = rv_agent_t::type_id::create($sformatf("sink%0d", l), this);
            end
            if (fault == LB_FA_NOT_AGENT) port.agent = sinks[A2C_DUT_LANE];
            if (fault == LB_FA_MISLABELLED) port.role = A2C_DST;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            lb_send_rv(agent.sqr, n_items);
            repeat (5) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (port.model_cmp.get_pairs() != want_pairs) begin
                `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d beats, expected %0d", port.model_cmp.get_pairs(), want_pairs))
            end
            if (fault == LB_FA_NONE && agent.drv.wd.cmp != port.model_cmp) `uvm_error("LB_MODE_B", "the port did not hand model_cmp to the watchdog")
        endfunction
    endclass : mode_b_foreign_agent_test

    // The env hands the port an a2c agent, which does not implement
    // a2c_mode_b_agent: raised at connect_phase, and nothing pairs.
    class mode_b_contract_not_agent_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_contract_not_agent_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault = LB_FA_NOT_AGENT;
            want_text.push_back("uvm_test_top.sink0: the agent does not implement a2c_mode_b_agent");
        endfunction
    endclass : mode_b_contract_not_agent_test

    // The model lane's analysis port is null.
    class mode_b_contract_null_ap_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_contract_null_ap_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault = LB_FA_NULL_AP;
            want_text.push_back("uvm_test_top.agent: lane_ap(A2C_MODEL_LANE) is null");
        endfunction
    endclass : mode_b_contract_null_ap_test

    // Both lanes give the DUT lane's analysis port, which would match every
    // beat against itself.
    class mode_b_contract_same_ap_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_contract_same_ap_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault = LB_FA_SAME_AP;
            want_text.push_back("uvm_test_top.agent: lane_ap() returns one analysis port for both lanes");
        endfunction
    endclass : mode_b_contract_same_ap_test

    // The foreign source builds no watchdog: one A2C_MODE_B_CONTRACT naming
    // it, and the beats still pair.
    class mode_b_foreign_agent_no_watchdog_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_foreign_agent_no_watchdog_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault = LB_FA_NO_WATCHDOG;
            want_text.push_back("uvm_test_top.agent: an active master gives no lane watchdog");
        endfunction
    endclass : mode_b_foreign_agent_no_watchdog_test

    // The source builds its watchdog with one lane.
    class mode_b_contract_one_lane_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_contract_one_lane_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault = LB_FA_ONE_LANE;
            want_text.push_back("uvm_test_top.agent: the lane watchdog counts 1 lanes, not the 2 of Mode B");
        endfunction
    endclass : mode_b_contract_one_lane_test

    // The env gives the port the role A2C_DST for a master with no
    // watchdog.
    class mode_b_contract_mislabelled_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_contract_mislabelled_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault = LB_FA_MISLABELLED;
            want_text.push_back("uvm_test_top.agent: an active A2C_DST agent gives neither a lane watchdog nor a replay log");
        endfunction
    endclass : mode_b_contract_mislabelled_test

    // The source builds and configures its watchdog and never steps it:
    // raised at check_phase, once model_cmp has paired the beats.
    class mode_b_contract_unstepped_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_contract_unstepped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault = LB_FA_UNSTEPPED;
            want_text.push_back("uvm_test_top.agent: model_cmp paired 100 items, but the master never stepped its lane watchdog");
        endfunction
    endclass : mode_b_contract_unstepped_test

    // The source steps its watchdog and never configures it. An
    // unconfigured watchdog keeps its default model throttle bound, so both
    // sinks are always ready.
    class mode_b_contract_unconfigured_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_contract_unconfigured_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault = LB_FA_UNCONFIGURED;
            want_text.push_back("uvm_test_top.agent: the master never called configure() on its lane watchdog");
        endfunction

        virtual function void configure_sink(int l, rv_config_t cfg);
            cfg.ready_pct = 100;
        endfunction
    endclass : mode_b_contract_unconfigured_test

    // The model lane's sink never raises rdy, so the foreign source's
    // watchdog declares the model lane dead after 30 clocks: one A2C_SKEW,
    // and model_cmp, which the port gave the watchdog, reports none of the
    // DUT lane's unpaired beats.
    class mode_b_foreign_model_death_test extends mode_b_foreign_agent_test;
        `uvm_component_utils(mode_b_foreign_model_death_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            demote_id  = "A2C_SKEW";
            want_errors = 1;
            want_text.push_back("rv: the model lane has not completed the transfer of ");
            want_text.push_back("so the master declares the model lane dead");
            want_pairs = 0;
            uvm_config_db#(int unsigned)::set(this, "agent.drv", "a2c_lane_skew_cycles", 30);
        endfunction

        virtual function void configure_sink(int l, rv_config_t cfg);
            if (l == A2C_MODEL_LANE) cfg.ready_pct = 0;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (!agent.drv.wd.dead[A2C_MODEL_LANE] || agent.drv.wd.dead[A2C_DUT_LANE]) begin
                `uvm_error("LB_MODE_B", $sformatf("the lanes died %p, expected the model lane alone", agent.drv.wd.dead))
            end
        endfunction
    endclass : mode_b_foreign_model_death_test

    // Foreign agents on a2c_lane_driver, each on its own port. With
    // foreign_src a foreign source drives rv and rv_model, and otherwise an
    // a2c rdy_vld source does; a foreign sink with a replay log serves both.
    // With pa_busy an a2c push_ack master on pa waits 300 clocks for each of
    // two acks, with joint_stall_cycles 100, while the rdy_vld beats flow.
    // With stall_expected the joint stall kills every lane before n_items
    // beats, and the ports pair fewer.
    class lb_foreign_lane_base extends lb_mode_b_base;
        lb_foreign_lane_agent        src;
        rv_agent_t                   a2c_src;
        lb_foreign_lane_agent        sink;
        a2c_mode_b_port #(rv_item_t) src_port;
        a2c_mode_b_port #(rv_item_t) sink_port;
        pa_agent_t                   pa_src;
        pa_agent_t                   pa_dst;
        bit                          foreign_src;
        bit                          pa_busy;
        bit                          stall_expected;
        lb_fa_fault_e                fault;

        `uvm_component_utils(lb_foreign_lane_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_MODE_B_CONTRACT";
            n_items   = 100;
        endfunction

        protected function rv_config_t rv_cfg(string name, a2c_role_e role);
            rv_config_t cfg = rv_config_t::type_id::create(name);
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", cfg.vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if rv")
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv_model", cfg.model_vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if rv_model")
            cfg.clk_vif   = clk_vif;
            cfg.role      = role;
            cfg.port_name = "rv";
            return cfg;
        endfunction

        protected function void build_pa(string name, a2c_role_e role, int unsigned ack_delay);
            pa_config_t cfg = pa_config_t::type_id::create({name, "_cfg"});
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa", cfg.vif)) `uvm_fatal("LB_CFG", "no virtual push_ack_if pa")
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa_model", cfg.model_vif)) `uvm_fatal("LB_CFG", "no virtual push_ack_if pa_model")
            cfg.clk_vif       = clk_vif;
            cfg.role          = role;
            cfg.port_name     = "pa";
            cfg.ack_delay_min = ack_delay;
            cfg.ack_delay_max = ack_delay;
            uvm_config_db#(pa_config_t)::set(this, name, "cfg", cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            sink = lb_foreign_lane_agent::type_id::create("sink", this);
            sink.cfg   = rv_cfg("sink_cfg", A2C_DST);
            sink.fault = fault;
            sink_port  = a2c_mode_b_port#(rv_item_t)::type_id::create("sink_port", this);
            sink_port.agent = sink;
            sink_port.role  = A2C_DST;
            if (foreign_src) begin
                src = lb_foreign_lane_agent::type_id::create("src", this);
                src.cfg  = rv_cfg("src_cfg", A2C_SRC);
                src_port = a2c_mode_b_port#(rv_item_t)::type_id::create("src_port", this);
                src_port.agent = src;
            end else begin
                uvm_config_db#(rv_config_t)::set(this, "a2c_src", "cfg", rv_cfg("a2c_src_cfg", A2C_SRC));
                a2c_src = rv_agent_t::type_id::create("a2c_src", this);
            end
            if (!pa_busy) return;
            build_pa("pa_src", A2C_SRC, 0);
            build_pa("pa_dst", A2C_DST, 300);
            pa_src = pa_agent_t::type_id::create("pa_src", this);
            pa_dst = pa_agent_t::type_id::create("pa_dst", this);
            uvm_config_db#(int unsigned)::set(this, "pa_src.drv", "a2c_joint_stall_cycles", 100);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                lb_send_rv(foreign_src ? src.sqr : a2c_src.sqr, n_items);
                if (pa_busy) begin
                    lb_list_seq#(pa_item_t) seq = lb_list_seq#(pa_item_t)::type_id::create("pa_seq");
                    repeat (2) begin
                        pa_item_t it = pa_item_t::type_id::create("it");
                        if (!it.randomize()) `uvm_fatal("LB_RAND", "push_ack item randomize failed")
                        seq.items.push_back(it);
                    end
                    seq.start(pa_src.sqr);
                end
            join
            repeat (5) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (stall_expected) begin
                if (sink_port.model_cmp.get_pairs() >= n_items) `uvm_error("LB_MODE_B", "the sink's model_cmp paired every beat, though the lanes died")
                return;
            end
            if (sink_port.model_cmp.get_pairs() != n_items) begin
                `uvm_error("LB_MODE_B", $sformatf("the sink's model_cmp paired %0d beats, expected %0d", sink_port.model_cmp.get_pairs(), n_items))
            end
            if (fault == LB_FA_NONE && sink.drv.replay.cmp != sink_port.model_cmp) begin
                `uvm_error("LB_MODE_B", "the port did not hand model_cmp to the replay log")
            end
            if (!foreign_src) return;
            if (src_port.model_cmp.get_pairs() != n_items) begin
                `uvm_error("LB_MODE_B", $sformatf("the source's model_cmp paired %0d beats, expected %0d", src_port.model_cmp.get_pairs(), n_items))
            end
            if (src.drv.wd.cmp != src_port.model_cmp) `uvm_error("LB_MODE_B", "the port did not hand model_cmp to the watchdog")
            if (src.drv.wd.steps == 0) `uvm_error("LB_MODE_B", "the lane driver never stepped its watchdog")
        endfunction
    endclass : lb_foreign_lane_base

    // A foreign source on a2c_lane_driver, whose watchdog exists from its
    // connect_phase, and a foreign sink with a replay log, each through its
    // own port: no A2C_MODE_B_CONTRACT, and both ports pair every beat.
    class mode_b_foreign_lane_driver_test extends lb_foreign_lane_base;
        `uvm_component_utils(mode_b_foreign_lane_driver_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            foreign_src = 1;
        endfunction
    endclass : mode_b_foreign_lane_driver_test

    // An a2c rdy_vld source and a foreign sink whose model lane replays the
    // DUT lane's recorded delays.
    class mode_b_foreign_responder_test extends lb_foreign_lane_base;
        `uvm_component_utils(mode_b_foreign_responder_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass : mode_b_foreign_responder_test

    // The foreign sink's replay log has no driver.
    class mode_b_contract_log_no_driver_test extends lb_foreign_lane_base;
        `uvm_component_utils(mode_b_contract_log_no_driver_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault       = LB_FA_LOG_NO_DRIVER;
            want_errors = 1;
            want_text.push_back("uvm_test_top.sink: the replay log has no driver or no clk_vif");
        endfunction
    endclass : mode_b_contract_log_no_driver_test

    // The foreign sink's replay log has no clk_vif, which the log reports
    // too, as A2C_CFG.
    class mode_b_contract_log_no_clk_test extends lb_foreign_lane_base;
        a2c_expected_error no_clk;

        `uvm_component_utils(mode_b_contract_log_no_clk_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            fault       = LB_FA_LOG_NO_CLK;
            want_errors = 1;
            want_text.push_back("uvm_test_top.sink: the replay log has no driver or no clk_vif");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            no_clk      = a2c_expected_error::type_id::create("no_clk", this);
            no_clk.id   = "A2C_CFG";
            no_clk.text = "uvm_test_top.sink.drv.replay: the replay log has no clk_vif";
        endfunction
    endclass : mode_b_contract_log_no_clk_test

    // Only the ports count the foreign rdy_vld transfers as handshakes, as
    // no monitor on rv or rv_model calls handshake(). They keep the push_ack
    // master's 300-clock waits, three times its joint_stall_cycles, from
    // raising A2C_JOINT_STALL.
    class mode_b_foreign_handshake_test extends lb_foreign_lane_base;
        `uvm_component_utils(mode_b_foreign_handshake_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            foreign_src = 1;
            pa_busy     = 1;
            n_items     = 400;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (pa_src.drv.wd.steps < 300) `uvm_error("LB_MODE_B", $sformatf("the push_ack master waited %0d clocks, short of one ack of 300", pa_src.drv.wd.steps))
        endfunction
    endclass : mode_b_foreign_handshake_test

    // As mode_b_foreign_handshake_test with joint_watch cleared on both
    // ports, as for agents inside the DUT: the rdy_vld transfers count for
    // nothing, so the push_ack master's first 300-clock wait raises the one
    // A2C_JOINT_STALL.
    class mode_b_foreign_joint_watch_off_test extends lb_foreign_lane_base;
        `uvm_component_utils(mode_b_foreign_joint_watch_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            foreign_src    = 1;
            pa_busy        = 1;
            n_items        = 400;
            stall_expected = 1;
            demote_id      = "A2C_JOINT_STALL";
            want_errors    = 1;
            want_text.push_back("pa: no port has made a handshake on any lane for 100 of this port's clocks");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            src_port.joint_watch  = 0;
            sink_port.joint_watch = 0;
        endfunction
    endclass : mode_b_foreign_joint_watch_off_test
