`ifndef REQ_ACK_UVM_PKG_SV
`define REQ_ACK_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for req_ack_if. A transfer is a clock with req and ack both high;
// rdata is valid with ack, and req still high on the next clock is a new
// request. The A2C_SRC driver sends one sequence item at a time and writes
// the rdata it gets back into that item before item_done(). The A2C_DST
// driver is a reactive responder: for each request it samples it takes one
// item from its sequencer and drives ack and the item's rdata after the
// item's delay. The agent starts req_ack_responder_seq on that sequencer as
// its run_phase default_sequence; a test replaces it with a uvm_config_db
// set from higher in the hierarchy or with a factory override. Pin timing
// follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver puts
// each request on both lanes at one drive point, and each lane drops req once
// its own transfer has happened; the next item starts when both have, with the
// DUT lane's rdata in req. A lane of the A2C_SRC driver that trails the other
// by lane_skew_cycles clocks, or stalls, is declared dead as for the AXI
// masters (a2c_lane_watchdog), and the other lane serves the sequence alone.
// The A2C_DST driver builds response n from the DUT lane's request n, through
// request_fifo, and records its rdata and delay; the model lane's request n
// gets the same rdata after the same delay, and a model lane that reaches
// request n first waits until the DUT lane has. Only the DUT lane's requests
// reach request_fifo. A responder sequence that takes simulated time to answer
// holds only the DUT lane. The replay log holds the end of the run phase while
// the model lane catches up (a2c_replay_drain). model_cmp compares the
// transfers of the two lanes in order: on the A2C_SRC role for their rdata, on
// the A2C_DST role for their request data. What the DUT produces that is not
// compared:
//   DUT dst port, A2C_SRC agent: `ack` delay
//   DUT src port, A2C_DST agent: none
package req_ack_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class req_ack_item #(type data_t = logic, type rdata_t = logic) extends uvm_sequence_item;
        rand data_t  data;
        rand rdata_t rdata;
        // src role: idle clocks (req low) the driver inserts before this request.
        int unsigned gap;
        // dst role: extra clocks the driver waits after it samples the request
        // before it raises ack.
        int unsigned delay;

        `uvm_object_param_utils(req_ack_item#(data_t, rdata_t))

        function new(string name = "req_ack_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            req_ack_item#(data_t, rdata_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            data  = rhs_.data;
            rdata = rhs_.rdata;
            gap   = rhs_.gap;
            delay = rhs_.delay;
        endfunction

        // gap and delay are stimulus timing, not payload, so they take no part
        // in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            req_ack_item#(data_t, rdata_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (data === rhs_.data) && (rdata === rhs_.rdata);
        endfunction

        virtual function string convert2string();
            return $sformatf("data=%p rdata=%p", data, rdata);
        endfunction
    endclass : req_ack_item

    class req_ack_config #(type data_t = logic, type rdata_t = logic) extends uvm_object;
        virtual req_ack_if #(.data_t(data_t), .rdata_t(rdata_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise.
        virtual req_ack_if #(.data_t(data_t), .rdata_t(rdata_t)) model_vif;
        virtual a2c_clk_if                                       clk_vif;
        uvm_active_passive_enum                                  is_active = UVM_ACTIVE;
        a2c_role_e                                               role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                                                   port_name = "";

        `uvm_object_param_utils(req_ack_config#(data_t, rdata_t))

        function new(string name = "req_ack_config");
            super.new(name);
        endfunction
    endclass : req_ack_config

    // request_fifo holds each request the monitor sees, data only, in order,
    // so a responder sequence can compute rdata from the request. The agent
    // connects it in the A2C_DST role only.
    class req_ack_sequencer #(type data_t = logic, type rdata_t = logic)
        extends uvm_sequencer #(req_ack_item#(data_t, rdata_t));
        uvm_tlm_analysis_fifo #(req_ack_item#(data_t, rdata_t)) request_fifo;

        `uvm_component_param_utils(req_ack_sequencer#(data_t, rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            request_fifo = new("request_fifo", this);
        endfunction

        // A responder takes one request per transfer, so more than one left
        // at the end means the responder sequence does not drain the fifo,
        // which then grows for the whole run.
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (request_fifo.used() > 1) begin
                `uvm_error("A2C_RESPONDER", $sformatf("request_fifo holds %0d requests at the end of the test: the responder sequence must take one per request",
                                                      request_fifo.used()))
            end
        endfunction
    endclass : req_ack_sequencer

    // The default A2C_DST responder: one item per request in request_fifo,
    // with random rdata and no delay. A replacement extends this class and
    // overrides respond(), or replaces body() and keeps request_fifo drained.
    class req_ack_responder_seq #(type data_t = logic, type rdata_t = logic)
        extends uvm_sequence #(req_ack_item#(data_t, rdata_t));
        `uvm_object_param_utils(req_ack_responder_seq#(data_t, rdata_t))
        `uvm_declare_p_sequencer(req_ack_sequencer#(data_t, rdata_t))

        function new(string name = "req_ack_responder_seq");
            super.new(name);
        endfunction

        // Sets rsp.rdata and rsp.delay for request.
        virtual function void respond(req_ack_item#(data_t, rdata_t) request, req_ack_item#(data_t, rdata_t) rsp);
            if (!rsp.randomize()) `uvm_fatal("A2C_RAND", "req_ack response randomize failed")
            rsp.data  = request.data;
            rsp.delay = 0;
        endfunction

        virtual task body();
            req_ack_item#(data_t, rdata_t) request;
            req_ack_item#(data_t, rdata_t) rsp;
            forever begin
                p_sequencer.request_fifo.get(request);
                rsp = req_ack_item#(data_t, rdata_t)::type_id::create("rsp");
                start_item(rsp);
                respond(request, rsp);
                finish_item(rsp);
            end
        endtask
    endclass : req_ack_responder_seq

    class req_ack_driver #(type data_t = logic, type rdata_t = logic)
        extends uvm_driver #(req_ack_item#(data_t, rdata_t)) implements a2c_replay_lanes, a2c_lane_waits;
        typedef virtual req_ack_if #(.data_t(data_t), .rdata_t(rdata_t)) vif_t;
        typedef a2c_replay_log #(rdata_t) replay_t;
        // LANE_REQUESTED: a lane that has seen req and has no response yet:
        // a DUT lane whose responder has not answered, or a model lane
        // waiting for the DUT lane until its requester withdraws req.
        typedef enum {LANE_IDLE, LANE_REQUESTED, LANE_WAIT, LANE_ACK} lane_state_e;

        req_ack_config#(data_t, rdata_t) cfg;
        // dst role in Mode B only.
        replay_t                         replay;

        // src role in Mode B: the agent's model_cmp, and the passive agents
        // on each lane's pin set, indexed by a2c_lane_e, which the master
        // tells of a dead lane.
        a2c_comparator_base              cmp;
        a2c_pin_watchers                 watchers[2];
        // src role: bounds how long one lane may trail the other and how
        // long the lanes may stall in Mode B, and keeps which lanes are
        // dead.
        a2c_lane_watchdog                wd;

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

        `uvm_component_param_utils(req_ack_driver#(data_t, rdata_t))

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

        protected function void drive_req(bit r);
            for (int l = 0; l < lanes; l++) if (!wd.dead[l]) lane[l].req <= r;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back requests go out on consecutive clocks, and req drops
        // on the first drive point with no item.
        protected virtual task run_src();
            wd = new(this, cfg.port_name, lanes, "item", "every open and later item completes at once, with the rdata it was sent with");
            wd.cmp      = cmp;
            wd.watchers = watchers;
            wd.configure();
            for (int l = 0; l < lanes; l++) begin
                lane[l].req  <= 1'b0;
                lane[l].data <= '0;
            end
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
                    drive_req(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    drive_req(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                for (int l = 0; l < lanes; l++) begin
                    if (wd.dead[l]) continue;
                    lane[l].req  <= 1'b1;
                    lane[l].data <= req.data;
                end
                wait_transfer();
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last live lane's transfer,
        // which is the rising edge before it, with the DUT lane's rdata in
        // req, or the model lane's once the DUT lane is dead. A lane whose
        // transfer has happened holds req low from the next drive point on. In
        // Mode B wd bounds how long one lane may trail the other and how long
        // the lanes may stall (a2c_lane_watchdog), and a lane it declares dead
        // drops out of the wait.
        protected task wait_transfer();
            bit     pending[2];
            bit     took[2];
            bit     finished[2];
            rdata_t rdata[2];
            wd.begin_item();
            for (int l = 0; l < lanes; l++) pending[l] = !wd.dead[l];
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    took[l]     = pending[l] && lane[l].ack === 1'b1;
                    pending[l] &= !took[l];
                    finished[l] |= took[l];
                    if (took[l]) rdata[l] = lane[l].rdata;
                    if (took[l] && l == A2C_DUT_LANE) req.rdata = rdata[l];
                end
                wd.step(took, pending);
                cfg.clk_vif.drive_edge();
                if (!pending[A2C_DUT_LANE] && !pending[A2C_MODEL_LANE]) break;
                for (int l = 0; l < lanes; l++) begin
                    if (finished[l]) lane[l].req <= 1'b0;
                end
            end
            if (!finished[A2C_DUT_LANE] && finished[A2C_MODEL_LANE]) req.rdata = rdata[A2C_MODEL_LANE];
        endtask

        virtual function string waiting_for(a2c_lane_e l);
            return $sformatf("the request of data=%p", req.data);
        endfunction

        // Mode B: a dead lane keeps an asserted req and its payload until
        // that transfer happens, as the protocol requires, and drops req at
        // the drive point after it. No later item drives the lane.
        protected task release_dead();
            bit took[2];
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < 2; l++) took[l] = wd.dead[l] && lane[l].req === 1'b1 && lane[l].ack === 1'b1;
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < 2; l++) if (took[l]) lane[l].req <= 1'b0;
            end
        endtask

        // ack and rdata are driven for one clock per transfer, and rise only
        // after req has been sampled, so with no delay a transfer takes two
        // clocks. rdata is zero while ack is low. One process serves every
        // lane, taking the DUT lane first, so a model lane waiting on
        // request n replays it on the clock the DUT lane takes its response.
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
                    if (state[l] == LANE_IDLE && lane[l].req === 1'b1) begin
                        state[l] = LANE_REQUESTED;
                        starts[l]++;
                    end
                end
                at_edge = 0;
                if (state[A2C_DUT_LANE] == LANE_REQUESTED) begin
                    fetch_response(at_edge);
                    if (!at_edge) begin
                        delay[A2C_DUT_LANE] = req.delay;
                        rdata[A2C_DUT_LANE] = req.rdata;
                        if (replay != null) replay.record(rdata[A2C_DUT_LANE], delay[A2C_DUT_LANE]);
                        state[A2C_DUT_LANE] = LANE_WAIT;
                    end
                end
                // The model lane's requester withdrew the request it waited
                // on, which the monitor reports as A2C_HOLD. No response was
                // taken for it, so the lane goes back to idle and waits for
                // no record.
                if (lanes == 2 && state[A2C_MODEL_LANE] == LANE_REQUESTED && lane[A2C_MODEL_LANE].req !== 1'b1) begin
                    starts[A2C_MODEL_LANE]--;
                    replay.cancel_wait();
                    state[A2C_MODEL_LANE] = LANE_IDLE;
                end
                if (lanes == 2 && state[A2C_MODEL_LANE] == LANE_REQUESTED && replay.can_replay()) begin
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
    endclass : req_ack_driver

    class req_ack_monitor #(type data_t = logic, type rdata_t = logic) extends uvm_monitor;
        req_ack_config#(data_t, rdata_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual req_ack_if #(.data_t(data_t), .rdata_t(rdata_t)) vif;
        // One item per completed transfer, with data and rdata.
        uvm_analysis_port #(req_ack_item#(data_t, rdata_t)) ap;
        // One item per request, data only, on the clock the request is first
        // seen.
        uvm_analysis_port #(req_ack_item#(data_t, rdata_t)) req_ap;

        `uvm_component_param_utils(req_ack_monitor#(data_t, rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap     = new("ap", this);
            req_ap = new("req_ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            logic   req;
            logic   ack;
            data_t  data;
            rdata_t rdata;
            data_t  held;
            bit     waiting = 0;
            req_ack_item#(data_t, rdata_t) item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                req   = vif.req;
                ack   = vif.ack;
                data  = vif.data;
                rdata = vif.rdata;
                // A source waiting for ack must hold req and data until the transfer.
                if (waiting && (req !== 1'b1 || data !== held)) begin
                    string what = (req !== 1'b1) ? "req dropped" : "data changed";
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before ack of %h", cfg.port_name, what, held))
                end
                if (ack === 1'b1 && req !== 1'b1) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: ack is high with req %b", cfg.port_name, req))
                end
                if (req === 1'b1 && !waiting) begin
                    item = req_ack_item#(data_t, rdata_t)::type_id::create("request");
                    item.data = data;
                    req_ap.write(item);
                end
                waiting = (req === 1'b1 && ack !== 1'b1);
                held    = data;
                // X/Z checks only fire on a 4-state boundary. Across a 2-state
                // SystemC boundary an X or Z from the DUT arrives as 0.
                if ($isunknown(req)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: req is %b after reset release", cfg.port_name, req))
                    continue;
                end
                if (req !== 1'b1) continue;
                if ($isunknown(data)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: data has X or Z while req is high: %h", cfg.port_name, data))
                end
                if (ack !== 1'b1) continue;
                if ($isunknown(rdata)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: rdata has X or Z while ack is high: %h", cfg.port_name, rdata))
                end
                // Each transfer counts for the joint stall rule (a2c_joint_watch).
                a2c_joint_watch::handshake();
                item = req_ack_item#(data_t, rdata_t)::type_id::create("item");
                item.data  = data;
                item.rdata = rdata;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h %0h", data, rdata)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : req_ack_monitor

    class req_ack_agent #(type data_t = logic, type rdata_t = logic) extends uvm_agent;
        typedef req_ack_item#(data_t, rdata_t)   item_t;
        typedef req_ack_config#(data_t, rdata_t) config_t;
        // Finds the passive agents on the DUT pin set, whose model_cmps a cut of
        // the active agent's replay log also cuts, and tells a passive agent
        // whether an active one has claimed the pin set.
        typedef a2c_pin_registry #(virtual req_ack_if #(.data_t(data_t), .rdata_t(rdata_t))) registry_t;

        req_ack_config#(data_t, rdata_t)    cfg;
        req_ack_driver#(data_t, rdata_t)    drv;
        req_ack_sequencer#(data_t, rdata_t) sqr;
        req_ack_monitor#(data_t, rdata_t)   mon;
        // Mode B only.
        req_ack_monitor#(data_t, rdata_t)   model_mon;
        a2c_in_order_comparator #(item_t)   model_cmp;

        `uvm_component_param_utils(req_ack_agent#(data_t, rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(req_ack_config#(data_t, rdata_t))::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "req_ack_agent has no cfg")
            end
            mon = req_ack_monitor#(data_t, rdata_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = req_ack_monitor#(data_t, rdata_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                model_cmp = a2c_in_order_comparator#(item_t)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active != UVM_ACTIVE) return;
            drv = req_ack_driver#(data_t, rdata_t)::type_id::create("drv", this);
            drv.cfg = cfg;
            sqr = req_ack_sequencer#(data_t, rdata_t)::type_id::create("sqr", this);
            // A set from the test or env is higher in the hierarchy, so it
            // wins over this one during build.
            if (cfg.role == A2C_DST) begin
                uvm_config_db#(uvm_object_wrapper)::set(this, "sqr.run_phase", "default_sequence",
                                                        req_ack_responder_seq#(data_t, rdata_t)::type_id::get());
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
                if (drv != null && drv.replay != null) begin
                    drv.replay.cmp      = model_cmp;
                    drv.replay.watchers = registry_t::of(cfg.vif);
                    registry_t::of(cfg.vif).owner = get_full_name();
                end
                if (drv != null && cfg.role == A2C_SRC) begin
                    drv.cmp                      = model_cmp;
                    drv.watchers[A2C_DUT_LANE]   = registry_t::of(cfg.vif);
                    drv.watchers[A2C_MODEL_LANE] = registry_t::of(cfg.model_vif);
                    registry_t::of(cfg.vif).owner = get_full_name();
                end
                if (drv == null) registry_t::of(cfg.vif).cmps.push_back(model_cmp);
            end
            if (sqr == null) return;
            drv.seq_item_port.connect(sqr.seq_item_export);
            if (cfg.role == A2C_DST) begin
                mon.req_ap.connect(sqr.request_fifo.analysis_export);
            end
        endfunction

        // A passive Mode B agent says so when no active agent has claimed
        // its pin set, since its model_cmp then misses the drain's cuts or
        // the master's lane deaths.
        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            if (drv == null && model_cmp != null) registry_t::note_unowned(cfg.vif, this, cfg.port_name);
        endfunction
    endclass : req_ack_agent

endpackage : req_ack_uvm_pkg

`endif // REQ_ACK_UVM_PKG_SV
