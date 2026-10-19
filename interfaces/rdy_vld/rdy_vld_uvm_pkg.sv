`ifndef RDY_VLD_UVM_PKG_SV
`define RDY_VLD_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for rdy_vld_if. The role (a2c_role_e) names the side of the
// interface the agent plays. Pin timing follows a2c_clk_if: drive at
// drive_edge(), sample at sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver puts
// each beat on both lanes at one drive point, and each lane drops vld once
// its own beat has transferred; the next beat starts when both have. The
// A2C_DST driver gives both lanes the same rdy. On the A2C_DST role
// model_cmp compares the beats of the two lanes in order. What the DUT
// produces that is not compared:
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

    class rdy_vld_driver #(type data_t = logic) extends uvm_driver #(rdy_vld_item#(data_t));
        typedef virtual rdy_vld_if #(.data_t(data_t)) vif_t;

        rdy_vld_config#(data_t) cfg;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;

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
            for (int l = 0; l < lanes; l++) lane[l].vld <= vld;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back items go out on consecutive clocks, and vld drops on the
        // first drive point with no item.
        protected virtual task run_src();
            for (int l = 0; l < lanes; l++) begin
                lane[l].vld  <= 1'b0;
                lane[l].data <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
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
                    lane[l].vld  <= 1'b1;
                    lane[l].data <= req.data;
                end
                wait_transfer();
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last lane's beat transferred,
        // which is the rising edge before it. A lane whose beat has
        // transferred holds vld low from the next drive point on.
        protected task wait_transfer();
            bit          pending[2];
            int unsigned left = lanes;
            for (int l = 0; l < lanes; l++) pending[l] = 1'b1;
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (pending[l] && lane[l].rdy === 1'b1) begin
                        pending[l] = 1'b0;
                        left--;
                    end
                end
                cfg.clk_vif.drive_edge();
                if (left == 0) return;
                for (int l = 0; l < lanes; l++) begin
                    if (!pending[l]) lane[l].vld <= 1'b0;
                end
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

    class rdy_vld_monitor #(type data_t = logic) extends uvm_monitor;
        rdy_vld_config#(data_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual rdy_vld_if #(.data_t(data_t))      vif;
        uvm_analysis_port #(rdy_vld_item#(data_t)) ap;

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
                item = rdy_vld_item#(data_t)::type_id::create("item");
                item.data = data;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", data)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
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
