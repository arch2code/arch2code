// Mode B with an agent that a2c does not provide: a hand-written rdy_vld
// source that implements only a2c_mode_b_agent, compared by
// a2c_mode_b_port. Included in a2c_uvm_loopback_pkg after the rdy_vld tests,
// whose typedefs and sequences it uses.

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
                a2c_joint_watch::handshake();
                it = rv_item_t::type_id::create("it");
                it.data = vif.data;
                ap.write(it);
            end
        endtask
    endclass : lb_foreign_monitor

    // Puts each item on both lanes and completes it once every live lane
    // has transferred it, stepping its watchdog once per clock. With
    // no_watchdog set it builds none and waits on both lanes.
    class lb_foreign_driver extends uvm_driver #(rv_item_t) implements a2c_lane_waits;
        rv_vif_t           vif[2];
        virtual a2c_clk_if clk_vif;
        string             port;
        bit                no_watchdog;
        a2c_lane_watchdog  wd;

        `uvm_component_utils(lb_foreign_driver)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (!no_watchdog) wd = new(this, port, 2, "item", "every open and later item completes at once");
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
            if (wd != null) wd.configure(clk_vif);
            foreach (vif[l]) vif[l].vld <= 1'b0;
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            forever begin
                seq_item_port.get_next_item(req);
                if (wd != null) wd.begin_item();
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
                    if (wd != null) wd.step(took, pending);
                    clk_vif.drive_edge();
                    foreach (vif[l]) if (took[l]) vif[l].vld <= 1'b0;
                end
                seq_item_port.item_done();
            end
        endtask
    endclass : lb_foreign_driver

    // The test sets the pins, the clock, the port name and no_watchdog
    // before the agent's build_phase.
    class lb_foreign_agent extends uvm_agent implements a2c_mode_b_agent #(rv_item_t);
        rv_vif_t                    vif[2];
        virtual a2c_clk_if          clk_vif;
        string                      port;
        bit                         no_watchdog;
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
            drv.vif         = vif;
            drv.clk_vif     = clk_vif;
            drv.port        = port;
            drv.no_watchdog = no_watchdog;
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
            return mons[l].ap;
        endfunction

        virtual function a2c_lane_watchdog lane_watchdog();
            return drv.wd;
        endfunction

        virtual function a2c_replay_log_base lane_replay();
            return null;
        endfunction
    endclass : lb_foreign_agent

    // The foreign source sends n_items beats to an a2c rdy_vld sink on each
    // lane, each with random rdy, and a2c_mode_b_port pairs every beat. Its
    // watchdog takes model_cmp from the port.
    class mode_b_foreign_agent_test extends lb_mode_b_base;
        lb_foreign_agent            agent;
        rv_agent_t                  sinks[2];
        a2c_mode_b_port #(rv_item_t) port;
        bit                         no_watchdog;

        `uvm_component_utils(mode_b_foreign_agent_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            string pins[2] = '{"rv", "rv_model"};
            super.build_phase(phase);
            agent = lb_foreign_agent::type_id::create("agent", this);
            port  = a2c_mode_b_port#(rv_item_t)::type_id::create("port", this);
            port.agent        = agent;
            agent.clk_vif     = clk_vif;
            agent.port        = "rv";
            agent.no_watchdog = no_watchdog;
            foreach (sinks[l]) begin
                rv_config_t cfg = rv_config_t::type_id::create($sformatf("sink%0d_cfg", l));
                if (!uvm_config_db#(rv_vif_t)::get(this, "", pins[l], cfg.vif)) `uvm_fatal("LB_CFG", {"no virtual rdy_vld_if ", pins[l]})
                agent.vif[l]  = cfg.vif;
                cfg.clk_vif   = clk_vif;
                cfg.role      = A2C_DST;
                cfg.port_name = pins[l];
                cfg.ready_pct = 50;
                uvm_config_db#(rv_config_t)::set(this, $sformatf("sink%0d", l), "cfg", cfg);
                sinks[l] = rv_agent_t::type_id::create($sformatf("sink%0d", l), this);
            end
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_list_seq#(rv_item_t) seq = lb_list_seq#(rv_item_t)::type_id::create("seq");
            phase.raise_objection(this);
            for (int unsigned i = 0; i < n_items; i++) begin
                rv_item_t it = rv_item_t::type_id::create("it");
                if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
                seq.items.push_back(it);
            end
            clk_vif.wait_reset_release();
            seq.start(agent.sqr);
            repeat (5) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (port.model_cmp.get_pairs() != n_items) begin
                `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d beats, expected %0d", port.model_cmp.get_pairs(), n_items))
            end
            if (!no_watchdog && agent.drv.wd.cmp != port.model_cmp) `uvm_error("LB_MODE_B", "the port did not hand model_cmp to the watchdog")
        endfunction
    endclass : mode_b_foreign_agent_test

    // The foreign source builds no watchdog: one A2C_MODE_B_CONTRACT naming
    // it, and the beats still pair.
    class mode_b_foreign_agent_no_watchdog_test extends mode_b_foreign_agent_test;
        a2c_expected_error contract;

        `uvm_component_utils(mode_b_foreign_agent_no_watchdog_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            no_watchdog = 1;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            contract      = a2c_expected_error::type_id::create("contract", this);
            contract.id   = "A2C_MODE_B_CONTRACT";
            contract.text = "uvm_test_top.agent: an active master gives no lane watchdog, so a lane that trails the other or stalls is never declared dead";
        endfunction
    endclass : mode_b_foreign_agent_no_watchdog_test
