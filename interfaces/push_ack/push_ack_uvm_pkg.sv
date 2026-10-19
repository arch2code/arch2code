`ifndef PUSH_ACK_UVM_PKG_SV
`define PUSH_ACK_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for push_ack_if. A transfer is a clock with push and ack both
// high, and push still high on the next clock is a new transfer. The A2C_SRC
// driver pushes sequence items; the A2C_DST driver only acks, so it has no
// sequencer. Pin timing follows a2c_clk_if: drive at drive_edge(), sample at
// sample_edge().
package push_ack_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class push_ack_item #(type data_t = logic) extends uvm_sequence_item;
        rand data_t  data;
        // Idle clocks (push low) the src driver inserts before this transfer.
        int unsigned gap;

        `uvm_object_param_utils(push_ack_item#(data_t))

        function new(string name = "push_ack_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            push_ack_item#(data_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            data = rhs_.data;
            gap  = rhs_.gap;
        endfunction

        // gap is stimulus timing, not payload, so it takes no part in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            push_ack_item#(data_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", data);
        endfunction
    endclass : push_ack_item

    class push_ack_config #(type data_t = logic) extends uvm_object;
        virtual push_ack_if #(.data_t(data_t)) vif;
        virtual a2c_clk_if                     clk_vif;
        uvm_active_passive_enum                is_active = UVM_ACTIVE;
        a2c_role_e                             role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                                 port_name = "";
        // dst role: extra clocks, drawn per transfer, that the driver waits
        // after it samples push before it raises ack.
        int unsigned                           ack_delay_min = 0;
        int unsigned                           ack_delay_max = 0;

        `uvm_object_param_utils(push_ack_config#(data_t))

        function new(string name = "push_ack_config");
            super.new(name);
        endfunction
    endclass : push_ack_config

    class push_ack_driver #(type data_t = logic) extends uvm_driver #(push_ack_item#(data_t));
        push_ack_config#(data_t) cfg;

        `uvm_component_param_utils(push_ack_driver#(data_t))

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
        // back-to-back items go out on consecutive clocks, and push drops on
        // the first drive point with no item.
        protected virtual task run_src();
            cfg.vif.push <= 1'b0;
            cfg.vif.data <= '0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.push <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.push <= 1'b0;
                    cfg.clk_vif.drive_edge();
                end
                cfg.vif.push <= 1'b1;
                cfg.vif.data <= req.data;
                do cfg.clk_vif.sample_edge(); while (cfg.vif.ack !== 1'b1);
                // The transfer happens at the rising edge before this drive point.
                cfg.clk_vif.drive_edge();
                seq_item_port.item_done();
            end
        endtask

        // ack is high for one clock per transfer, and rises only after push
        // has been sampled, so with no delay a transfer takes two clocks.
        protected virtual task run_dst();
            cfg.vif.ack <= 1'b0;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (cfg.vif.push !== 1'b1) continue;
                repeat ($urandom_range(cfg.ack_delay_max, cfg.ack_delay_min)) cfg.clk_vif.drive_edge();
                cfg.clk_vif.drive_edge();
                cfg.vif.ack <= 1'b1;
                cfg.clk_vif.drive_edge();
                cfg.vif.ack <= 1'b0;
            end
        endtask
    endclass : push_ack_driver

    class push_ack_monitor #(type data_t = logic) extends uvm_monitor;
        push_ack_config#(data_t)                    cfg;
        uvm_analysis_port #(push_ack_item#(data_t)) ap;

        `uvm_component_param_utils(push_ack_monitor#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            logic  push;
            logic  ack;
            data_t data;
            data_t held;
            bit    waiting = 0;
            push_ack_item#(data_t) item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                push = cfg.vif.push;
                ack  = cfg.vif.ack;
                data = cfg.vif.data;
                // A source waiting for ack must hold push and data until the transfer.
                if (waiting && (push !== 1'b1 || data !== held)) begin
                    string what = (push !== 1'b1) ? "push dropped" : "data changed";
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before ack of %h", cfg.port_name, what, held))
                end
                if (ack === 1'b1 && push !== 1'b1) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: ack is high with push %b", cfg.port_name, push))
                end
                waiting = (push === 1'b1 && ack !== 1'b1);
                held    = data;
                // X/Z checks only fire on a 4-state boundary. Across a 2-state
                // SystemC boundary an X or Z from the DUT arrives as 0.
                if ($isunknown(push)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: push is %b after reset release", cfg.port_name, push))
                    continue;
                end
                if (push !== 1'b1) continue;
                if ($isunknown(data)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: data has X or Z while push is high: %h", cfg.port_name, data))
                end
                if (ack !== 1'b1) continue;
                item = push_ack_item#(data_t)::type_id::create("item");
                item.data = data;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", data)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : push_ack_monitor

    class push_ack_agent #(type data_t = logic) extends uvm_agent;
        typedef push_ack_item#(data_t)   item_t;
        typedef push_ack_config#(data_t) config_t;

        push_ack_config#(data_t)                cfg;
        push_ack_driver#(data_t)                drv;
        // A2C_SRC only.
        uvm_sequencer #(push_ack_item#(data_t)) sqr;
        push_ack_monitor#(data_t)               mon;

        `uvm_component_param_utils(push_ack_agent#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(push_ack_config#(data_t))::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "push_ack_agent has no cfg")
            end
            if (cfg.ack_delay_min > cfg.ack_delay_max) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: ack_delay_min %0d is above ack_delay_max %0d", cfg.port_name,
                                                cfg.ack_delay_min, cfg.ack_delay_max))
            end
            mon = push_ack_monitor#(data_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active == UVM_ACTIVE) begin
                drv = push_ack_driver#(data_t)::type_id::create("drv", this);
                drv.cfg = cfg;
                if (cfg.role == A2C_SRC) begin
                    sqr = uvm_sequencer#(push_ack_item#(data_t))::type_id::create("sqr", this);
                end
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
        endfunction
    endclass : push_ack_agent

endpackage : push_ack_uvm_pkg

`endif // PUSH_ACK_UVM_PKG_SV
