// Loopback tests of backpressure: false on rdy_vld and axi4_stream, the two
// types whose backpressure a port may turn off. Included in
// a2c_uvm_loopback_pkg after rdy_vld_lb_tests.svh and axi4_stream_lb_tests.svh.

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
