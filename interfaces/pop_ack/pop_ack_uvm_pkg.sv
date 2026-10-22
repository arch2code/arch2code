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
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver pops on
// both lanes at one drive point, and each lane drops pop once its own
// transfer has happened; the next item starts when both have, with the DUT
// lane's rdata in req. The A2C_DST driver takes response n from its
// sequencer for the DUT lane's pop n and records its rdata and delay; the
// model lane's pop n gets the same rdata after the same delay, and a model
// lane that reaches pop n first waits until the DUT lane has. A responder
// sequence that takes simulated time to answer holds only the DUT lane.
// The replay log holds the end of the run phase while the model lane
// catches up (a2c_replay_drain). model_cmp compares the transfers of the
// two lanes in order: on the A2C_SRC role for their rdata, on the A2C_DST
// role for their count, since both lanes get the same rdata. What the DUT
// produces that is not compared:
//   DUT dst port, A2C_SRC agent: `ack` delay
//   DUT src port, A2C_DST agent: none
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
        // The model DUT's pin set in Mode B; null otherwise.
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

    class pop_ack_driver #(type rdata_t = logic) extends uvm_driver #(pop_ack_item#(rdata_t))
        implements a2c_replay_lanes;
        typedef virtual pop_ack_if #(.rdata_t(rdata_t)) vif_t;
        typedef a2c_replay_log #(rdata_t) replay_t;
        // LANE_POPPED: a lane that has seen pop and has no response yet:
        // a DUT lane whose responder has not answered, or a model lane
        // waiting for the DUT lane.
        typedef enum {LANE_IDLE, LANE_POPPED, LANE_WAIT, LANE_ACK} lane_state_e;

        pop_ack_config#(rdata_t) cfg;
        // dst role in Mode B only.
        replay_t                 replay;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        protected lane_state_e state[2];
        protected int unsigned starts[2];
        // dst role: a fetch of the DUT lane's response is under way, and
        // has returned it in req.
        protected bit          fetching;
        protected bit          fetched;
        // The transactions each lane has completed, each counted at the
        // drive point of its last clock, from which it cannot be withdrawn.
        protected int unsigned done[2];

        `uvm_component_param_utils(pop_ack_driver#(rdata_t))

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

        protected function void drive_pop(bit p);
            for (int l = 0; l < lanes; l++) lane[l].pop <= p;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back pops go out on consecutive clocks, and pop drops on
        // the first drive point with no item.
        protected virtual task run_src();
            drive_pop(1'b0);
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    drive_pop(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    drive_pop(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                drive_pop(1'b1);
                wait_transfer();
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last lane's transfer, which
        // is the rising edge before it, with the DUT lane's rdata in req. A
        // lane whose transfer has happened holds pop low from the next drive
        // point on.
        protected task wait_transfer();
            bit          pending[2];
            int unsigned left = lanes;
            for (int l = 0; l < lanes; l++) pending[l] = 1'b1;
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (pending[l] && lane[l].ack === 1'b1) begin
                        if (l == A2C_DUT_LANE) req.rdata = lane[l].rdata;
                        pending[l] = 1'b0;
                        left--;
                    end
                end
                cfg.clk_vif.drive_edge();
                if (left == 0) return;
                for (int l = 0; l < lanes; l++) begin
                    if (!pending[l]) lane[l].pop <= 1'b0;
                end
            end
        endtask

        // ack and rdata are driven for one clock per transfer, and rise only
        // after pop has been sampled, so with no delay a transfer takes two
        // clocks. rdata is zero while ack is low. One process serves every
        // lane, taking the DUT lane first, so a model lane waiting on
        // pop n replays it on the clock the DUT lane takes its response.
        protected virtual task run_dst();
            int unsigned delay[2];
            rdata_t      rdata[2];
            bit          at_edge;
            for (int l = 0; l < lanes; l++) begin
                state[l] = LANE_IDLE;
                lane[l].ack   <= 1'b0;
                lane[l].rdata <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (state[l] == LANE_IDLE && lane[l].pop === 1'b1) begin
                        state[l] = LANE_POPPED;
                        starts[l]++;
                    end
                end
                at_edge = 0;
                if (state[A2C_DUT_LANE] == LANE_POPPED) begin
                    fetch_response(at_edge);
                    if (!at_edge) begin
                        delay[A2C_DUT_LANE] = req.delay;
                        rdata[A2C_DUT_LANE] = req.rdata;
                        if (replay != null) replay.record(rdata[A2C_DUT_LANE], delay[A2C_DUT_LANE]);
                        state[A2C_DUT_LANE] = LANE_WAIT;
                    end
                end
                if (lanes == 2 && state[A2C_MODEL_LANE] == LANE_POPPED && replay.can_replay()) begin
                    replay.replay(rdata[A2C_MODEL_LANE], delay[A2C_MODEL_LANE]);
                    state[A2C_MODEL_LANE] = LANE_WAIT;
                end
                if (at_edge) cfg.clk_vif.skew_after_edge();
                else cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) begin
                    case (state[l])
                        LANE_WAIT: begin
                            if (delay[l] > 0) begin
                                delay[l]--;
                            end else begin
                                lane[l].ack   <= 1'b1;
                                lane[l].rdata <= rdata[l];
                                state[l] = LANE_ACK;
                                done[l]++;
                            end
                        end
                        LANE_ACK: begin
                            lane[l].ack   <= 1'b0;
                            lane[l].rdata <= '0;
                            state[l] = LANE_IDLE;
                            if (l == A2C_DUT_LANE) seq_item_port.item_done();
                        end
                        default: ;
                    endcase
                end
            end
        endtask

        // Waits for the DUT lane's response in req until the next rising
        // edge, and returns at_edge set if the edge came first. The fetch
        // runs in its own process and outlives the wait, so a responder that
        // takes clocks to answer stalls only the DUT lane. Its response takes
        // effect from the first drive point after it arrives, as it would
        // with get_next_item() called in line.
        protected task fetch_response(output bit at_edge);
            if (!fetching) begin
                fetching = 1;
                fork
                    begin
                        seq_item_port.get_next_item(req);
                        fetched = 1;
                    end
                join_none
            end
            fork
                begin
                    fork
                        wait (fetched);
                        @(cfg.clk_vif.cb);
                    join_any
                    disable fork;
                end
            join
            at_edge = !fetched;
            if (fetched) begin
                fetched  = 0;
                fetching = 0;
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
    endclass : pop_ack_driver

    class pop_ack_monitor #(type rdata_t = logic) extends uvm_monitor;
        pop_ack_config#(rdata_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual pop_ack_if #(.rdata_t(rdata_t))     vif;
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
                pop   = vif.pop;
                ack   = vif.ack;
                rdata = vif.rdata;
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
        // Finds the passive agents on the DUT pin set, whose model_cmps a cut of
        // the active agent's replay log also cuts, and tells a passive agent
        // whether an active one has claimed the pin set.
        typedef a2c_pin_registry #(virtual pop_ack_if #(.rdata_t(rdata_t))) registry_t;

        pop_ack_config#(rdata_t)                cfg;
        pop_ack_driver#(rdata_t)                drv;
        uvm_sequencer #(pop_ack_item#(rdata_t)) sqr;
        pop_ack_monitor#(rdata_t)               mon;
        // Mode B only.
        pop_ack_monitor#(rdata_t)               model_mon;
        a2c_in_order_comparator #(item_t)       model_cmp;

        `uvm_component_param_utils(pop_ack_agent#(rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(pop_ack_config#(rdata_t))::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "pop_ack_agent has no cfg")
            end
            mon = pop_ack_monitor#(rdata_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = pop_ack_monitor#(rdata_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                model_cmp = a2c_in_order_comparator#(item_t)::type_id::create("model_cmp", this);
            end
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

        // A passive A2C_DST Mode B agent says so when no active responder has
        // claimed its pin set, since its model_cmp then misses the drain's
        // cuts. An active A2C_SRC agent keeps no replay log and claims no pin
        // set, so a passive one has nothing to report.
        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            if (drv == null && model_cmp != null && cfg.role == A2C_DST) registry_t::note_unowned(cfg.vif, this, cfg.port_name);
        endfunction
    endclass : pop_ack_agent

endpackage : pop_ack_uvm_pkg

`endif // POP_ACK_UVM_PKG_SV
