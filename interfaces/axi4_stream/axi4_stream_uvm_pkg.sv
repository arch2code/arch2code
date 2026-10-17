`ifndef AXI4_STREAM_UVM_PKG_SV
`define AXI4_STREAM_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for axi4_stream_if. The role (a2c_role_e) names the side of the
// interface the agent plays. The type parameters and their defaults are the
// interface's, and tstrb and tkeep take one bit per tdata byte as the
// interface sizes them. Pin timing follows a2c_clk_if: drive at drive_edge(),
// sample at sample_edge().
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
        axi4_stream_config#(tdata_t, tid_t, tdest_t, tuser_t) cfg;

        `uvm_component_param_utils(axi4_stream_driver#(tdata_t, tid_t, tdest_t, tuser_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            if (cfg.role == A2C_SRC) begin
                run_src();
            end else begin
                run_dst();
            end
        endtask

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back items go out on consecutive clocks, and tvalid drops on
        // the first drive point with no item.
        protected virtual task run_src();
            cfg.vif.tvalid <= 1'b0;
            cfg.vif.tdata  <= '0;
            cfg.vif.tlast  <= 1'b0;
            cfg.vif.tid    <= '0;
            cfg.vif.tdest  <= '0;
            cfg.vif.tuser  <= '0;
            cfg.vif.tstrb  <= '0;
            cfg.vif.tkeep  <= '0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.tvalid <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.tvalid <= 1'b0;
                    cfg.clk_vif.drive_edge();
                end
                cfg.vif.tvalid <= 1'b1;
                cfg.vif.tdata  <= req.tdata;
                cfg.vif.tlast  <= req.tlast;
                cfg.vif.tid    <= req.tid;
                cfg.vif.tdest  <= req.tdest;
                cfg.vif.tuser  <= req.tuser;
                cfg.vif.tstrb  <= req.tstrb;
                cfg.vif.tkeep  <= req.tkeep;
                do cfg.clk_vif.sample_edge(); while (cfg.vif.tready !== 1'b1);
                // The beat transfers at the rising edge before this drive point.
                cfg.clk_vif.drive_edge();
                seq_item_port.item_done();
            end
        endtask

        // tready is driven from time 0, so a backpressure: false sink is
        // ready on the first clock out of reset. Such a sink never stalls, so
        // ready_pct does not apply to it.
        protected virtual task run_dst();
            if (cfg.no_backpressure) begin
                cfg.vif.tready <= 1'b1;
                return;
            end
            forever begin
                cfg.vif.tready <= ($urandom_range(99, 0) < cfg.ready_pct);
                cfg.clk_vif.drive_edge();
            end
        endtask
    endclass : axi4_stream_driver

    class axi4_stream_monitor #(type tdata_t = logic [31:0], type tid_t = logic [7:0],
                                type tdest_t = logic [7:0], type tuser_t = logic) extends uvm_monitor;
        axi4_stream_config#(tdata_t, tid_t, tdest_t, tuser_t)                     cfg;
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
                if (cfg.vif.tvalid === 1'b1) begin
                    item = axi4_stream_item#(tdata_t, tid_t, tdest_t, tuser_t)::type_id::create("item");
                    item.tdata = cfg.vif.tdata;
                    item.tlast = cfg.vif.tlast;
                    item.tid   = cfg.vif.tid;
                    item.tdest = cfg.vif.tdest;
                    item.tuser = cfg.vif.tuser;
                    item.tstrb = cfg.vif.tstrb;
                    item.tkeep = cfg.vif.tkeep;
                end
                // A stalled source must hold tvalid and the payload until the beat transfers.
                if (held != null && (item == null || !item.compare(held))) begin
                    string what = (item == null) ? "tvalid dropped" : "payload changed";
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before the stalled beat %s transferred", cfg.port_name,
                                                     what, held.convert2string()))
                end
                held = (item != null && cfg.vif.tready !== 1'b1) ? item : null;
                if (item == null) continue;
                if (cfg.vif.tready !== 1'b1) begin
                    if (cfg.no_backpressure) begin
                        `uvm_error("A2C_STALL", $sformatf("%s: tready is %b while tvalid is high on a backpressure: false interface",
                                                          cfg.port_name, cfg.vif.tready))
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
        endfunction
    endclass : axi4_stream_agent

endpackage : axi4_stream_uvm_pkg

`endif // AXI4_STREAM_UVM_PKG_SV
