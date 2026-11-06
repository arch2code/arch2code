`ifndef RDY_VLD_UVM_PKG_SV
`define RDY_VLD_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for rdy_vld_if. The role (a2c_role_e) names the side of the
// interface the agent plays. Pin timing follows a2c_clk_if: drive at
// drive_edge(), sample at sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver puts
// each beat on both lanes at one drive point, and each lane drops vld once its
// own beat has transferred; the next beat starts when both have. A lane of the
// A2C_SRC driver that trails the other by lane_skew_cycles clocks, or stalls,
// is declared dead as for the AXI masters (a2c_lane_watchdog), and the other
// lane serves the sequence alone. The A2C_DST driver gives both lanes the same
// rdy. On the A2C_DST role model_cmp compares the beats of the two lanes in
// order. What the DUT produces that is not compared:
//   DUT dst port, A2C_SRC agent: `rdy` timing
//   DUT src port, A2C_DST agent: `vld` timing
package rdy_vld_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class rdy_vld_item #(type data_t = logic) extends uvm_sequence_item;
        rand data_t  data;
        // Idle clocks (vld low) the src driver inserts before this beat.
        int unsigned gap;

        `uvm_object_param_utils(rdy_vld_item#(data_t))

        function new(string name = "rdy_vld_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            rdy_vld_item#(data_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            data = rhs_.data;
            gap  = rhs_.gap;
        endfunction

        // gap is stimulus timing, not payload, so it takes no part in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            rdy_vld_item#(data_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", data);
        endfunction
    endclass : rdy_vld_item

    class rdy_vld_config #(type data_t = logic) extends uvm_object;
        virtual rdy_vld_if #(.data_t(data_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise.
        virtual rdy_vld_if #(.data_t(data_t)) model_vif;
        virtual a2c_clk_if                    clk_vif;
        uvm_active_passive_enum               is_active = UVM_ACTIVE;
        a2c_role_e                            role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                                port_name = "";
        // The interface declares backpressure: false, so the consumer must
        // never hold rdy low while vld is high; the monitor reports it if it does.
        bit                                   no_backpressure = 0;
        // dst role: percentage of clocks with rdy high. With burst set, rdy
        // holds each level for a run of 1 to burst_max clocks, and this is the
        // percentage of runs that are high.
        int unsigned                          ready_pct = 100;
        bit                                   burst = 0;
        int unsigned                          burst_max = 8;

        `uvm_object_param_utils(rdy_vld_config#(data_t))

        function new(string name = "rdy_vld_config");
            super.new(name);
        endfunction
    endclass : rdy_vld_config

    class rdy_vld_driver #(type data_t = logic) extends uvm_driver #(rdy_vld_item#(data_t))
        implements a2c_lane_waits;
        typedef virtual rdy_vld_if #(.data_t(data_t)) vif_t;

        rdy_vld_config#(data_t) cfg;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        // src role: bounds how long one lane may trail the other and how
        // long the lanes may stall in Mode B, and keeps which lanes are
        // dead.
        a2c_lane_watchdog      wd;

        `uvm_component_param_utils(rdy_vld_driver#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            lane[A2C_DUT_LANE] = cfg.vif;
            lane[A2C_MODEL_LANE] = cfg.model_vif;
            lanes = (cfg.model_vif != null) ? 2 : 1;
            if (cfg.role == A2C_SRC) begin
                run_src();
            end else begin
                run_dst();
            end
        endtask

        protected function void drive_vld(bit vld);
            for (int l = 0; l < lanes; l++) if (!wd.dead[l]) lane[l].vld <= vld;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back items go out on consecutive clocks, and vld drops on the
        // first drive point with no item.
        protected virtual task run_src();
            wd = new(this, cfg.port_name, lanes, "item", "every open and later item completes at once");
            wd.configure(cfg.clk_vif);
            for (int l = 0; l < lanes; l++) begin
                lane[l].vld  <= 1'b0;
                lane[l].data <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            if (lanes == 2) begin
                fork
                    release_dead();
                join_none
            end
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    drive_vld(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    drive_vld(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                for (int l = 0; l < lanes; l++) begin
                    if (wd.dead[l]) continue;
                    lane[l].vld  <= 1'b1;
                    lane[l].data <= req.data;
                end
                wait_transfer();
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last live lane's beat
        // transferred, which is the rising edge before it. A lane whose beat
        // has transferred holds vld low from the next drive point on. In Mode
        // B wd bounds how long one lane may trail the other and how long the
        // lanes may stall (a2c_lane_watchdog), and a lane it declares dead
        // drops out of the wait.
        protected task wait_transfer();
            bit    pending[2];
            bit    took[2];
            bit    finished[2];
            wd.begin_item();
            for (int l = 0; l < lanes; l++) pending[l] = !wd.dead[l];
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    took[l]     = pending[l] && lane[l].rdy === 1'b1;
                    pending[l] &= !took[l];
                    finished[l] |= took[l];
                end
                wd.step(took, pending);
                cfg.clk_vif.drive_edge();
                if (!pending[A2C_DUT_LANE] && !pending[A2C_MODEL_LANE]) return;
                for (int l = 0; l < lanes; l++) begin
                    if (finished[l]) lane[l].vld <= 1'b0;
                end
            end
        endtask

        virtual function string waiting_for(a2c_lane_e l);
            return $sformatf("the transfer of %p", req.data);
        endfunction

        // Mode B: a dead lane keeps an asserted vld and its payload until
        // that transfer happens, as the protocol requires, and drops vld at
        // the drive point after it. No later item drives the lane.
        protected task release_dead();
            bit took[2];
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < 2; l++) took[l] = wd.dead[l] && lane[l].vld === 1'b1 && lane[l].rdy === 1'b1;
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < 2; l++) if (took[l]) lane[l].vld <= 1'b0;
            end
        endtask

        // rdy is driven from time 0, so a backpressure: false sink is ready
        // on the first clock out of reset. Such a sink never stalls, so
        // ready_pct and burst do not apply to it.
        protected virtual task run_dst();
            bit          ready;
            int unsigned run;
            if (cfg.no_backpressure) begin
                for (int l = 0; l < lanes; l++) lane[l].rdy <= 1'b1;
                return;
            end
            forever begin
                ready = ($urandom_range(99, 0) < cfg.ready_pct);
                run   = cfg.burst ? $urandom_range(cfg.burst_max, 1) : 1;
                repeat (run) begin
                    for (int l = 0; l < lanes; l++) lane[l].rdy <= ready;
                    cfg.clk_vif.drive_edge();
                end
            end
        endtask
    endclass : rdy_vld_driver

    class rdy_vld_monitor #(type data_t = logic) extends uvm_monitor implements a2c_flow_counts;
        rdy_vld_config#(data_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual rdy_vld_if #(.data_t(data_t))      vif;
        uvm_analysis_port #(rdy_vld_item#(data_t)) ap;

        // The counts a2c_rt_checker reads (a2c_flow_counts), from the reset release.
        protected longint unsigned n_samples;
        protected longint unsigned n_valid;
        protected longint unsigned n_ready;
        protected longint unsigned n_transfers;

        `uvm_component_param_utils(rdy_vld_monitor#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            logic vld;
            logic rdy;
            data_t data;
            data_t held;
            bit    stalled = 0;
            rdy_vld_item#(data_t) item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                vld  = vif.vld;
                rdy  = vif.rdy;
                data = vif.data;
                n_samples++;
                n_valid     += (vld === 1'b1);
                n_ready     += (rdy === 1'b1);
                n_transfers += (vld === 1'b1 && rdy === 1'b1);
                // A stalled source must hold vld and data until the beat transfers.
                if (stalled && (vld !== 1'b1 || data !== held)) begin
                    string what = (vld !== 1'b1) ? "vld dropped" : "data changed";
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before the stalled beat %h transferred", cfg.port_name,
                                                     what, held))
                end
                stalled = (vld === 1'b1 && rdy !== 1'b1);
                held    = data;
                // X/Z checks only fire on a 4-state boundary. Across a 2-state
                // SystemC boundary an X or Z from the DUT arrives as 0.
                if ($isunknown(vld)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: vld is %b after reset release", cfg.port_name, vld))
                    continue;
                end
                if (vld !== 1'b1) continue;
                if ($isunknown(data)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: data has X or Z while vld is high: %h", cfg.port_name, data))
                end
                if (rdy !== 1'b1) begin
                    if (cfg.no_backpressure) begin
                        `uvm_error("A2C_STALL", $sformatf("%s: rdy is %b while vld is high on a backpressure: false interface", cfg.port_name, rdy))
                    end
                    continue;
                end
                // Each transfer counts for the joint stall rule (a2c_joint_watch).
                a2c_joint_watch::handshake();
                item = rdy_vld_item#(data_t)::type_id::create("item");
                item.data = data;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", data)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask

        virtual function void flow_counts(output longint unsigned samples, output longint unsigned valid,
                                          output longint unsigned ready, output longint unsigned transfers);
            samples   = n_samples;
            valid     = n_valid;
            ready     = n_ready;
            transfers = n_transfers;
        endfunction

        virtual function a2c_clk_vif_t flow_clock();
            return cfg.clk_vif;
        endfunction

        virtual function string flow_port();
            return cfg.port_name;
        endfunction
    endclass : rdy_vld_monitor

    class rdy_vld_agent #(type data_t = logic) extends uvm_agent;
        typedef rdy_vld_item#(data_t)   item_t;
        typedef rdy_vld_config#(data_t) config_t;

        rdy_vld_config#(data_t)                cfg;
        rdy_vld_driver#(data_t)                drv;
        uvm_sequencer #(rdy_vld_item#(data_t)) sqr;
        rdy_vld_monitor#(data_t)               mon;
        // Mode B only. model_cmp exists on the A2C_DST role.
        rdy_vld_monitor#(data_t)               model_mon;
        a2c_in_order_comparator #(item_t)      model_cmp;

        `uvm_component_param_utils(rdy_vld_agent#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(rdy_vld_config#(data_t))::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "rdy_vld_agent has no cfg")
            end
            if (cfg.burst && cfg.burst_max == 0) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: burst ready needs burst_max of 1 or more", cfg.port_name))
            end
            mon = rdy_vld_monitor#(data_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = rdy_vld_monitor#(data_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                if (cfg.role == A2C_DST) model_cmp = a2c_in_order_comparator#(item_t)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active == UVM_ACTIVE) begin
                drv = rdy_vld_driver#(data_t)::type_id::create("drv", this);
                drv.cfg = cfg;
                if (cfg.role == A2C_SRC) begin
                    sqr = uvm_sequencer#(rdy_vld_item#(data_t))::type_id::create("sqr", this);
                end
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
            end
        endfunction
    endclass : rdy_vld_agent

endpackage : rdy_vld_uvm_pkg

`endif // RDY_VLD_UVM_PKG_SV
