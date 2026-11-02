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

    class notify_ack_config extends uvm_object;
        virtual notify_ack_if   vif;
        // The model DUT's pin set in Mode B; null otherwise.
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

    class notify_ack_driver extends uvm_driver #(notify_ack_item) implements a2c_replay_lanes, a2c_lane_waits;
        typedef virtual notify_ack_if vif_t;
        typedef a2c_replay_log #(bit) replay_t;
        // LANE_NOTIFIED: a lane that has seen notify and has no ack delay
        // yet, which only a model lane waiting for the DUT lane stays in.
        typedef enum {LANE_IDLE, LANE_NOTIFIED, LANE_WAIT, LANE_ACK} lane_state_e;

        notify_ack_config cfg;
        // dst role in Mode B only.
        replay_t          replay;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        // src role: bounds how long one lane may trail the other and how
        // long the lanes may stall in Mode B, and keeps which lanes are
        // dead.
        a2c_lane_watchdog      wd;
        protected lane_state_e state[2];
        protected int unsigned starts[2];
        // The transactions each lane has completed, each counted at the
        // drive point of its last clock, from which it cannot be withdrawn.
        protected int unsigned done[2];

        `uvm_component_utils(notify_ack_driver)

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

        protected function void drive_notify(bit notify);
            for (int l = 0; l < lanes; l++) if (!wd.dead[l]) lane[l].notify <= notify;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back items go out on consecutive clocks, and notify drops
        // on the first drive point with no item.
        protected virtual task run_src();
            wd = new(this, cfg.port_name, lanes, "item", "every open and later item completes at once");
            wd.configure();
            drive_notify(1'b0);
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
                    drive_notify(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    drive_notify(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                drive_notify(1'b1);
                wait_event();
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last live lane's event
        // completed, which is the rising edge before it. A lane whose event
        // has completed holds notify low from the next drive point on. In Mode
        // B wd bounds how long one lane may trail the other and how long the
        // lanes may stall (a2c_lane_watchdog), and a lane it declares dead
        // drops out of the wait.
        protected task wait_event();
            bit    pending[2];
            bit    took[2];
            bit    finished[2];
            wd.begin_item();
            for (int l = 0; l < lanes; l++) pending[l] = !wd.dead[l];
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    took[l]     = pending[l] && lane[l].ack === 1'b1;
                    pending[l] &= !took[l];
                    finished[l] |= took[l];
                end
                wd.step(took, pending);
                cfg.clk_vif.drive_edge();
                if (!pending[A2C_DUT_LANE] && !pending[A2C_MODEL_LANE]) return;
                for (int l = 0; l < lanes; l++) begin
                    if (finished[l]) lane[l].notify <= 1'b0;
                end
            end
        endtask

        virtual function string waiting_for(a2c_lane_e l);
            return "the ack of a notify";
        endfunction

        // Mode B: a dead lane keeps an asserted notify until its ack, as the
        // protocol requires, and drops notify at the drive point after it.
        // No later item drives the lane.
        protected task release_dead();
            bit took[2];
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < 2; l++) took[l] = wd.dead[l] && lane[l].notify === 1'b1 && lane[l].ack === 1'b1;
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < 2; l++) if (took[l]) lane[l].notify <= 1'b0;
            end
        endtask

        // ack is high for one clock per event, and rises only after notify
        // has been sampled, so with no delay an event takes two clocks. One
        // process serves every lane, sampling the DUT lane first, so a model
        // lane waiting on event n replays it on the clock the DUT lane draws
        // its delay.
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
                    if (state[l] == LANE_IDLE && lane[l].notify === 1'b1) begin
                        state[l] = LANE_NOTIFIED;
                        starts[l]++;
                    end
                    if (state[l] != LANE_NOTIFIED) continue;
                    // The model lane's requester withdrew the request it
                    // waited on, which the monitor reports as A2C_HOLD.
                    // Nothing was taken for it, so the lane goes back to idle
                    // and waits for no record.
                    if (l == A2C_MODEL_LANE && lane[l].notify !== 1'b1) begin
                        starts[l]--;
                        replay.cancel_wait();
                        state[l] = LANE_IDLE;
                        continue;
                    end
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
    endclass : notify_ack_driver

    class notify_ack_monitor extends uvm_monitor;
        notify_ack_config                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual notify_ack_if                vif;
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
                a2c_joint_watch::handshake();
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
        // Finds the passive agents on the DUT pin set, whose model_cmps a cut of
        // the active agent's replay log also cuts, and tells a passive agent
        // whether an active one has claimed the pin set.
        typedef a2c_pin_registry #(virtual notify_ack_if) registry_t;

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

        // A passive A2C_DST Mode B agent says so when no active responder
        // has claimed its pin set, since its model_cmp then misses the
        // drain's cuts. An A2C_SRC agent has no model_cmp, as only the DUT's
        // ack timing differs between the lanes there, so an active one tells
        // a passive one of no death and claims no pin set.
        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            if (drv == null && model_cmp != null && cfg.role == A2C_DST) registry_t::note_unowned(cfg.vif, this, cfg.port_name);
        endfunction
    endclass : notify_ack_agent

endpackage : notify_ack_uvm_pkg

`endif // NOTIFY_ACK_UVM_PKG_SV
