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
