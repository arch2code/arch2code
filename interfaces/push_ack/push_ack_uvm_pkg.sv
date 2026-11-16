`ifndef PUSH_ACK_UVM_PKG_SV
`define PUSH_ACK_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for push_ack_if. A transfer is a clock with push and ack both
// high, and push still high on the next clock is a new transfer. The A2C_SRC
// driver pushes sequence items; the A2C_DST driver only acks, so it has no
// sequencer. Pin timing follows a2c_clk_if: drive at drive_edge(), sample at
// sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver puts
// each item on both lanes at one drive point, and each lane drops push once
// its own transfer has happened; the next item starts when both have. A lane
// of the A2C_SRC driver that trails the other by lane_skew_cycles clocks, or
// stalls, is declared dead as for the AXI masters (a2c_lane_watchdog), and the
// other lane serves the sequence alone. The A2C_DST driver acks each lane's
// transfer n after the delay the DUT lane drew for it: the DUT lane draws and
// records the delay, and a model lane that reaches transfer n first waits
// until the DUT lane has. Its replay log holds the end of the run phase while
// the model lane catches up (a2c_replay_drain). On the A2C_DST role model_cmp
// compares the pushed data of the two lanes in order. What the DUT produces
// that is not compared:
//   DUT dst port, A2C_SRC agent: `ack` timing
//   DUT src port, A2C_DST agent: none
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
            // A field that differs is also passed to comparer, whose
            // miscompares string then names it.
            if (data !== rhs_.data) void'(comparer.compare_field("data", data, rhs_.data, $bits(data)));
            return super.do_compare(rhs, comparer) && (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", data);
        endfunction
    endclass : push_ack_item

    class push_ack_config #(type data_t = logic) extends a2c_agent_config #(virtual push_ack_if #(.data_t(data_t)));
        // dst role: extra clocks, drawn per transfer, that the driver waits
        // after it samples push before it raises ack.
        int unsigned ack_delay_min = 0;
        int unsigned ack_delay_max = 0;

        `uvm_object_param_utils(push_ack_config#(data_t))

        function new(string name = "push_ack_config");
            super.new(name);
        endfunction
    endclass : push_ack_config

    // ack is high for one clock per transfer, and rises only after push has
    // been sampled, so with no delay a transfer takes two clocks.
    class push_ack_driver #(type data_t = logic)
        extends a2c_lane_driver #(push_ack_item#(data_t), virtual push_ack_if #(.data_t(data_t)), push_ack_config#(data_t));
        `uvm_component_param_utils(push_ack_driver#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected virtual function void reset_lane(int l);
            lane[l].push <= 1'b0;
            lane[l].data <= '0;
        endfunction

        protected virtual function void drive_request(int l, bit on);
            lane[l].push <= on;
            if (on) lane[l].data <= req.data;
        endfunction

        protected virtual function bit request_held(int l);
            return lane[l].push === 1'b1;
        endfunction

        protected virtual function bit request_taken(int l);
            return lane[l].ack === 1'b1;
        endfunction

        protected virtual function int unsigned item_gap();
            return req.gap;
        endfunction

        virtual function string waiting_for(a2c_lane_e l);
            return $sformatf("the transfer of %p", req.data);
        endfunction

        protected virtual function bit request_seen(int l);
            return lane[l].push === 1'b1;
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
    endclass : push_ack_driver

    class push_ack_monitor #(type data_t = logic) extends uvm_monitor implements a2c_flow_counts;
        push_ack_config#(data_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual push_ack_if #(.data_t(data_t))      vif;
        uvm_analysis_port #(push_ack_item#(data_t)) ap;

        // The counts a2c_rt_checker reads (a2c_flow_counts), from the reset release.
        protected longint unsigned n_samples;
        protected longint unsigned n_valid;
        protected longint unsigned n_ready;
        protected longint unsigned n_transfers;

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
                push = vif.push;
                ack  = vif.ack;
                data = vif.data;
                // ack means nothing without push, so a clock with push low
                // counts as one the sink did not refuse.
                n_samples++;
                n_valid     += (push === 1'b1);
                n_ready     += (ack === 1'b1 || push !== 1'b1);
                n_transfers += (push === 1'b1 && ack === 1'b1);
                // A source waiting for ack must hold push and data until the transfer.
                if (waiting && (push !== 1'b1 || data !== held)) begin
                    string what = a2c_select_str(push !== 1'b1, "push dropped", "data changed");
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
                // Each transfer counts for the joint stall rule (a2c_joint_watch).
                a2c_joint_watch::handshake();
                item = push_ack_item#(data_t)::type_id::create("item");
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
    endclass : push_ack_monitor

    class push_ack_agent #(type data_t = logic) extends uvm_agent;
        typedef push_ack_item#(data_t)   item_t;
        typedef push_ack_config#(data_t) config_t;
        // Finds the passive agents on the DUT pin set, whose model_cmps a cut of
        // the active agent's replay log also cuts, and tells a passive agent
        // whether an active one has claimed the pin set.
        typedef a2c_pin_registry #(virtual push_ack_if #(.data_t(data_t))) registry_t;

        push_ack_config#(data_t)                cfg;
        push_ack_driver#(data_t)                drv;
        // A2C_SRC only.
        uvm_sequencer #(push_ack_item#(data_t)) sqr;
        push_ack_monitor#(data_t)               mon;
        // Mode B only. model_cmp exists on the A2C_DST role.
        push_ack_monitor#(data_t)               model_mon;
        a2c_in_order_comparator #(item_t)       model_cmp;

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
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = push_ack_monitor#(data_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                if (cfg.role == A2C_DST) model_cmp = a2c_in_order_comparator#(item_t)::type_id::create("model_cmp", this);
            end
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
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
            end
            if (drv != null) drv.join_lanes(this, model_cmp, mon, model_mon);
            else registry_t::join_passive(cfg.vif, cfg.model_vif, mon, model_mon, model_cmp);
        endfunction

        // A passive A2C_DST Mode B agent says so when no active agent has
        // claimed its pin set, since its model_cmp then misses the drain's
        // cuts or the master's lane deaths. An A2C_SRC agent has no
        // model_cmp, as only the DUT's ack timing differs between the lanes
        // there.
        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            if (drv == null && model_cmp != null && cfg.role == A2C_DST) registry_t::note_unowned(cfg.vif, this, cfg.port_name);
        endfunction
    endclass : push_ack_agent

endpackage : push_ack_uvm_pkg

`endif // PUSH_ACK_UVM_PKG_SV
