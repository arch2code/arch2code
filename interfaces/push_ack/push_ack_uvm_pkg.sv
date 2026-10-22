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
// its own transfer has happened; the next item starts when both have. The
// A2C_DST driver acks each lane's transfer n after the delay the DUT lane drew
// for it: the DUT lane draws and records the delay, and a model lane that
// reaches transfer n first waits until the DUT lane has. Its replay log holds
// the end of the run phase while the model lane catches up (a2c_replay_drain).
// On the A2C_DST role model_cmp compares the pushed data of the two lanes in
// order. What the DUT produces that is not compared:
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
            return super.do_compare(rhs, comparer) && (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", data);
        endfunction
    endclass : push_ack_item

    class push_ack_config #(type data_t = logic) extends uvm_object;
        virtual push_ack_if #(.data_t(data_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise.
        virtual push_ack_if #(.data_t(data_t)) model_vif;
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

    class push_ack_driver #(type data_t = logic) extends uvm_driver #(push_ack_item#(data_t))
        implements a2c_replay_lanes;
        typedef virtual push_ack_if #(.data_t(data_t)) vif_t;
        typedef a2c_replay_log #(bit) replay_t;
        // LANE_PUSHED: a lane that has seen push and has no ack delay yet,
        // which only a model lane waiting for the DUT lane stays in.
        typedef enum {LANE_IDLE, LANE_PUSHED, LANE_WAIT, LANE_ACK} lane_state_e;

        push_ack_config#(data_t) cfg;
        // dst role in Mode B only.
        replay_t                 replay;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        protected lane_state_e state[2];
        protected int unsigned starts[2];
        // The transactions each lane has completed, each counted at the
        // drive point of its last clock, from which it cannot be withdrawn.
        protected int unsigned done[2];

        `uvm_component_param_utils(push_ack_driver#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (cfg.model_vif == null || cfg.role != A2C_DST) return;
            replay = replay_t::type_id::create("replay", this);
            replay.driver  = this;
            replay.clk_vif = cfg.clk_vif;
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

        protected function void drive_push(bit push);
            for (int l = 0; l < lanes; l++) lane[l].push <= push;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back items go out on consecutive clocks, and push drops on
        // the first drive point with no item.
        protected virtual task run_src();
            for (int l = 0; l < lanes; l++) begin
                lane[l].push <= 1'b0;
                lane[l].data <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    drive_push(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    drive_push(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                for (int l = 0; l < lanes; l++) begin
                    lane[l].push <= 1'b1;
                    lane[l].data <= req.data;
                end
                wait_transfer();
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last lane's transfer, which
        // is the rising edge before it. A lane whose transfer has happened
        // holds push low from the next drive point on.
        protected task wait_transfer();
            bit          pending[2];
            int unsigned left = lanes;
            for (int l = 0; l < lanes; l++) pending[l] = 1'b1;
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (pending[l] && lane[l].ack === 1'b1) begin
                        pending[l] = 1'b0;
                        left--;
                    end
                end
                cfg.clk_vif.drive_edge();
                if (left == 0) return;
                for (int l = 0; l < lanes; l++) begin
                    if (!pending[l]) lane[l].push <= 1'b0;
                end
            end
        endtask

        // ack is high for one clock per transfer, and rises only after push
        // has been sampled, so with no delay a transfer takes two clocks.
        // One process serves every lane, sampling the DUT lane first, so a
        // model lane waiting on transfer n replays it on the clock the DUT
        // lane draws its delay.
        protected virtual task run_dst();
            int unsigned delay[2];
            bit          unused;
            for (int l = 0; l < lanes; l++) begin
                state[l] = LANE_IDLE;
                lane[l].ack <= 1'b0;
            end
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (state[l] == LANE_IDLE && lane[l].push === 1'b1) begin
                        state[l] = LANE_PUSHED;
                        starts[l]++;
                    end
                    if (state[l] != LANE_PUSHED) continue;
                    if (l == A2C_DUT_LANE) begin
                        delay[l] = $urandom_range(cfg.ack_delay_max, cfg.ack_delay_min);
                        if (replay != null) replay.record(1'b0, delay[l]);
                    end else if (replay.can_replay()) begin
                        replay.replay(unused, delay[l]);
                    end else begin
                        continue;
                    end
                    state[l] = LANE_WAIT;
                end
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) begin
                    case (state[l])
                        LANE_WAIT: begin
                            if (delay[l] > 0) begin
                                delay[l]--;
                            end else begin
                                lane[l].ack <= 1'b1;
                                state[l] = LANE_ACK;
                                done[l]++;
                            end
                        end
                        LANE_ACK: begin
                            lane[l].ack <= 1'b0;
                            state[l] = LANE_IDLE;
                        end
                        default: ;
                    endcase
                end
            end
        endtask

        virtual function bit lane_busy(a2c_lane_e l);
            return state[l] != LANE_IDLE;
        endfunction

        virtual function int unsigned lane_done(a2c_lane_e l);
            return done[l];
        endfunction

        virtual function int unsigned lane_starts(a2c_lane_e l);
            return starts[l];
        endfunction
    endclass : push_ack_driver

    class push_ack_monitor #(type data_t = logic) extends uvm_monitor;
        push_ack_config#(data_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual push_ack_if #(.data_t(data_t))      vif;
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
                push = vif.push;
                ack  = vif.ack;
                data = vif.data;
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
                if (drv != null && drv.replay != null) begin
                    drv.replay.cmp      = model_cmp;
                    drv.replay.watchers = registry_t::of(cfg.vif);
                    registry_t::of(cfg.vif).owner = get_full_name();
                end
                if (drv == null) registry_t::of(cfg.vif).cmps.push_back(model_cmp);
            end
        endfunction

        // A passive Mode B agent says so when no active responder has claimed
        // its pin set, since its model_cmp then misses the drain's cuts.
        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            if (drv == null && model_cmp != null) registry_t::note_unowned(cfg.vif, this, cfg.port_name);
        endfunction
    endclass : push_ack_agent

endpackage : push_ack_uvm_pkg

`endif // PUSH_ACK_UVM_PKG_SV
