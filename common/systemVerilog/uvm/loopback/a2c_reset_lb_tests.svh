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
    // items[0], so the two lanes of a paired-mode port send the same items
    // from the release whatever each had sent before. Responses are taken and
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

    // One paired-mode port of lb_reset_paired_test: the agent under test on
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

    // Three paired-mode ports on clk run until each has paired some items,
    // the test resets clk's domain with items in flight, and each port sends
    // its list again from the release. Every lane recovers: each
    // comparator pairs exactly the items sent after the release, the
    // counters see each lane's full list after it, and nothing in flight
    // at the reset is reported as missing, extra or unpaired. At least two
    // ports must have had an item in flight at the reset, push_ack's replay
    // log or a lane ahead of the other.
    class lb_reset_paired_test extends lb_paired_base;
        lb_reset_epoch    epoch;
        lb_reset_rv_port  rv_port;
        lb_reset_pa_port  pa_port;
        lb_reset_axr_port axr_port;
        realtime          reset_at;

        `uvm_component_utils(lb_reset_paired_test)

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
    endclass : lb_reset_paired_test

    // Requests a reset of clk_vif's domain lead drive points after the one
    // it is called at, and returns at once. Called at the drive point at
    // which a driver takes an item, it puts the reset's first sampled edge,
    // where the driver abandons the item, lead + 2 rising edges on.
    function automatic void lb_reset_after(virtual a2c_clk_if clk_vif, int unsigned lead);
        fork
            begin
                repeat (lead) clk_vif.drive_edge();
                clk_vif.request_reset();
            end
        join_none
    endfunction

    // One memory read, with the reset requested lead drive points after the
    // driver takes it; rsp is the response.
    class lb_reset_held_mem_seq extends memory_base_seq #(lb_mem_addr_t, lb_data_t);
        mem_item_t         it;
        mem_item_t         rsp;
        virtual a2c_clk_if clk_vif;
        int unsigned       lead;

        `uvm_object_utils(lb_reset_held_mem_seq)

        function new(string name = "lb_reset_held_mem_seq");
            super.new(name);
        endfunction

        virtual task body();
            start_item(it);
            lb_reset_after(clk_vif, lead);
            finish_item(it);
            reads_sent++;
            wait_for_reads();
        endtask

        virtual function void read_done(mem_item_t rsp);
            this.rsp = rsp;
        endfunction
    endclass : lb_reset_held_mem_seq

    class lb_reset_held_axr_seq extends axr_base_seq_t;
        axr_item_t         it;
        axr_item_t         rsp;
        virtual a2c_clk_if clk_vif;

        `uvm_object_utils(lb_reset_held_axr_seq)

        function new(string name = "lb_reset_held_axr_seq");
            super.new(name);
        endfunction

        virtual task body();
            start_item(it);
            lb_reset_after(clk_vif, 0);
            finish_item(it);
            reads_sent++;
            wait_for_reads();
        endtask

        virtual function void read_done(item_t rsp);
            this.rsp = rsp;
        endfunction
    endclass : lb_reset_held_axr_seq

    class lb_reset_held_axw_seq extends axw_base_seq_t;
        axw_item_t         it;
        axw_item_t         rsp;
        virtual a2c_clk_if clk_vif;

        `uvm_object_utils(lb_reset_held_axw_seq)

        function new(string name = "lb_reset_held_axw_seq");
            super.new(name);
        endfunction

        virtual task body();
            start_item(it);
            lb_reset_after(clk_vif, 0);
            finish_item(it);
            writes_sent++;
            wait_for_writes();
        endtask

        virtual function void write_done(item_t rsp);
            this.rsp = rsp;
        endfunction
    endclass : lb_reset_held_axw_seq

    class lb_reset_held_apb_seq extends uvm_sequence #(apb_item_t);
        apb_item_t         it;
        virtual a2c_clk_if clk_vif;

        `uvm_object_utils(lb_reset_held_apb_seq)

        function new(string name = "lb_reset_held_apb_seq");
            super.new(name);
        endfunction

        virtual task body();
            start_item(it);
            lb_reset_after(clk_vif, 0);
            finish_item(it);
        endtask
    endclass : lb_reset_held_apb_seq

    // A reset while a master's driver holds an item: a memory read in its
    // gap and in its enable clock, an axi_read and an axi_write burst in its
    // gap before the address goes out, and an apb read in its setup phase.
    // Each sequence must end within a few clocks of the reset, as one that
    // waits for its response would otherwise hang until the run timeout:
    // the memory read with data 0, each AXI burst with no beats, and the
    // apb read with slverr set, so a register read reports UVM_NOT_OK. The
    // pins at the reset's edge show which point each reset hit.
    class lb_reset_held_test extends lb_base_test;
        mem_agent_t   mem_src;
        mem_agent_t   mem_dst;
        axr_agent_t   axr_master;
        axr_agent_t   axr_slave;
        axw_agent_t   axw_master;
        axw_agent_t   axw_slave;
        apb_agent_t   apb_master;
        apb_agent_t   apb_slave;
        mem_vif_t     mem_vif;
        axr_vif_t     axr_vif;
        axw_vif_t     axw_vif;
        apb_vif_t     apb_vif;
        int unsigned  resets;
        // At each reset's first sampled edge: enable, arvalid, awvalid, psel.
        bit           pins_at_reset[4];

        `uvm_component_utils(lb_reset_held_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            mem_config_t mem_src_cfg = mem_config_t::type_id::create("mem_src_cfg");
            mem_config_t mem_dst_cfg = mem_config_t::type_id::create("mem_dst_cfg");
            axr_config_t axr_master_cfg = axr_config_t::type_id::create("axr_master_cfg");
            axr_config_t axr_slave_cfg = axr_config_t::type_id::create("axr_slave_cfg");
            axw_config_t axw_master_cfg = axw_config_t::type_id::create("axw_master_cfg");
            axw_config_t axw_slave_cfg = axw_config_t::type_id::create("axw_slave_cfg");
            apb_config_t apb_master_cfg = apb_config_t::type_id::create("apb_master_cfg");
            apb_config_t apb_slave_cfg = apb_config_t::type_id::create("apb_slave_cfg");
            super.build_phase(phase);
            if (!uvm_config_db#(mem_vif_t)::get(this, "", "mem", mem_vif)) `uvm_fatal("LB_CFG", "no virtual memory_if 'mem'")
            if (!uvm_config_db#(axr_vif_t)::get(this, "", "axr", axr_vif)) `uvm_fatal("LB_CFG", "no virtual axi_read_if 'axr'")
            if (!uvm_config_db#(axw_vif_t)::get(this, "", "axw", axw_vif)) `uvm_fatal("LB_CFG", "no virtual axi_write_if 'axw'")
            if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb", apb_vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb'")
            mem_src_cfg.vif = mem_vif;
            mem_dst_cfg.vif = mem_vif;
            mem_dst_cfg.mem = lb_word_mem_t::type_id::create("mem");
            axr_master_cfg.vif = axr_vif;
            axr_slave_cfg.vif  = axr_vif;
            axr_slave_cfg.mem  = axi_read_mem_t::type_id::create("axr_mem");
            axw_master_cfg.vif = axw_vif;
            axw_slave_cfg.vif  = axw_vif;
            axw_slave_cfg.mem  = axi_write_mem_t::type_id::create("axw_mem");
            apb_master_cfg.vif = apb_vif;
            apb_slave_cfg.vif  = apb_vif;
            apb_slave_cfg.mem  = apb_mem_t::type_id::create("apb_mem");
            mem_src_cfg.port_name    = "mem";
            mem_dst_cfg.port_name    = "mem";
            axr_master_cfg.port_name = "axr";
            axr_slave_cfg.port_name  = "axr";
            axw_master_cfg.port_name = "axw";
            axw_slave_cfg.port_name  = "axw";
            apb_master_cfg.port_name = "apb";
            apb_slave_cfg.port_name  = "apb";
            mem_dst_cfg.role    = A2C_DST;
            axr_slave_cfg.role  = A2C_DST;
            axw_slave_cfg.role  = A2C_DST;
            apb_slave_cfg.role  = A2C_DST;
            mem_src_cfg.clk_vif    = clk_vif;
            mem_dst_cfg.clk_vif    = clk_vif;
            axr_master_cfg.clk_vif = clk_vif;
            axr_slave_cfg.clk_vif  = clk_vif;
            axw_master_cfg.clk_vif = clk_vif;
            axw_slave_cfg.clk_vif  = clk_vif;
            apb_master_cfg.clk_vif = clk_vif;
            apb_slave_cfg.clk_vif  = clk_vif;
            uvm_config_db#(mem_config_t)::set(this, "mem_src", "cfg", mem_src_cfg);
            uvm_config_db#(mem_config_t)::set(this, "mem_dst", "cfg", mem_dst_cfg);
            uvm_config_db#(axr_config_t)::set(this, "axr_master", "cfg", axr_master_cfg);
            uvm_config_db#(axr_config_t)::set(this, "axr_slave", "cfg", axr_slave_cfg);
            uvm_config_db#(axw_config_t)::set(this, "axw_master", "cfg", axw_master_cfg);
            uvm_config_db#(axw_config_t)::set(this, "axw_slave", "cfg", axw_slave_cfg);
            uvm_config_db#(apb_config_t)::set(this, "apb_master", "cfg", apb_master_cfg);
            uvm_config_db#(apb_config_t)::set(this, "apb_slave", "cfg", apb_slave_cfg);
            mem_src    = mem_agent_t::type_id::create("mem_src", this);
            mem_dst    = mem_agent_t::type_id::create("mem_dst", this);
            axr_master = axr_agent_t::type_id::create("axr_master", this);
            axr_slave  = axr_agent_t::type_id::create("axr_slave", this);
            axw_master = axw_agent_t::type_id::create("axw_master", this);
            axw_slave  = axw_agent_t::type_id::create("axw_slave", this);
            apb_master = apb_agent_t::type_id::create("apb_master", this);
            apb_slave  = apb_agent_t::type_id::create("apb_slave", this);
        endfunction

        // Runs seq on sqr and fails unless it ends within 50 clocks of its
        // start and after exactly one more reset.
        protected task run_case(uvm_sequence_base seq, uvm_sequencer_base sqr, string what);
            int unsigned resets_then = resets;
            bit          done;
            fork
                begin
                    seq.start(sqr);
                    done = 1;
                end
            join_none
            for (int unsigned c = 0; c < 50 && !done; c++) clk_vif.sample_edge();
            if (!done) `uvm_error("LB_RESET", $sformatf("%s: the sequence still waits for its response 50 clocks on", what))
            if (resets != resets_then + 1) `uvm_error("LB_RESET", $sformatf("%s: %0d resets, expected 1", what, resets - resets_then))
            clk_vif.wait_reset_release();
        endtask

        protected function void want_pin(int unsigned pin, bit want, string name, string what);
            if (pins_at_reset[pin] != want) begin
                `uvm_error("LB_RESET", $sformatf("%s: %s was %0d at the reset, so the reset missed the point under test", what,
                                                 name, pins_at_reset[pin]))
            end
        endfunction

        protected task mem_case(int unsigned gap, int unsigned lead, bit enable, string what);
            lb_reset_held_mem_seq seq = lb_reset_held_mem_seq::type_id::create("mem_seq");
            seq.it       = mem_item_t::type_id::create("it");
            seq.it.write = 1'b0;
            seq.it.addr  = 7;
            seq.it.gap   = gap;
            seq.clk_vif  = clk_vif;
            seq.lead     = lead;
            run_case(seq, mem_src.sqr, what);
            want_pin(0, enable, "enable", what);
            if (seq.rsp == null) return;
            if (seq.rsp.data !== '0 || seq.rsp.addr != 7) begin
                `uvm_error("LB_RESET", $sformatf("%s: answered %s, expected address 7 with data 0", what, seq.rsp.convert2string()))
            end
        endtask

        virtual task run_phase(uvm_phase phase);
            lb_reset_held_axr_seq axr_seq = lb_reset_held_axr_seq::type_id::create("axr_seq");
            lb_reset_held_axw_seq axw_seq = lb_reset_held_axw_seq::type_id::create("axw_seq");
            lb_reset_held_apb_seq apb_seq = lb_reset_held_apb_seq::type_id::create("apb_seq");
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.wait_reset_assert();
                    pins_at_reset = '{mem_vif.enable === 1'b1, axr_vif.arvalid === 1'b1, axw_vif.awvalid === 1'b1,
                                      apb_vif.psel === 1'b1};
                    resets++;
                end
            join_none
            mem_case(6, 0, 0, "memory read in its gap");
            mem_case(4, 3, 1, "memory read in its enable clock");

            axr_seq.it = axr_item_t::type_id::create("it");
            if (!axr_seq.it.randomize() with {len < 4;}) `uvm_fatal("LB_RAND", "axi_read item randomize failed")
            axr_seq.it.gap = 6;
            axr_seq.clk_vif = clk_vif;
            run_case(axr_seq, axr_master.sqr, "axi_read burst in its gap");
            want_pin(1, 0, "arvalid", "axi_read burst in its gap");
            if (axr_seq.rsp != null && axr_seq.rsp.data.size() != 0) begin
                `uvm_error("LB_RESET", $sformatf("axi_read burst in its gap: returned with %0d beats, expected none", axr_seq.rsp.data.size()))
            end

            axw_seq.it = axw_item_t::type_id::create("it");
            if (!axw_seq.it.randomize() with {len < 4;}) `uvm_fatal("LB_RAND", "axi_write item randomize failed")
            axw_seq.it.gap = 6;
            axw_seq.clk_vif = clk_vif;
            run_case(axw_seq, axw_master.sqr, "axi_write burst in its gap");
            want_pin(2, 0, "awvalid", "axi_write burst in its gap");
            if (axw_seq.rsp != null && axw_seq.rsp.data.size() != 0) begin
                `uvm_error("LB_RESET", $sformatf("axi_write burst in its gap: returned with %0d beats, expected none", axw_seq.rsp.data.size()))
            end

            apb_seq.it       = apb_item_t::type_id::create("it");
            apb_seq.it.write = 1'b0;
            apb_seq.it.addr  = 'h40;
            apb_seq.clk_vif  = clk_vif;
            run_case(apb_seq, apb_master.sqr, "apb read in its setup phase");
            want_pin(3, 1, "psel", "apb read in its setup phase");
            if (apb_seq.it.slverr !== 1'b1) begin
                `uvm_error("LB_RESET", "apb read in its setup phase: completed with slverr 0, so a register read would report UVM_IS_OK")
            end
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (resets != 5) `uvm_error("LB_RESET", $sformatf("%0d resets seen, expected 5", resets))
        endfunction
    endclass : lb_reset_held_test
