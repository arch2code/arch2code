`ifndef NOTIFY_ACK_UVM_PKG_SV
`define NOTIFY_ACK_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for notify_ack_if, which has no payload and no parameters. An
// event is a clock with notify and ack both high, and notify still high on
// the next clock is a new event. The A2C_SRC driver notifies once per
// sequence item; the A2C_DST driver only acks, so it has no sequencer. Pin
// timing follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver raises
// notify on both lanes at one drive point, and each lane drops it once its own
// event has completed; the next item starts when both have. A lane of the
// A2C_SRC driver that trails the other by lane_skew_cycles clocks, or stalls,
// is declared dead as for the AXI masters (a2c_lane_watchdog), and the other
// lane serves the sequence alone. The A2C_DST driver acks each lane's event n
// after the delay the DUT lane drew for it: the DUT lane draws and records the
// delay, and a model lane that reaches event n first waits until the DUT lane
// has. Its replay log holds the end of the run phase while the model lane
// catches up (a2c_replay_drain). On the A2C_DST role model_cmp pairs the
// events of the two lanes, so it checks their count. What the DUT produces
// that is not compared:
//   DUT dst port, A2C_SRC agent: `ack` timing
//   DUT src port, A2C_DST agent: none
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

    class notify_ack_config extends a2c_agent_config #(virtual notify_ack_if);
        // dst role: extra clocks, drawn per event, that the driver waits
        // after it samples notify before it raises ack.
        int unsigned ack_delay_min = 0;
        int unsigned ack_delay_max = 0;

        `uvm_object_utils(notify_ack_config)

        function new(string name = "notify_ack_config");
            super.new(name);
        endfunction
    endclass : notify_ack_config

    // ack is high for one clock per event, and rises only after notify has
    // been sampled, so with no delay an event takes two clocks.
    class notify_ack_driver extends a2c_lane_driver #(notify_ack_item, virtual notify_ack_if, notify_ack_config);
        `uvm_component_utils(notify_ack_driver)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected virtual function void raise_request(int l);
            lane[l].notify <= 1'b1;
        endfunction

        protected virtual function void drop_request(int l);
            lane[l].notify <= 1'b0;
        endfunction

        protected virtual function bit request_held(int l);
            return lane[l].notify === 1'b1;
        endfunction

        protected virtual function bit request_taken(int l);
            return lane[l].ack === 1'b1;
        endfunction

        protected virtual function int unsigned item_gap();
            return req.gap;
        endfunction

        virtual function string waiting_for(a2c_lane_e l);
            return "the ack of a notify";
        endfunction

        protected virtual function bit request_seen(int l);
            return lane[l].notify === 1'b1;
        endfunction

        protected virtual task respond(output bit r, output int unsigned delay, output bit at_edge);
            r       = 1'b0;
            delay   = $urandom_range(cfg.ack_delay_max, cfg.ack_delay_min);
            at_edge = 0;
        endtask

        protected virtual function void idle_response(int l);
            lane[l].ack <= 1'b0;
        endfunction

        protected virtual function void drive_response(int l, bit r);
            lane[l].ack <= 1'b1;
        endfunction

        protected virtual function void end_response(int l);
            lane[l].ack <= 1'b0;
        endfunction
    endclass : notify_ack_driver

    class notify_ack_monitor extends a2c_monitor;
        notify_ack_config                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual notify_ack_if                vif;
        uvm_analysis_port #(notify_ack_item) ap;

        `uvm_component_utils(notify_ack_monitor)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual function a2c_clk_vif_t monitor_clock();
            return cfg.clk_vif;
        endfunction

        virtual task run_from_reset();
            logic notify;
            logic ack;
            bit   waiting = 0;
            notify_ack_item item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (cfg.clk_vif.in_reset()) continue;
                notify = vif.notify;
                ack    = vif.ack;
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
                // Each transfer counts for the joint stall rule (a2c_joint_watch).
                if (cfg.joint_watch) a2c_joint_watch::handshake();
                item = notify_ack_item::type_id::create("item");
                // An event has no payload, so the hex field is always 0.
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(), "0"),
                          UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : notify_ack_monitor

    class notify_ack_agent extends a2c_lane_agent #(virtual notify_ack_if);
        typedef notify_ack_item   item_t;
        typedef notify_ack_config config_t;

        notify_ack_config                cfg;
        notify_ack_driver                drv;
        // A2C_SRC only.
        uvm_sequencer #(notify_ack_item) sqr;
        notify_ack_monitor               mon;
        // Mode B only. model_cmp exists on the A2C_DST role.
        notify_ack_monitor                         model_mon;
        a2c_in_order_comparator #(notify_ack_item) model_cmp;

        `uvm_component_utils(notify_ack_agent)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(notify_ack_config)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "notify_ack_agent has no cfg")
            end
            if (cfg.ack_delay_min > cfg.ack_delay_max) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: ack_delay_min %0d is above ack_delay_max %0d", cfg.port_name,
                                                cfg.ack_delay_min, cfg.ack_delay_max))
            end
            mon = notify_ack_monitor::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = notify_ack_monitor::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                if (cfg.role == A2C_DST) model_cmp = a2c_in_order_comparator#(notify_ack_item)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active == UVM_ACTIVE) begin
                drv = notify_ack_driver::type_id::create("drv", this);
                drv.cfg = cfg;
                if (cfg.role == A2C_SRC) begin
                    sqr = uvm_sequencer#(notify_ack_item)::type_id::create("sqr", this);
                end
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
            end
        endfunction

        virtual function lane_cfg_t lane_cfg();
            return cfg;
        endfunction

        virtual function a2c_lane_joiner lane_joiner();
            return drv;
        endfunction

        virtual function uvm_monitor lane_monitor(a2c_lane_e l);
            return (l == A2C_DUT_LANE) ? mon : model_mon;
        endfunction

        virtual function a2c_comparator_base lane_cmp();
            return model_cmp;
        endfunction
    endclass : notify_ack_agent

endpackage : notify_ack_uvm_pkg

`endif // NOTIFY_ACK_UVM_PKG_SV
