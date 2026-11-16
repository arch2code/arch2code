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
// both lanes at one drive point, and each lane drops pop once its own transfer
// has happened; the next item starts when both have, with the DUT lane's rdata
// in req. A lane of the A2C_SRC driver that trails the other by
// lane_skew_cycles clocks, or stalls, is declared dead as for the AXI masters
// (a2c_lane_watchdog), and the other lane serves the sequence alone. The
// A2C_DST driver takes response n from its sequencer for the DUT lane's pop n
// and records its rdata and delay; the model lane's pop n gets the same rdata
// after the same delay, and a model lane that reaches pop n first waits until
// the DUT lane has. A responder sequence that takes simulated time to answer
// holds only the DUT lane. The replay log holds the end of the run phase while
// the model lane catches up (a2c_replay_drain). model_cmp compares the
// transfers of the two lanes in order: on the A2C_SRC role for their rdata, on
// the A2C_DST role for their count, since both lanes get the same rdata. What
// the DUT produces that is not compared:
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
            // A field that differs is also passed to comparer, whose
            // miscompares string then names it.
            if (rdata !== rhs_.rdata) void'(comparer.compare_field("rdata", rdata, rhs_.rdata, $bits(rdata)));
            return super.do_compare(rhs, comparer) && (rdata === rhs_.rdata);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", rdata);
        endfunction
    endclass : pop_ack_item

    class pop_ack_config #(type rdata_t = logic) extends a2c_agent_config #(virtual pop_ack_if #(.rdata_t(rdata_t)));
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

    // ack and rdata are driven for one clock per transfer, and rise only
    // after pop has been sampled, so with no delay a transfer takes two
    // clocks. rdata is zero while ack is low. In Mode B the src role
    // returns the DUT lane's rdata in req, or the model lane's once the DUT
    // lane is dead.
    class pop_ack_driver #(type rdata_t = logic)
        extends a2c_lane_driver #(pop_ack_item#(rdata_t), virtual pop_ack_if #(.rdata_t(rdata_t)), pop_ack_config#(rdata_t), rdata_t);
        // src role: the rdata each lane returned.
        protected rdata_t rdata[2];
        // dst role: a fetch of the DUT lane's response is under way, and
        // has returned it in req.
        protected bit     fetching;
        protected bit     fetched;

        `uvm_component_param_utils(pop_ack_driver#(rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            none_left = "every open and later item completes at once, with the rdata it was sent with";
        endfunction

        protected virtual function void drive_request(int l, bit on);
            lane[l].pop <= on;
        endfunction

        protected virtual function bit request_held(int l);
            return lane[l].pop === 1'b1;
        endfunction

        protected virtual function bit request_taken(int l);
            return lane[l].ack === 1'b1;
        endfunction

        protected virtual function int unsigned item_gap();
            return req.gap;
        endfunction

        protected virtual function void take_response(a2c_lane_e l);
            rdata[l] = lane[l].rdata;
        endfunction

        protected virtual function void return_response(a2c_lane_e l);
            req.rdata = rdata[l];
        endfunction

        virtual function string waiting_for(a2c_lane_e l);
            return "a pop";
        endfunction

        protected virtual function bit request_seen(int l);
            return lane[l].pop === 1'b1;
        endfunction

        // Waits for the DUT lane's response in req until the next rising
        // edge, and returns at_edge set if the edge came first. The fetch
        // runs in its own process and outlives the wait, so a responder that
        // takes clocks to answer stalls only the DUT lane. Its response takes
        // effect from the first drive point after it arrives, as it would
        // with get_next_item() called in line.
        protected virtual task respond(output rdata_t r, output int unsigned delay, output bit at_edge);
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
            if (!fetched) return;
            fetched  = 0;
            fetching = 0;
            r        = req.rdata;
            delay    = req.delay;
        endtask

        protected virtual function void idle_response(int l);
            lane[l].ack   <= 1'b0;
            lane[l].rdata <= '0;
        endfunction

        protected virtual function void drive_response(int l, rdata_t r);
            lane[l].ack   <= 1'b1;
            lane[l].rdata <= r;
        endfunction

        protected virtual function void end_response(int l);
            lane[l].ack   <= 1'b0;
            lane[l].rdata <= '0;
            if (l == A2C_DUT_LANE) seq_item_port.item_done();
        endfunction
    endclass : pop_ack_driver

    class pop_ack_monitor #(type rdata_t = logic) extends uvm_monitor implements a2c_starvation_source;
        pop_ack_config#(rdata_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual pop_ack_if #(.rdata_t(rdata_t))     vif;
        // One item per completed transfer, with rdata.
        uvm_analysis_port #(pop_ack_item#(rdata_t)) ap;

        // The counts a2c_rt_checker reads (a2c_starvation_source), from the
        // reset release: the popper waits on clocks with pop high and ack low.
        protected longint unsigned n_samples;
        protected longint unsigned n_withheld;

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
                n_samples++;
                n_withheld += (pop === 1'b1 && ack !== 1'b1);
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
                // Each transfer counts for the joint stall rule (a2c_joint_watch).
                a2c_joint_watch::handshake();
                item = pop_ack_item#(rdata_t)::type_id::create("item");
                item.rdata = rdata;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", rdata)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask

        virtual function void starvation_counts(output longint unsigned samples, output longint unsigned withheld);
            samples  = n_samples;
            withheld = n_withheld;
        endfunction

        virtual function string starvation_port();
            return cfg.port_name;
        endfunction
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
            end
            if (drv != null) drv.join_lanes(this, model_cmp, mon, model_mon);
            else registry_t::join_passive(cfg.vif, cfg.model_vif, mon, model_mon, model_cmp);
        endfunction

        // A passive Mode B agent says so when no active agent has claimed
        // its pin set, since its model_cmp then misses the drain's cuts or
        // the master's lane deaths.
        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            if (drv == null && model_cmp != null) registry_t::note_unowned(cfg.vif, this, cfg.port_name);
        endfunction
    endclass : pop_ack_agent

endpackage : pop_ack_uvm_pkg

`endif // POP_ACK_UVM_PKG_SV
