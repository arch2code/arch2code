// Tests of a mid-run reset that a test requests through
// a2c_clk_if::request_reset(). Included in a2c_uvm_loopback_pkg after the
// agents' tests, whose typedefs they use.

    // The resets clk_vif has asserted since the run began, which
    // lb_reset_seq reads to start its list again.
    class lb_reset_epoch;
        int unsigned n;
    endclass : lb_reset_epoch

    // Sends items over and over until a reset, then once more from the
    // first and stops. The item the driver held at the reset completes
    // there, and the first item the driver takes after the release is
    // items[0], so the two lanes of a Mode B port send the same items from
    // the release whatever each had sent before. Responses are taken and
    // dropped.
    class lb_reset_seq #(type T = uvm_sequence_item) extends uvm_sequence #(T);
        T              items[$];
        lb_reset_epoch epoch;

        `uvm_object_param_utils(lb_reset_seq#(T))

        function new(string name = "lb_reset_seq");
            super.new(name);
            use_response_handler(1);
        endfunction

        virtual function void response_handler(uvm_sequence_item response);
        endfunction

        virtual task body();
            int unsigned seen = epoch.n;
            int unsigned i = 0;
            forever begin
                T it;
                if (seen != 0 && seen == epoch.n && i == items.size()) break;
                it = T::type_id::create("it");
                start_item(it);
                if (epoch.n != seen) begin
                    seen = epoch.n;
                    i    = 0;
                end
                it.copy(items[i % items.size()]);
                finish_item(it);
                i++;
            end
        endtask
    endclass : lb_reset_seq

    // One Mode B port of lb_reset_mode_b_test: the agent under test on
    // both lanes, and a peer on each lane in the opposite role. The side
    // that sends runs an lb_reset_seq per sequencer, the model lane's
    // items with other gaps. A dual counter counts the agent's monitors.
    virtual class lb_reset_port #(type AGENT_T = uvm_agent, type ITEM_T = uvm_sequence_item,
                                  type CFG_T = uvm_object, type VIF_T = int) extends uvm_component;
        string                   port;
        a2c_role_e               role = A2C_SRC;
        virtual a2c_clk_if       clk_vif;
        lb_reset_epoch           epoch;
        int unsigned             n_items = 40;
        AGENT_T                  agent;
        AGENT_T                  peer;
        AGENT_T                  model_peer;
        CFG_T                    agent_cfg;
        CFG_T                    peer_cfg;
        CFG_T                    model_peer_cfg;
        ITEM_T                   items[$];
        ITEM_T                   model_items[$];
        a2c_txn_counter #(ITEM_T) counter;
        lb_arrivals#(ITEM_T)     arrivals;
        lb_arrivals#(ITEM_T)     model_arrivals;
        // At the reset: the comparator's pairs and each lane's items.
        int unsigned             pairs_at_reset;
        int unsigned             seen_at_reset[2];

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        pure virtual function ITEM_T new_item(int unsigned i);
        // Sets the configs' delays, and the model lane's gap of an item.
        pure virtual function void configure();
        pure virtual function int unsigned model_gap();

        // What the port had in flight at the reset beyond the lanes' item
        // counts, or "".
        virtual function string held_at_reset();
            return "";
        endfunction

        protected function CFG_T lane_cfg(string name, VIF_T lane_vif, a2c_role_e lane_role, string lane_port);
            CFG_T cfg = CFG_T::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = lane_port;
            return cfg;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            VIF_T      vif;
            VIF_T      model_vif;
            a2c_role_e peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            super.build_phase(phase);
            if (!uvm_config_db#(VIF_T)::get(get_parent(), "", port, vif)) `uvm_fatal("LB_CFG", {"no interface ", port})
            if (!uvm_config_db#(VIF_T)::get(get_parent(), "", {port, "_model"}, model_vif)) `uvm_fatal("LB_CFG", {"no interface ", port, "_model"})
            agent_cfg = lane_cfg("agent_cfg", vif, role, port);
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lane_cfg("peer_cfg", vif, peer_role, port);
            model_peer_cfg = lane_cfg("model_peer_cfg", model_vif, peer_role, {port, "_model"});
            configure();
            uvm_config_db#(CFG_T)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(CFG_T)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(CFG_T)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent      = AGENT_T::type_id::create("agent", this);
            peer       = AGENT_T::type_id::create("peer", this);
            model_peer = AGENT_T::type_id::create("model_peer", this);
            counter    = a2c_txn_counter#(ITEM_T)::type_id::create("counter", this);
            counter.port_name = port;
            counter.dual      = 1;
            counter.clk_vif   = clk_vif;
            arrivals       = lb_arrivals#(ITEM_T)::type_id::create("arrivals", this);
            model_arrivals = lb_arrivals#(ITEM_T)::type_id::create("model_arrivals", this);
            for (int unsigned i = 0; i < n_items; i++) begin
                ITEM_T it = new_item(i);
                ITEM_T m;
                $cast(m, it.clone());
                m.gap = model_gap();
                items.push_back(it);
                model_items.push_back(m);
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.mon.ap.connect(counter.analysis_export);
            agent.model_mon.ap.connect(counter.model_export);
            agent.mon.ap.connect(arrivals.analysis_export);
            agent.model_mon.ap.connect(model_arrivals.analysis_export);
        endfunction

        protected task send(uvm_sequencer_base sqr, ITEM_T list[$]);
            lb_reset_seq#(ITEM_T) seq = lb_reset_seq#(ITEM_T)::type_id::create("seq");
            seq.items = list;
            seq.epoch = epoch;
            seq.start(sqr);
        endtask

        // Returns once the side that sends has sent its list after the
        // reset.
        task stream();
            if (role == A2C_SRC) begin
                send(agent.sqr, items);
            end else begin
                fork
                    send(peer.sqr, items);
                    send(model_peer.sqr, model_items);
                join
            end
        endtask

        function void note_reset();
            pairs_at_reset = agent.model_cmp.get_pairs();
            seen_at_reset  = '{arrivals.items.size(), model_arrivals.items.size()};
        endfunction

        // Whether the port had an item in flight at the reset: one lane had
        // delivered more than the other, or the port held more.
        function string in_flight();
            string what = held_at_reset();
            if (seen_at_reset[0] != seen_at_reset[1]) begin
                what = {what, a2c_select_str(what == "", "", ", "),
                        $sformatf("the DUT lane had delivered %0d items and the model lane %0d", seen_at_reset[0], seen_at_reset[1])};
            end
            return what;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned after = agent.model_cmp.get_pairs() - pairs_at_reset;
            super.check_phase(phase);
            if (pairs_at_reset == 0) `uvm_error("LB_RESET", $sformatf("%s: model_cmp paired nothing before the reset", port))
            if (after != n_items) begin
                `uvm_error("LB_RESET", $sformatf("%s: model_cmp paired %0d items after the reset, expected the %0d sent from the release",
                                                 port, after, n_items))
            end
            `uvm_info("LB_RESET", $sformatf("%s: %0d pairs before the reset, %0d after; in flight at the reset: %s", port,
                                            pairs_at_reset, after, in_flight()), UVM_NONE)
        endfunction
    endclass : lb_reset_port

    // rdy_vld with the agent the A2C_DST side: its comparator re-pairs.
    class lb_reset_rv_port extends lb_reset_port #(rv_agent_t, rv_item_t, rv_config_t, rv_vif_t);
        `uvm_component_utils(lb_reset_rv_port)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "rv";
            role = A2C_DST;
        endfunction

        virtual function rv_item_t new_item(int unsigned i);
            rv_item_t it = rv_item_t::type_id::create("it");
            if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
            it.gap = 0;
            return it;
        endfunction

        virtual function void configure();
            agent_cfg.ready_pct = 70;
        endfunction

        virtual function int unsigned model_gap();
            return $urandom_range(3, 1);
        endfunction
    endclass : lb_reset_rv_port

    // push_ack with the agent the A2C_DST side: the model lane, behind,
    // replays the DUT lane's acks from the replay log, which the reset
    // empties.
    class lb_reset_pa_port extends lb_reset_port #(pa_agent_t, pa_item_t, pa_config_t, pa_vif_t);
        int unsigned replay_at_reset;

        `uvm_component_utils(lb_reset_pa_port)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "pa";
            role = A2C_DST;
        endfunction

        virtual function pa_item_t new_item(int unsigned i);
            pa_item_t it = pa_item_t::type_id::create("it");
            if (!it.randomize()) `uvm_fatal("LB_RAND", "push_ack item randomize failed")
            it.data.value = 20'(i);
            it.gap = 0;
            return it;
        endfunction

        virtual function void configure();
            agent_cfg.ack_delay_max = 2;
        endfunction

        virtual function int unsigned model_gap();
            return $urandom_range(4, 2);
        endfunction

        virtual function string held_at_reset();
            if (replay_at_reset == 0) return "";
            return $sformatf("%0d acks recorded for the model lane and not replayed", replay_at_reset);
        endfunction
    endclass : lb_reset_pa_port

    // axi_read with the agent the master: the model lane's slave answers
    // later, so bursts are outstanding on it at the reset, and the master
    // returns them with no beats.
    class lb_reset_axr_port extends lb_reset_port #(axr_agent_t, axr_item_t, axr_config_t, axr_vif_t);
        `uvm_component_utils(lb_reset_axr_port)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            port    = "axr";
            role    = A2C_SRC;
            n_items = 20;
        endfunction

        virtual function axr_item_t new_item(int unsigned i);
            axr_item_t it = axr_item_t::type_id::create("it");
            if (!it.randomize() with {len < 4;}) `uvm_fatal("LB_RAND", "axi_read item randomize failed")
            it.gap = 0;
            return it;
        endfunction

        virtual function void configure();
            axi_read_mem_t mem = axi_read_mem_t::type_id::create("mem");
            agent_cfg.max_outstanding     = 4;
            peer_cfg.mem                  = mem;
            model_peer_cfg.mem            = mem;
            peer_cfg.resp_delay_max       = 1;
            model_peer_cfg.resp_delay_min = 4;
            model_peer_cfg.resp_delay_max = 8;
        endfunction

        virtual function int unsigned model_gap();
            return 0;
        endfunction
    endclass : lb_reset_axr_port

    // Three Mode B ports on clk run until each has paired some items, the
    // test resets clk's domain with items in flight, and each port sends
    // its list again from the release. Every lane recovers: each
    // comparator pairs exactly the items sent after the release, the
    // counters see each lane's full list after it, and nothing in flight
    // at the reset is reported as missing, extra or unpaired. At least two
    // ports must have had an item in flight at the reset, push_ack's replay
    // log or a lane ahead of the other.
    class lb_reset_mode_b_test extends lb_mode_b_base;
        lb_reset_epoch    epoch;
        lb_reset_rv_port  rv_port;
        lb_reset_pa_port  pa_port;
        lb_reset_axr_port axr_port;
        realtime          reset_at;

        `uvm_component_utils(lb_reset_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            epoch    = new();
            rv_port  = lb_reset_rv_port::type_id::create("rv_port", this);
            pa_port  = lb_reset_pa_port::type_id::create("pa_port", this);
            axr_port = lb_reset_axr_port::type_id::create("axr_port", this);
            rv_port.clk_vif  = clk_vif;
            pa_port.clk_vif  = clk_vif;
            axr_port.clk_vif = clk_vif;
            rv_port.epoch    = epoch;
            pa_port.epoch    = epoch;
            axr_port.epoch   = epoch;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.wait_reset_assert();
                    epoch.n++;
                    reset_at = $realtime;
                end
            join_none
            fork
                rv_port.stream();
                pa_port.stream();
                axr_port.stream();
                begin
                    while (rv_port.agent.model_cmp.get_pairs() < 10 || pa_port.agent.model_cmp.get_pairs() < 10
                           || axr_port.agent.model_cmp.get_pairs() < 5) begin
                        clk_vif.sample_edge();
                    end
                    rv_port.note_reset();
                    pa_port.note_reset();
                    pa_port.replay_at_reset = pa_port.agent.drv.replay.pending();
                    axr_port.note_reset();
                    clk_vif.request_reset();
                    rv_port.counter.expect_count(rv_port.n_items);
                    pa_port.counter.expect_count(pa_port.n_items);
                    axr_port.counter.expect_count(axr_port.n_items);
                end
            join
            fork
                rv_port.counter.wait_for_count(clk_vif, 20000, 20);
                pa_port.counter.wait_for_count(clk_vif, 20000, 20);
                axr_port.counter.wait_for_count(clk_vif, 20000, 20);
            join
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            int unsigned busy = 0;
            super.check_phase(phase);
            if (epoch.n != 1) `uvm_error("LB_RESET", $sformatf("%0d resets seen, expected 1", epoch.n))
            busy += rv_port.in_flight() != "";
            busy += pa_port.in_flight() != "";
            busy += axr_port.in_flight() != "";
            if (busy < 2) `uvm_error("LB_RESET", $sformatf("only %0d ports had an item in flight at the reset at %0t", busy, reset_at))
        endfunction
    endclass : lb_reset_mode_b_test
