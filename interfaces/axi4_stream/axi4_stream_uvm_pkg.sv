`ifndef AXI4_STREAM_UVM_PKG_SV
`define AXI4_STREAM_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for axi4_stream_if. The role (a2c_role_e) names the side of the
// interface the agent plays. The type parameters and their defaults are the
// interface's, and tstrb and tkeep take one bit per tdata byte as the
// interface sizes them. Pin timing follows a2c_clk_if: drive at drive_edge(),
// sample at sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver puts
// each beat on both lanes at one drive point, and each lane drops tvalid
// once its own beat has transferred; the next beat starts when both have.
// The A2C_DST driver gives both lanes the same tready. On the A2C_DST role
// model_cmp compares the beats of the two lanes in order, every field
// do_compare covers. What the DUT produces that is not compared:
//   DUT dst port, A2C_SRC agent: `tready` timing
//   DUT src port, A2C_DST agent: `tvalid` timing
package axi4_stream_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class axi4_stream_item #(type tdata_t = logic [31:0], type tid_t = logic [7:0],
                             type tdest_t = logic [7:0], type tuser_t = logic) extends uvm_sequence_item;
        typedef logic [$bits(tdata_t)/8-1:0] tstrb_t;

        rand tdata_t tdata;
        rand bit     tlast;
        rand tid_t   tid;
        rand tdest_t tdest;
        rand tuser_t tuser;
        // All ones unless a sequence sets them.
        tstrb_t      tstrb;
        tstrb_t      tkeep;
        // Idle clocks (tvalid low) the src driver inserts before this beat.
        int unsigned gap;

        `uvm_object_param_utils(axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t))

        function new(string name = "axi4_stream_item");
            super.new(name);
            tstrb = '1;
            tkeep = '1;
        endfunction

        virtual function void do_copy(uvm_object rhs);
            axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            tdata = rhs_.tdata;
            tlast = rhs_.tlast;
            tid   = rhs_.tid;
            tdest = rhs_.tdest;
            tuser = rhs_.tuser;
            tstrb = rhs_.tstrb;
            tkeep = rhs_.tkeep;
            gap   = rhs_.gap;
        endfunction

        // gap is stimulus timing, not payload, so it takes no part in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (tdata === rhs_.tdata) && (tlast === rhs_.tlast)
                && (tid === rhs_.tid) && (tdest === rhs_.tdest) && (tuser === rhs_.tuser)
                && (tstrb === rhs_.tstrb) && (tkeep === rhs_.tkeep);
        endfunction

        virtual function string convert2string();
            return $sformatf("tdata=%p tlast=%0d tid=%0h tdest=%0h tuser=%0h tstrb=%0h tkeep=%0h",
                             tdata, tlast, tid, tdest, tuser, tstrb, tkeep);
        endfunction
    endclass : axi4_stream_item

    class axi4_stream_config #(type tdata_t = logic [31:0], type tid_t = logic [7:0],
                               type tdest_t = logic [7:0], type tuser_t = logic) extends uvm_object;
        virtual axi4_stream_if #(.tdata_t(tdata_t), .tid_t(tid_t), .tdest_t(tdest_t), .tuser_t(tuser_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise.
        virtual axi4_stream_if #(.tdata_t(tdata_t), .tid_t(tid_t), .tdest_t(tdest_t), .tuser_t(tuser_t)) model_vif;
        virtual a2c_clk_if      clk_vif;
        uvm_active_passive_enum is_active = UVM_ACTIVE;
        a2c_role_e              role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                  port_name = "";
        // The interface declares backpressure: false, so the consumer must
        // never hold tready low while tvalid is high; the monitor reports it
        // if it does.
        bit                     no_backpressure = 0;
        // dst role: percentage of clocks with tready high.
        int unsigned            ready_pct = 100;

        `uvm_object_param_utils(axi4_stream_config#(tdata_t, tid_t, tdest_t, tuser_t))

        function new(string name = "axi4_stream_config");
            super.new(name);
        endfunction
    endclass : axi4_stream_config

    class axi4_stream_driver #(type tdata_t = logic [31:0], type tid_t = logic [7:0],
                               type tdest_t = logic [7:0], type tuser_t = logic)
            extends uvm_driver #(axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t));
        typedef virtual axi4_stream_if #(.tdata_t(tdata_t), .tid_t(tid_t), .tdest_t(tdest_t), .tuser_t(tuser_t)) vif_t;

        axi4_stream_config#(tdata_t, tid_t, tdest_t, tuser_t) cfg;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;

        `uvm_component_param_utils(axi4_stream_driver#(tdata_t, tid_t, tdest_t, tuser_t))

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

        protected function void drive_tvalid(bit tvalid);
            for (int l = 0; l < lanes; l++) lane[l].tvalid <= tvalid;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back items go out on consecutive clocks, and tvalid drops on
        // the first drive point with no item.
        protected virtual task run_src();
            for (int l = 0; l < lanes; l++) begin
                lane[l].tvalid <= 1'b0;
                lane[l].tdata  <= '0;
                lane[l].tlast  <= 1'b0;
                lane[l].tid    <= '0;
                lane[l].tdest  <= '0;
                lane[l].tuser  <= '0;
                lane[l].tstrb  <= '0;
                lane[l].tkeep  <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    drive_tvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    drive_tvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                for (int l = 0; l < lanes; l++) begin
                    lane[l].tvalid <= 1'b1;
                    lane[l].tdata  <= req.tdata;
                    lane[l].tlast  <= req.tlast;
                    lane[l].tid    <= req.tid;
                    lane[l].tdest  <= req.tdest;
                    lane[l].tuser  <= req.tuser;
                    lane[l].tstrb  <= req.tstrb;
                    lane[l].tkeep  <= req.tkeep;
                end
                wait_transfer();
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last lane's beat transferred,
        // which is the rising edge before it. A lane whose beat has
        // transferred holds tvalid low from the next drive point on.
        protected task wait_transfer();
            bit          pending[2];
            int unsigned left = lanes;
            for (int l = 0; l < lanes; l++) pending[l] = 1'b1;
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (pending[l] && lane[l].tready === 1'b1) begin
                        pending[l] = 1'b0;
                        left--;
                    end
                end
                cfg.clk_vif.drive_edge();
                if (left == 0) return;
                for (int l = 0; l < lanes; l++) begin
                    if (!pending[l]) lane[l].tvalid <= 1'b0;
                end
            end
        endtask

        // tready is driven from time 0, so a backpressure: false sink is
        // ready on the first clock out of reset. Such a sink never stalls, so
        // ready_pct does not apply to it.
        protected virtual task run_dst();
            bit ready;
            if (cfg.no_backpressure) begin
                for (int l = 0; l < lanes; l++) lane[l].tready <= 1'b1;
                return;
            end
            forever begin
                ready = ($urandom_range(99, 0) < cfg.ready_pct);
                for (int l = 0; l < lanes; l++) lane[l].tready <= ready;
                cfg.clk_vif.drive_edge();
            end
        endtask
    endclass : axi4_stream_driver

    class axi4_stream_monitor #(type tdata_t = logic [31:0], type tid_t = logic [7:0],
                                type tdest_t = logic [7:0], type tuser_t = logic) extends uvm_monitor;
        axi4_stream_config#(tdata_t, tid_t, tdest_t, tuser_t)                     cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual axi4_stream_if #(.tdata_t(tdata_t), .tid_t(tid_t), .tdest_t(tdest_t), .tuser_t(tuser_t)) vif;
        uvm_analysis_port #(axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t)) ap;

        `uvm_component_param_utils(axi4_stream_monitor#(tdata_t, tid_t, tdest_t, tuser_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t) item;
            axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t) held;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                item = null;
                if (vif.tvalid === 1'b1) begin
                    item = axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t)::type_id::create("item");
                    item.tdata = vif.tdata;
                    item.tlast = vif.tlast;
                    item.tid   = vif.tid;
                    item.tdest = vif.tdest;
                    item.tuser = vif.tuser;
                    item.tstrb = vif.tstrb;
                    item.tkeep = vif.tkeep;
                end
                // A stalled source must hold tvalid and the payload until the beat transfers.
                if (held != null && (item == null || !item.compare(held))) begin
                    string what = (item == null) ? "tvalid dropped" : "payload changed";
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before the stalled beat %s transferred", cfg.port_name,
                                                     what, held.convert2string()))
                end
                held = (item != null && vif.tready !== 1'b1) ? item : null;
                if (item == null) continue;
                if (vif.tready !== 1'b1) begin
                    if (cfg.no_backpressure) begin
                        `uvm_error("A2C_STALL", $sformatf("%s: tready is %b while tvalid is high on a backpressure: false interface",
                                                          cfg.port_name, vif.tready))
                    end
                    continue;
                end
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", item.tdata)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : axi4_stream_monitor

    class axi4_stream_agent #(type tdata_t = logic [31:0], type tid_t = logic [7:0],
                              type tdest_t = logic [7:0], type tuser_t = logic) extends uvm_agent;
        typedef axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t)   item_t;
        typedef axi4_stream_config#(tdata_t, tid_t, tdest_t, tuser_t) config_t;

        config_t                                               cfg;
        axi4_stream_driver#(tdata_t, tid_t, tdest_t, tuser_t)  drv;
        uvm_sequencer #(item_t)                                sqr;
        axi4_stream_monitor#(tdata_t, tid_t, tdest_t, tuser_t) mon;
        // Mode B only. model_cmp exists on the A2C_DST role.
        axi4_stream_monitor#(tdata_t, tid_t, tdest_t, tuser_t) model_mon;
        a2c_in_order_comparator #(item_t)                      model_cmp;

        `uvm_component_param_utils(axi4_stream_agent#(tdata_t, tid_t, tdest_t, tuser_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi4_stream_agent has no cfg")
            end
            mon = axi4_stream_monitor#(tdata_t, tid_t, tdest_t, tuser_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = axi4_stream_monitor#(tdata_t, tid_t, tdest_t, tuser_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                if (cfg.role == A2C_DST) model_cmp = a2c_in_order_comparator#(item_t)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active == UVM_ACTIVE) begin
                drv = axi4_stream_driver#(tdata_t, tid_t, tdest_t, tuser_t)::type_id::create("drv", this);
                drv.cfg = cfg;
                if (cfg.role == A2C_SRC) begin
                    sqr = uvm_sequencer#(item_t)::type_id::create("sqr", this);
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
    endclass : axi4_stream_agent

endpackage : axi4_stream_uvm_pkg

`endif // AXI4_STREAM_UVM_PKG_SV
