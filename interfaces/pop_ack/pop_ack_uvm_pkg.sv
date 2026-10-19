`ifndef POP_ACK_UVM_PKG_SV
`define POP_ACK_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for pop_ack_if. A transfer is a clock with pop and ack both high;
// rdata is valid with ack, and pop still high on the next clock is a new
// pop. The A2C_SRC driver pops once per sequence item and writes the rdata it
// gets back into that item before item_done(). The A2C_DST driver is a
// reactive responder: for each pop it samples it takes one item from its
// sequencer and drives ack and the item's rdata after the item's delay. The
// agent starts pop_ack_responder_seq on that sequencer as its run_phase
// default_sequence; a test replaces it with a uvm_config_db set from higher
// in the hierarchy or with a factory override. Pin timing follows
// a2c_clk_if: drive at drive_edge(), sample at sample_edge().
package pop_ack_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class pop_ack_item #(type rdata_t = logic) extends uvm_sequence_item;
        rand rdata_t rdata;
        // src role: idle clocks (pop low) the driver inserts before this pop.
        int unsigned gap;
        // dst role: extra clocks the driver waits after it samples the pop
        // before it raises ack.
        int unsigned delay;

        `uvm_object_param_utils(pop_ack_item#(rdata_t))

        function new(string name = "pop_ack_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            pop_ack_item#(rdata_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            rdata = rhs_.rdata;
            gap   = rhs_.gap;
            delay = rhs_.delay;
        endfunction

        // gap and delay are stimulus timing, not payload, so they take no part
        // in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            pop_ack_item#(rdata_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (rdata === rhs_.rdata);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", rdata);
        endfunction
    endclass : pop_ack_item

    class pop_ack_config #(type rdata_t = logic) extends uvm_object;
        virtual pop_ack_if #(.rdata_t(rdata_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise. The agent has no
        // Mode B operations yet and stops with A2C_CFG when it is set.
        virtual pop_ack_if #(.rdata_t(rdata_t)) model_vif;
        virtual a2c_clk_if                      clk_vif;
        uvm_active_passive_enum                 is_active = UVM_ACTIVE;
        a2c_role_e                              role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                                  port_name = "";

        `uvm_object_param_utils(pop_ack_config#(rdata_t))

        function new(string name = "pop_ack_config");
            super.new(name);
        endfunction
    endclass : pop_ack_config

    // The default A2C_DST responder: one item per pop, with random rdata and
    // no delay. A replacement extends this class and overrides respond(), or
    // replaces body().
    class pop_ack_responder_seq #(type rdata_t = logic) extends uvm_sequence #(pop_ack_item#(rdata_t));
        `uvm_object_param_utils(pop_ack_responder_seq#(rdata_t))

        function new(string name = "pop_ack_responder_seq");
            super.new(name);
        endfunction

        // Sets rsp.rdata and rsp.delay for the next pop.
        virtual function void respond(pop_ack_item#(rdata_t) rsp);
            if (!rsp.randomize()) `uvm_fatal("A2C_RAND", "pop_ack response randomize failed")
            rsp.delay = 0;
        endfunction

        virtual task body();
            pop_ack_item#(rdata_t) rsp;
            forever begin
                rsp = pop_ack_item#(rdata_t)::type_id::create("rsp");
                start_item(rsp);
                respond(rsp);
                finish_item(rsp);
            end
        endtask
    endclass : pop_ack_responder_seq

    class pop_ack_driver #(type rdata_t = logic) extends uvm_driver #(pop_ack_item#(rdata_t));
        pop_ack_config#(rdata_t) cfg;

        `uvm_component_param_utils(pop_ack_driver#(rdata_t))

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
        // back-to-back pops go out on consecutive clocks, and pop drops on
        // the first drive point with no item.
        protected virtual task run_src();
            cfg.vif.pop <= 1'b0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.pop <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.pop <= 1'b0;
                    cfg.clk_vif.drive_edge();
                end
                cfg.vif.pop <= 1'b1;
                do cfg.clk_vif.sample_edge(); while (cfg.vif.ack !== 1'b1);
                req.rdata = cfg.vif.rdata;
                // The transfer happens at the rising edge before this drive point.
                cfg.clk_vif.drive_edge();
                seq_item_port.item_done();
            end
        endtask

        // ack and rdata are driven for one clock per transfer, and rise only
        // after pop has been sampled, so with no delay a transfer takes two
        // clocks. rdata is zero while ack is low.
        protected virtual task run_dst();
            cfg.vif.ack   <= 1'b0;
            cfg.vif.rdata <= '0;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (cfg.vif.pop !== 1'b1) continue;
                seq_item_port.get_next_item(req);
                repeat (req.delay) cfg.clk_vif.drive_edge();
                cfg.clk_vif.drive_edge();
                cfg.vif.ack   <= 1'b1;
                cfg.vif.rdata <= req.rdata;
                cfg.clk_vif.drive_edge();
                cfg.vif.ack   <= 1'b0;
                cfg.vif.rdata <= '0;
                seq_item_port.item_done();
            end
        endtask
    endclass : pop_ack_driver

    class pop_ack_monitor #(type rdata_t = logic) extends uvm_monitor;
        pop_ack_config#(rdata_t)                    cfg;
        // One item per completed transfer, with rdata.
        uvm_analysis_port #(pop_ack_item#(rdata_t)) ap;

        `uvm_component_param_utils(pop_ack_monitor#(rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            logic   pop;
            logic   ack;
            rdata_t rdata;
            bit     waiting = 0;
            pop_ack_item#(rdata_t) item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                pop   = cfg.vif.pop;
                ack   = cfg.vif.ack;
                rdata = cfg.vif.rdata;
                // A source waiting for ack must hold pop until the transfer.
                if (waiting && pop !== 1'b1) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: pop dropped before ack", cfg.port_name))
                end
                if (ack === 1'b1 && pop !== 1'b1) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: ack is high with pop %b", cfg.port_name, pop))
                end
                waiting = (pop === 1'b1 && ack !== 1'b1);
                // X/Z checks only fire on a 4-state boundary. Across a 2-state
                // SystemC boundary an X or Z from the DUT arrives as 0.
                if ($isunknown(pop)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: pop is %b after reset release", cfg.port_name, pop))
                    continue;
                end
                if (pop !== 1'b1 || ack !== 1'b1) continue;
                if ($isunknown(rdata)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: rdata has X or Z while ack is high: %h", cfg.port_name, rdata))
                end
                item = pop_ack_item#(rdata_t)::type_id::create("item");
                item.rdata = rdata;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", rdata)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : pop_ack_monitor

    class pop_ack_agent #(type rdata_t = logic) extends uvm_agent;
        typedef pop_ack_item#(rdata_t)   item_t;
        typedef pop_ack_config#(rdata_t) config_t;

        pop_ack_config#(rdata_t)                cfg;
        pop_ack_driver#(rdata_t)                drv;
        uvm_sequencer #(pop_ack_item#(rdata_t)) sqr;
        pop_ack_monitor#(rdata_t)               mon;
        // Always null, because the agent has no Mode B operations yet; the env
        // names both on every port.
        pop_ack_monitor#(rdata_t)               model_mon;
        a2c_comparator_base                     model_cmp;

        `uvm_component_param_utils(pop_ack_agent#(rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(pop_ack_config#(rdata_t))::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "pop_ack_agent has no cfg")
            end
            if (cfg.model_vif != null) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: pop_ack has no Mode B operations yet", cfg.port_name))
            end
            mon = pop_ack_monitor#(rdata_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active != UVM_ACTIVE) return;
            drv = pop_ack_driver#(rdata_t)::type_id::create("drv", this);
            drv.cfg = cfg;
            sqr = uvm_sequencer#(pop_ack_item#(rdata_t))::type_id::create("sqr", this);
            // A set from the test or env is higher in the hierarchy, so it
            // wins over this one during build.
            if (cfg.role == A2C_DST) begin
                uvm_config_db#(uvm_object_wrapper)::set(this, "sqr.run_phase", "default_sequence",
                                                        pop_ack_responder_seq#(rdata_t)::type_id::get());
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
        endfunction
    endclass : pop_ack_agent

endpackage : pop_ack_uvm_pkg

`endif // POP_ACK_UVM_PKG_SV
