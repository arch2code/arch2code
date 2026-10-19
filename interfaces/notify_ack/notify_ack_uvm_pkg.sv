`ifndef NOTIFY_ACK_UVM_PKG_SV
`define NOTIFY_ACK_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for notify_ack_if, which has no payload and no parameters. An
// event is a clock with notify and ack both high, and notify still high on
// the next clock is a new event. The A2C_SRC driver notifies once per
// sequence item; the A2C_DST driver only acks, so it has no sequencer. Pin
// timing follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
package notify_ack_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class notify_ack_item extends uvm_sequence_item;
        // Idle clocks (notify low) the src driver inserts before this event.
        int unsigned gap;

        `uvm_object_utils(notify_ack_item)

        function new(string name = "notify_ack_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            notify_ack_item rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            gap = rhs_.gap;
        endfunction

        // gap is stimulus timing, and an event has no payload, so any two
        // items compare equal.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            notify_ack_item rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer);
        endfunction

        virtual function string convert2string();
            return "notify";
        endfunction
    endclass : notify_ack_item

    class notify_ack_config extends uvm_object;
        virtual notify_ack_if   vif;
        // The model DUT's pin set in Mode B; null otherwise. The agent has no
        // Mode B operations yet and stops with A2C_CFG when it is set.
        virtual notify_ack_if   model_vif;
        virtual a2c_clk_if      clk_vif;
        uvm_active_passive_enum is_active = UVM_ACTIVE;
        a2c_role_e              role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                  port_name = "";
        // dst role: extra clocks, drawn per event, that the driver waits
        // after it samples notify before it raises ack.
        int unsigned            ack_delay_min = 0;
        int unsigned            ack_delay_max = 0;

        `uvm_object_utils(notify_ack_config)

        function new(string name = "notify_ack_config");
            super.new(name);
        endfunction
    endclass : notify_ack_config

    class notify_ack_driver extends uvm_driver #(notify_ack_item);
        notify_ack_config cfg;

        `uvm_component_utils(notify_ack_driver)

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
        // back-to-back items go out on consecutive clocks, and notify drops
        // on the first drive point with no item.
        protected virtual task run_src();
            cfg.vif.notify <= 1'b0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.notify <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.notify <= 1'b0;
                    cfg.clk_vif.drive_edge();
                end
                cfg.vif.notify <= 1'b1;
                do cfg.clk_vif.sample_edge(); while (cfg.vif.ack !== 1'b1);
                // The event completes at the rising edge before this drive point.
                cfg.clk_vif.drive_edge();
                seq_item_port.item_done();
            end
        endtask

        // ack is high for one clock per event, and rises only after notify
        // has been sampled, so with no delay an event takes two clocks.
        protected virtual task run_dst();
            cfg.vif.ack <= 1'b0;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (cfg.vif.notify !== 1'b1) continue;
                repeat ($urandom_range(cfg.ack_delay_max, cfg.ack_delay_min)) cfg.clk_vif.drive_edge();
                cfg.clk_vif.drive_edge();
                cfg.vif.ack <= 1'b1;
                cfg.clk_vif.drive_edge();
                cfg.vif.ack <= 1'b0;
            end
        endtask
    endclass : notify_ack_driver

    class notify_ack_monitor extends uvm_monitor;
        notify_ack_config                    cfg;
        uvm_analysis_port #(notify_ack_item) ap;

        `uvm_component_utils(notify_ack_monitor)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            logic notify;
            logic ack;
            bit   waiting = 0;
            notify_ack_item item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                notify = cfg.vif.notify;
                ack    = cfg.vif.ack;
                // A source waiting for ack must hold notify until the event completes.
                if (waiting && notify !== 1'b1) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: notify dropped before ack", cfg.port_name))
                end
                if (ack === 1'b1 && notify !== 1'b1) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: ack is high with notify %b", cfg.port_name, notify))
                end
                waiting = (notify === 1'b1 && ack !== 1'b1);
                // X/Z checks only fire on a 4-state boundary. Across a 2-state
                // SystemC boundary an X or Z from the DUT arrives as 0.
                if ($isunknown(notify)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: notify is %b after reset release", cfg.port_name, notify))
                    continue;
                end
                if (notify !== 1'b1 || ack !== 1'b1) continue;
                item = notify_ack_item::type_id::create("item");
                // An event has no payload, so the hex field is always 0.
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(), "0"),
                          UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : notify_ack_monitor

    class notify_ack_agent extends uvm_agent;
        typedef notify_ack_item   item_t;
        typedef notify_ack_config config_t;

        notify_ack_config                cfg;
        notify_ack_driver                drv;
        // A2C_SRC only.
        uvm_sequencer #(notify_ack_item) sqr;
        notify_ack_monitor               mon;
        // Always null, because the agent has no Mode B operations yet; the env
        // names both on every port.
        notify_ack_monitor               model_mon;
        a2c_comparator_base              model_cmp;

        `uvm_component_utils(notify_ack_agent)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(notify_ack_config)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "notify_ack_agent has no cfg")
            end
            if (cfg.model_vif != null) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: notify_ack has no Mode B operations yet", cfg.port_name))
            end
            if (cfg.ack_delay_min > cfg.ack_delay_max) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: ack_delay_min %0d is above ack_delay_max %0d", cfg.port_name,
                                                cfg.ack_delay_min, cfg.ack_delay_max))
            end
            mon = notify_ack_monitor::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active == UVM_ACTIVE) begin
                drv = notify_ack_driver::type_id::create("drv", this);
                drv.cfg = cfg;
                if (cfg.role == A2C_SRC) begin
                    sqr = uvm_sequencer#(notify_ack_item)::type_id::create("sqr", this);
                end
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
        endfunction
    endclass : notify_ack_agent

endpackage : notify_ack_uvm_pkg

`endif // NOTIFY_ACK_UVM_PKG_SV
