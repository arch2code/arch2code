`timescale 1ns/1ps

// Loopback tests of the interface agents and of a2c_uvm_pkg's transaction
// counter and error demoter, with no DUT: on each interface a src agent drives a dst
// agent, and a scoreboard matches what the dst agent's monitor reports against
// the items the test sent. run_loopback.sh builds this and runs every test.
package a2c_uvm_loopback_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;
    import rdy_vld_uvm_pkg::*;
    import axi4_stream_uvm_pkg::*;
    import raw_uvm_pkg::*;
    import status_uvm_pkg::*;

    typedef struct packed {
        logic [3:0]  tag;
        logic [19:0] value;
    } lb_data_t;

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

    typedef rdy_vld_agent #(.data_t(lb_data_t)) rv_agent_t;
    typedef rv_agent_t::item_t rv_item_t;
    typedef rv_agent_t::config_t rv_config_t;
    typedef virtual rdy_vld_if #(.data_t(lb_data_t)) rv_vif_t;

    typedef axi4_stream_agent #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis_agent_t;
    typedef axis_agent_t::item_t axis_item_t;
    typedef axis_agent_t::config_t axis_config_t;
    typedef virtual axi4_stream_if #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis_vif_t;

    typedef raw_agent #(.data_t(lb_data_t)) raw_agent_t;
    typedef raw_agent_t::item_t raw_item_t;
    typedef raw_agent_t::config_t raw_config_t;
    typedef virtual raw_if #(.data_t(lb_data_t)) raw_vif_t;

    typedef status_agent #(.data_t(lb_data_t)) st_agent_t;
    typedef st_agent_t::item_t st_item_t;
    typedef st_agent_t::config_t st_config_t;
    typedef virtual status_if #(.data_t(lb_data_t)) st_vif_t;

    virtual class lb_scoreboard_base extends uvm_component;
        int unsigned matched;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass : lb_scoreboard_base

    // Matches each reported item against the oldest one not yet matched. A
    // sequence adds an item to expected before the driver puts it on the
    // pins, so the item is waiting when the monitor reports it.
    class lb_scoreboard #(type ITEM = uvm_sequence_item) extends lb_scoreboard_base;
        uvm_analysis_imp #(ITEM, lb_scoreboard#(ITEM)) imp;
        ITEM         expected[$];
        // A raw monitor reports every clock, so before the first sent item it
        // reports the idle value and after the last it repeats that item.
        bit          free_running;

        `uvm_component_param_utils(lb_scoreboard#(ITEM))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            imp = new("imp", this);
        endfunction

        virtual function void write(ITEM t);
            if (expected.size() == 0) begin
                if (!free_running) begin
                    `uvm_error("LB_EXTRA", $sformatf("reported %s after every sent item matched", t.convert2string()))
                end
                return;
            end
            if (!t.compare(expected[0])) begin
                if (free_running && matched == 0) return;
                `uvm_error("LB_MISMATCH", $sformatf("item %0d: reported %s, sent %s", matched, t.convert2string(),
                                                    expected[0].convert2string()))
            end
            void'(expected.pop_front());
            matched++;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            if (expected.size() != 0) begin
                `uvm_error("LB_MISSING", $sformatf("%0d sent items never reported, %0d matched", expected.size(), matched))
            end
        endfunction
    endclass : lb_scoreboard

    class lb_base_test extends uvm_test;
        virtual a2c_clk_if clk_vif;
        int unsigned       n_items = 400;

        `uvm_component_utils(lb_base_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk", clk_vif)) begin
                `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk'")
            end
        endfunction

        // Waits until the scoreboard has matched target items, or fails after
        // max_clocks.
        task wait_matched(lb_scoreboard_base sb, int unsigned target, int unsigned max_clocks);
            int unsigned clocks = 0;
            while (sb.matched < target && clocks < max_clocks) begin
                clk_vif.sample_edge();
                clocks++;
            end
            if (sb.matched < target) begin
                `uvm_error("LB_TIMEOUT", $sformatf("matched %0d of %0d items in %0d clocks", sb.matched, target, max_clocks))
            end
        endtask

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) begin
                `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
            end
        endfunction
    endclass : lb_base_test

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

    // Both dst agents set no_backpressure and ready_pct 0. Checks every beat
    // arrives and no beat stalls, so the dst drivers held ready high.
    class no_backpressure_test extends lb_base_test;
        rv_agent_t                  rv_src;
        rv_agent_t                  rv_dst;
        axis_agent_t                axis_src;
        axis_agent_t                axis_dst;
        lb_scoreboard#(rv_item_t)   rv_sb;
        lb_scoreboard#(axis_item_t) axis_sb;
        rv_vif_t                    rv_vif;
        axis_vif_t                  axis_vif;
        int unsigned                stalls;

        `uvm_component_utils(no_backpressure_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t   rv_cfg[2];
            axis_config_t axis_cfg[2];
            super.build_phase(phase);
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", rv_vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis", axis_vif)) `uvm_fatal("LB_CFG", "no virtual axi4_stream_if 'axis'")
            foreach (rv_cfg[i]) begin
                rv_cfg[i] = rv_config_t::type_id::create($sformatf("rv_cfg%0d", i));
                rv_cfg[i].vif       = rv_vif;
                rv_cfg[i].clk_vif   = clk_vif;
                rv_cfg[i].role      = i ? A2C_DST : A2C_SRC;
                rv_cfg[i].port_name = "rv";
                rv_cfg[i].no_backpressure = 1;
                rv_cfg[i].ready_pct = 0;
                axis_cfg[i] = axis_config_t::type_id::create($sformatf("axis_cfg%0d", i));
                axis_cfg[i].vif       = axis_vif;
                axis_cfg[i].clk_vif   = clk_vif;
                axis_cfg[i].role      = i ? A2C_DST : A2C_SRC;
                axis_cfg[i].port_name = "axis";
                axis_cfg[i].no_backpressure = 1;
                axis_cfg[i].ready_pct = 0;
            end
            uvm_config_db#(rv_config_t)::set(this, "rv_src", "cfg", rv_cfg[0]);
            uvm_config_db#(rv_config_t)::set(this, "rv_dst", "cfg", rv_cfg[1]);
            uvm_config_db#(axis_config_t)::set(this, "axis_src", "cfg", axis_cfg[0]);
            uvm_config_db#(axis_config_t)::set(this, "axis_dst", "cfg", axis_cfg[1]);
            rv_src   = rv_agent_t::type_id::create("rv_src", this);
            rv_dst   = rv_agent_t::type_id::create("rv_dst", this);
            axis_src = axis_agent_t::type_id::create("axis_src", this);
            axis_dst = axis_agent_t::type_id::create("axis_dst", this);
            rv_sb    = lb_scoreboard#(rv_item_t)::type_id::create("rv_sb", this);
            axis_sb  = lb_scoreboard#(axis_item_t)::type_id::create("axis_sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            rv_dst.mon.ap.connect(rv_sb.imp);
            axis_dst.mon.ap.connect(axis_sb.imp);
        endfunction

        virtual task run_phase(uvm_phase phase);
            rv_seq   rv_s   = rv_seq::type_id::create("rv_s");
            axis_seq axis_s = axis_seq::type_id::create("axis_s");
            phase.raise_objection(this);
            rv_s.n         = n_items;
            rv_s.max_gap   = 2;
            rv_s.sb        = rv_sb;
            axis_s.n       = n_items;
            axis_s.sb      = axis_sb;
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (rv_vif.vld === 1'b1 && rv_vif.rdy !== 1'b1) stalls++;
                    if (axis_vif.tvalid === 1'b1 && axis_vif.tready !== 1'b1) stalls++;
                end
            join_none
            fork
                rv_s.start(rv_src.sqr);
                axis_s.start(axis_src.sqr);
            join
            wait_matched(rv_sb, n_items, 10 * n_items);
            wait_matched(axis_sb, n_items, 10 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d rdy_vld and %0d axi4_stream beats, %0d stalled clocks",
                                            rv_sb.matched, axis_sb.matched, stalls), UVM_NONE)
            if (stalls != 0) `uvm_error("LB_STALL", "a backpressure: false dst driver held ready low")
        endfunction
    endclass : no_backpressure_test

    // Passive backpressure: false monitors watch pins the test drives by
    // hand. On each interface the source stalls, drops valid, stalls twice
    // more, changes the payload while stalled and then transfers. Expects
    // three A2C_STALL and two A2C_HOLD reports per interface, demoted to
    // info, and the one transferred beat reported.
    class monitor_checks_test extends lb_base_test;
        rv_agent_t                  rv_obs;
        axis_agent_t                axis_obs;
        lb_scoreboard#(rv_item_t)   rv_sb;
        lb_scoreboard#(axis_item_t) axis_sb;
        rv_vif_t                    rv_vif;
        axis_vif_t                  axis_vif;

        `uvm_component_utils(monitor_checks_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t   rv_cfg;
            axis_config_t axis_cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", rv_vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis", axis_vif)) `uvm_fatal("LB_CFG", "no virtual axi4_stream_if 'axis'")
            rv_cfg = rv_config_t::type_id::create("rv_cfg");
            rv_cfg.vif             = rv_vif;
            rv_cfg.clk_vif         = clk_vif;
            rv_cfg.is_active       = UVM_PASSIVE;
            rv_cfg.role            = A2C_DST;
            rv_cfg.port_name       = "rv";
            rv_cfg.no_backpressure = 1;
            axis_cfg = axis_config_t::type_id::create("axis_cfg");
            axis_cfg.vif             = axis_vif;
            axis_cfg.clk_vif         = clk_vif;
            axis_cfg.is_active       = UVM_PASSIVE;
            axis_cfg.role            = A2C_DST;
            axis_cfg.port_name       = "axis";
            axis_cfg.no_backpressure = 1;
            uvm_config_db#(rv_config_t)::set(this, "rv_obs", "cfg", rv_cfg);
            uvm_config_db#(axis_config_t)::set(this, "axis_obs", "cfg", axis_cfg);
            rv_obs   = rv_agent_t::type_id::create("rv_obs", this);
            axis_obs = axis_agent_t::type_id::create("axis_obs", this);
            rv_sb    = lb_scoreboard#(rv_item_t)::type_id::create("rv_sb", this);
            axis_sb  = lb_scoreboard#(axis_item_t)::type_id::create("axis_sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            rv_obs.mon.ap.connect(rv_sb.imp);
            axis_obs.mon.ap.connect(axis_sb.imp);
            rv_obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_STALL", UVM_INFO);
            rv_obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
            axis_obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_STALL", UVM_INFO);
            axis_obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
        endfunction

        // One clock per call: valid, payload and ready as the next rising
        // edge sees them.
        task drive(bit valid, int unsigned value, bit last, bit ready);
            rv_vif.vld      <= valid;
            rv_vif.data     <= lb_data_t'(value);
            rv_vif.rdy      <= ready;
            axis_vif.tvalid <= valid;
            axis_vif.tdata  <= lb_tdata_t'(value);
            axis_vif.tlast  <= last;
            axis_vif.tready <= ready;
            clk_vif.drive_edge();
        endtask

        virtual task run_phase(uvm_phase phase);
            rv_item_t   rv_it   = rv_item_t::type_id::create("rv_it");
            axis_item_t axis_it = axis_item_t::type_id::create("axis_it");
            phase.raise_objection(this);
            axis_vif.tid   <= '0;
            axis_vif.tdest <= '0;
            axis_vif.tuser <= '0;
            axis_vif.tstrb <= '1;
            axis_vif.tkeep <= '1;
            drive(0, 0, 0, 0);
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            rv_it.data     = lb_data_t'(3);
            axis_it.tdata  = lb_tdata_t'(3);
            axis_it.tlast  = 1;
            axis_it.tid    = '0;
            axis_it.tdest  = '0;
            axis_it.tuser  = '0;
            rv_sb.expected.push_back(rv_it);
            axis_sb.expected.push_back(axis_it);
            drive(1, 1, 0, 0);  // stall
            drive(0, 1, 0, 0);  // valid dropped
            drive(1, 2, 0, 0);  // stall
            drive(1, 3, 1, 0);  // stall, rdy_vld data and axi4_stream tdata and tlast changed
            drive(1, 3, 1, 1);  // transfer
            drive(0, 0, 0, 1);
            repeat (2) clk_vif.drive_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned stall = srv.get_id_count("A2C_STALL");
            int unsigned hold  = srv.get_id_count("A2C_HOLD");
            `uvm_info("LB_STATS", $sformatf("%0d A2C_STALL, %0d A2C_HOLD, %0d and %0d beats reported",
                                            stall, hold, rv_sb.matched, axis_sb.matched), UVM_NONE)
            if (stall != 6) `uvm_error("LB_CHECKS", $sformatf("expected 6 A2C_STALL reports, got %0d", stall))
            if (hold != 4) `uvm_error("LB_CHECKS", $sformatf("expected 4 A2C_HOLD reports, got %0d", hold))
        endfunction
    endclass : monitor_checks_test

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

    // A rdy_vld src agent drives a dst agent whose monitor feeds an
    // a2c_txn_counter. The test sends n_items beats and waits for
    // n_items + expect_delta, unless skip_wait is set. With second_wait set
    // it then sends n_items more and waits for them with the count right. An
    // a2c_error_demoter catches every A2C_TXN_COUNT, and the test checks how
    // many the counter raised by the end of the first wait, by the end of the
    // last wait and by the end of check_phase. With the expected count
    // right, none is raised.
    class txn_count_clean_test extends lb_base_test;
        rv_agent_t                     src;
        rv_agent_t                     dst;
        lb_scoreboard#(rv_item_t)      sb;
        a2c_txn_counter #(rv_item_t)   counter;
        a2c_error_demoter              demoter;
        int                            expect_delta = 0;
        bit                            skip_wait = 0;
        bit                            second_wait = 0;
        int unsigned                   want[3] = '{0, 0, 0};
        int unsigned                   got[3];

        `uvm_component_utils(txn_count_clean_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t src_cfg;
            rv_config_t dst_cfg;
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
            dst_cfg.ready_pct = 50;
            uvm_config_db#(rv_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(rv_config_t)::set(this, "dst", "cfg", dst_cfg);
            src   = rv_agent_t::type_id::create("src", this);
            dst   = rv_agent_t::type_id::create("dst", this);
            sb    = lb_scoreboard#(rv_item_t)::type_id::create("sb", this);
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv";
            demoter = a2c_error_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
            dst.mon.ap.connect(counter.imp);
        endfunction

        task send_and_wait(int unsigned expected);
            rv_seq seq = rv_seq::type_id::create("seq");
            seq.n       = n_items;
            seq.max_gap = 2;
            seq.sb      = sb;
            counter.expect_beats(expected);
            seq.start(src.sqr);
            if (!skip_wait) counter.wait_for_count(clk_vif, 20 * n_items, 50);
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            send_and_wait(n_items + expect_delta);
            got[0] = demoter.demoted;
            if (second_wait) send_and_wait(n_items);
            got[1] = demoter.demoted;
            // Lets a beat still in flight arrive before check_phase.
            repeat (50) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        // report_phase follows check_phase, so the counter's
        // check_phase reports are counted by now.
        virtual function void report_phase(uvm_phase phase);
            got[2] = demoter.demoted;
            `uvm_info("LB_STATS", $sformatf("%0d beats, first wait expected %0d; A2C_TXN_COUNT by the first wait %0d, by the last %0d, by check_phase %0d",
                                            sb.matched, int'(n_items) + expect_delta, got[0], got[1], got[2]), UVM_NONE)
            if (got != want) begin
                `uvm_error("LB_TXN_COUNT", $sformatf("expected %0d, %0d and %0d A2C_TXN_COUNT by the first wait, the last wait and check_phase",
                                                 want[0], want[1], want[2]))
            end
            super.report_phase(phase);
        endfunction
    endclass : txn_count_clean_test

    // Two beats more expected than sent: the wait reports them at its
    // deadline, and check_phase does not report them again.
    class txn_count_missing_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_missing_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = 2;
            want         = '{1, 1, 1};
        endfunction
    endclass : txn_count_missing_test

    // One beat fewer expected than sent: the wait reports the extra beat
    // at the end of its quiet window, and check_phase does not report it
    // again.
    class txn_count_extra_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = -1;
            want         = '{1, 1, 1};
        endfunction
    endclass : txn_count_extra_test

    // One beat fewer expected than sent and no wait: check_phase reports
    // the extra beat.
    class txn_count_unwaited_extra_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_unwaited_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = -1;
            skip_wait    = 1;
            want         = '{0, 0, 1};
        endfunction
    endclass : txn_count_unwaited_extra_test

    // A failing wait, two beats short, then a passing one on the same
    // counter: only the first reports.
    class txn_count_twice_test extends txn_count_clean_test;
        `uvm_component_utils(txn_count_twice_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            expect_delta = 2;
            second_wait  = 1;
            want         = '{1, 1, 1};
        endfunction
    endclass : txn_count_twice_test

endpackage : a2c_uvm_loopback_pkg

module a2c_uvm_loopback_tb;

    import uvm_pkg::*;
    import a2c_uvm_loopback_pkg::*;

    bit clk;
    bit rst_n;

    always #5 clk = ~clk;

    // Released on a falling edge, so no driver sees it change at the rising
    // edge it samples.
    initial begin
        repeat (5) @(negedge clk);
        rst_n = 1'b1;
    end

    a2c_clk_if clk_if(.clk(clk), .rst_n(rst_n));
    rdy_vld_if #(.data_t(lb_data_t)) rv();
    axi4_stream_if #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis();
    raw_if #(.data_t(lb_data_t)) raw();
    status_if #(.data_t(lb_data_t)) st();

    initial begin
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk", clk_if);
        uvm_config_db#(rv_vif_t)::set(null, "uvm_test_top", "rv", rv);
        uvm_config_db#(axis_vif_t)::set(null, "uvm_test_top", "axis", axis);
        uvm_config_db#(raw_vif_t)::set(null, "uvm_test_top", "raw", raw);
        uvm_config_db#(st_vif_t)::set(null, "uvm_test_top", "st", st);
        run_test();
    end

endmodule : a2c_uvm_loopback_tb
