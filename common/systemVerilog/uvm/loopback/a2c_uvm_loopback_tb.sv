`timescale 1ns/1ps

// Loopback tests of the interface agents and of a2c_uvm_pkg's classes, with
// no DUT: on each interface a src agent drives a dst agent, and a scoreboard
// matches what the dst agent's monitor reports against the items the test
// sent. The tests are in the *_lb_tests.svh files this package includes.
// run_loopback.sh builds this and runs every test those files declare.
package a2c_uvm_loopback_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;
    import rdy_vld_uvm_pkg::*;
    import axi4_stream_uvm_pkg::*;
    import raw_uvm_pkg::*;
    import status_uvm_pkg::*;
    import apb_uvm_pkg::*;
    import push_ack_uvm_pkg::*;
    import notify_ack_uvm_pkg::*;
    import req_ack_uvm_pkg::*;
    import pop_ack_uvm_pkg::*;
    import memory_uvm_pkg::*;
    import external_reg_uvm_pkg::*;
    import axi_read_uvm_pkg::*;
    import axi_write_uvm_pkg::*;

    typedef struct packed {
        logic [3:0]  tag;
        logic [19:0] value;
    } lb_data_t;

    // Clearing it stops clk3 at its level then.
    bit lb_clk3_run = 1;
    // clk6's half period in ns, which a test may change mid-run.
    real lb_clk6_half_ns = 5;
    // Each rise makes one runt pulse on clk7, 0.5ns into its next low phase.
    bit lb_clk7_runt;
    // Clearing it stops clk8 low at the end of its burst and gap then.
    bit lb_clk8_run = 1;

    virtual class lb_scoreboard_base extends uvm_component;
        int unsigned matched;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass : lb_scoreboard_base

    // Matches each reported item against the oldest one not yet matched. A
    // sequence adds an item to expected before the driver puts it on the
    // pins, so the item is waiting when the monitor reports it.
    class lb_scoreboard #(type ITEM = uvm_sequence_item) extends lb_scoreboard_base;
        uvm_analysis_imp #(ITEM, lb_scoreboard#(ITEM)) imp;
        ITEM         expected[$];
        // A raw monitor reports every clock, so before the first sent item it
        // reports the idle value and after the last it repeats that item.
        bit          free_running;

        `uvm_component_param_utils(lb_scoreboard#(ITEM))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            imp = new("imp", this);
        endfunction

        virtual function void write(ITEM t);
            if (expected.size() == 0) begin
                if (!free_running) begin
                    `uvm_error("LB_EXTRA", $sformatf("reported %s after every sent item matched", t.convert2string()))
                end
                return;
            end
            if (!t.compare(expected[0])) begin
                if (free_running && matched == 0) return;
                `uvm_error("LB_MISMATCH", $sformatf("item %0d: reported %s, sent %s", matched, t.convert2string(),
                                                    expected[0].convert2string()))
            end
            void'(expected.pop_front());
            matched++;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            if (expected.size() != 0) begin
                `uvm_error("LB_MISSING", $sformatf("%0d sent items never reported, %0d matched", expected.size(), matched))
            end
        endfunction
    endclass : lb_scoreboard

    class lb_base_test extends uvm_test;
        virtual a2c_clk_if clk_vif;
        int unsigned       n_items = 400;

        `uvm_component_utils(lb_base_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk", clk_vif)) begin
                `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk'")
            end
        endfunction

        // Waits until the scoreboard has matched target items, or fails after
        // max_clocks.
        task wait_matched(lb_scoreboard_base sb, int unsigned target, int unsigned max_clocks);
            int unsigned clocks = 0;
            while (sb.matched < target && clocks < max_clocks) begin
                clk_vif.sample_edge();
                clocks++;
            end
            if (sb.matched < target) begin
                `uvm_error("LB_TIMEOUT", $sformatf("matched %0d of %0d items in %0d clocks", sb.matched, target, max_clocks))
            end
        endtask

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) begin
                `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
            end
        endfunction
    endclass : lb_base_test

    // An a2c_error_demoter that keeps the text of each message it demotes.
    class lb_recording_demoter extends a2c_error_demoter;
        string messages[$];

        `uvm_object_utils(lb_recording_demoter)

        function new(string name = "lb_recording_demoter");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_severity() == UVM_ERROR && get_id() == demote_id) messages.push_back(get_message());
            return super.catch();
        endfunction

        // How many kept messages hold sub.
        function int unsigned count(string sub);
            int unsigned n = 0;
            foreach (messages[i]) n += a2c_contains(messages[i], sub);
            return n;
        endfunction
    endclass : lb_recording_demoter

    // For each log in logs, the DUT lane's start count on the clock of the
    // log's latest cut, and the time of that clock. Both are read 1ps after
    // the rising edge the drain decides at, before any lane starts again.
    class lb_cut_tracker extends uvm_component;
        a2c_replay_log_base logs[$];
        int unsigned        starts_at_cut[a2c_replay_log_base];
        realtime            cut_time[a2c_replay_log_base];

        `uvm_component_utils(lb_cut_tracker)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            foreach (logs[i]) begin
                automatic a2c_replay_log_base log = logs[i];
                fork
                    track(log);
                join_none
            end
        endtask

        // A drain that re-cuts on its first clock replaces one cut with
        // another between two looks, so a change of cut is a new cut.
        protected task track(a2c_replay_log_base log);
            int unsigned last_cut = 0;
            forever begin
                @(log.clk_vif.cb);
                #1ps;
                if (log.get_cut() != 0 && log.get_cut() != last_cut) begin
                    starts_at_cut[log] = log.driver.lane_starts(A2C_DUT_LANE);
                    cut_time[log]      = $realtime;
                end
                last_cut = log.get_cut();
            end
        endtask
    endclass : lb_cut_tracker

    // What every Mode B test shares: a demoter on demote_id that records
    // the messages, and a report_phase check that it demoted exactly
    // want_errors, each kept message holding want_text when set. A test
    // adds the logs whose cuts it checks to tracker.logs.
    class lb_mode_b_base extends lb_base_test;
        lb_recording_demoter demoter;
        string               demote_id = "A2C_MODEL_CMP";
        int unsigned         want_errors = 0;
        string               want_text[$];
        lb_cut_tracker       tracker;

        `uvm_component_utils(lb_mode_b_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            demoter = lb_recording_demoter::type_id::create("demoter");
            demoter.demote_id = demote_id;
            uvm_report_cb::add(null, demoter);
            tracker = lb_cut_tracker::type_id::create("tracker", this);
        endfunction

        // A busy port's run ends at the drain's cut, after more than floor
        // transfers. The cut keeps the transfers the DUT lane had started on
        // the clock of the cut, they are paired, and each lane has completed
        // them all.
        protected function void check_cut(a2c_replay_log_base log, int unsigned floor, int unsigned pairs, int unsigned dut_done,
                                          int unsigned model_done);
            int unsigned cut = log.get_cut();
            if (cut <= floor) `uvm_error("LB_MODE_B", $sformatf("the drain cut the run after transfer %0d, expected one after %0d", cut, floor))
            // A cut the drain reaches on its own clock ends the run before
            // the tracker's look 1ps later.
            if (!tracker.starts_at_cut.exists(log) && cut != 0 && $realtime == log.clk_vif.last_rise) begin
                tracker.starts_at_cut[log] = log.driver.lane_starts(A2C_DUT_LANE);
                tracker.cut_time[log]      = $realtime;
            end
            if (!tracker.starts_at_cut.exists(log)) begin
                `uvm_error("LB_MODE_B", $sformatf("the tracker saw no cut of %s", log.get_full_name()))
            end else if (tracker.starts_at_cut[log] != cut) begin
                `uvm_error("LB_MODE_B", $sformatf("the cut keeps %0d transfers, but the DUT lane had started %0d on the clock of the cut",
                                                  cut, tracker.starts_at_cut[log]))
            end
            if (pairs != cut) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d transfers, expected the %0d the cut keeps", pairs, cut))
            if (dut_done < cut || model_done < cut) begin
                `uvm_error("LB_MODE_B", $sformatf("the lanes completed %0d and %0d transfers, short of the %0d the cut keeps", dut_done, model_done, cut))
            end
            if (uvm_report_server::get_server().get_id_count("A2C_CUT") == 0) `uvm_error("LB_MODE_B", "no A2C_CUT report of the cut")
        endfunction

        // A drain that cuts at its deadline ends at most quiet clocks after
        // it. The clock counter races the drain on each edge, so took may be
        // one off.
        protected function void check_cut_time(int unsigned took, int unsigned quiet, int unsigned deadline);
            if (took + 1 < deadline || took > deadline + quiet + 1) begin
                `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected a cut at its deadline of %0d and an end within %0d clocks more",
                                                  took, deadline, quiet))
            end
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (demoter.demoted != want_errors) begin
                `uvm_error("LB_MODE_B", $sformatf("expected %0d %s, got %0d: %p", want_errors, demote_id, demoter.demoted,
                                              demoter.messages))
            end
            foreach (want_text[i]) begin
                if (demoter.count(want_text[i]) == 0) begin
                    `uvm_error("LB_MODE_B", $sformatf("no %s message holds '%s': %p", demote_id, want_text[i], demoter.messages))
                end
            end
            super.report_phase(phase);
        endfunction
    endclass : lb_mode_b_base

    // Sends a prepared list of items in order.
    class lb_list_seq #(type T = uvm_sequence_item) extends uvm_sequence #(T);
        T items[$];

        `uvm_object_param_utils(lb_list_seq#(T))

        function new(string name = "lb_list_seq");
            super.new(name);
        endfunction

        virtual task body();
            foreach (items[i]) begin
                start_item(items[i]);
                finish_item(items[i]);
            end
        endtask
    endclass : lb_list_seq

    // Keeps every item a monitor reports, with the time it reported it.
    class lb_arrivals #(type T = uvm_sequence_item) extends uvm_subscriber #(T);
        T        items[$];
        realtime at[$];

        `uvm_component_param_utils(lb_arrivals#(T))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void write(T t);
            items.push_back(t);
            at.push_back($realtime);
        endfunction
    endclass : lb_arrivals

    // What a Mode B test of a handshake port varies. LB_DUT_EXTRA and
    // LB_MODEL_EXTRA give one lane's peer one transfer more; LB_DRAIN holds
    // the model lane's last transfer back until after the test drops its
    // objection; LB_BUSY keeps both peers sending after the drop, the model
    // lane's a clock behind with the same gaps, and LB_BUSY_ZERO does so
    // with no gaps. LB_SLOW keeps both peers sending after the drop too,
    // with gaps that let each lane lead in turn, to an A2C_DST agent whose
    // responder takes clocks to answer. LB_TAIL sends 60 transfers after the
    // drop, the model lane's a clock behind, and stops. Its only gap, of 10
    // clocks before the 31st, idles the port for less than the quiet window.
    // LB_AFTER_EXPIRY sends the last transfer in a second round, after a
    // first drain that expired, and one transfer more in a third round,
    // after a second drain that did not.
    typedef enum {LB_MATCH, LB_MODEL_LEADS, LB_DUT_EXTRA, LB_MODEL_EXTRA, LB_DRAIN, LB_BUSY, LB_BUSY_ZERO, LB_SLOW,
                  LB_TAIL, LB_MISMATCH, LB_AFTER_EXPIRY} lb_variant_e;

    // Mode B on one push_ack, notify_ack, req_ack or pop_ack port. agent,
    // the agent under test, has the port as its DUT lane and <port>_model
    // as its model lane, and each lane has a single-lane peer of the other
    // role. As A2C_SRC the agent sends items and the peers answer. As
    // A2C_DST the peers send items and model_items, with gaps drawn per
    // lane, so either lane may reach a transfer first, and the agent
    // answers. Each lane's dst side must report its expected items in order.
    // As A2C_SRC an item must start on either lane only after both lanes
    // completed the one before, and the lanes must complete some items on
    // different clocks. As A2C_DST the model lane must never complete a
    // transfer before the DUT lane, each lane must reach some transfers
    // first, and model_cmp must pair every transfer. A family's test
    // defines new_item() and configure(), and sets role and variant.
    virtual class lb_hs_mode_b #(type AGENT_T = uvm_agent, type ITEM_T = uvm_sequence_item,
                                 type CFG_T = uvm_object, type VIF_T = int) extends lb_mode_b_base;
        string               port;
        a2c_role_e           role = A2C_SRC;
        lb_variant_e         variant = LB_MATCH;
        AGENT_T              agent;
        AGENT_T              peer;
        AGENT_T              model_peer;
        CFG_T                agent_cfg;
        CFG_T                peer_cfg;
        CFG_T                model_peer_cfg;
        VIF_T                vif;
        VIF_T                model_vif;
        ITEM_T               items[$];
        ITEM_T               model_items[$];
        // Indexed by a2c_lane_e: what each lane's dst side must report.
        ITEM_T               expected[2][$];
        // LB_MISMATCH: the transfer whose model lane item differs.
        int unsigned         mismatch_at;
        // A model lane item check_phase does not check, or -1.
        int                  skip_model = -1;
        lb_arrivals#(ITEM_T) arrivals;
        lb_arrivals#(ITEM_T) model_arrivals;
        int unsigned         drain_quiet = 20;
        int unsigned         drain_deadline = 400;
        int unsigned         clocks;
        int unsigned         dropped_at;
        int unsigned         pending_at_drop;
        bit                  done[2];
        // A2C_DST: transfers the model lane reached first, and in all.
        int unsigned         model_led;
        realtime             drop_time;
        // phase_ready_to_end() calls; LB_AFTER_EXPIRY: the clock of the
        // second, what the replay log held when the test dropped the second
        // and third time, and whether the DUT lane was inside the third
        // transfer then.
        int unsigned         ready_calls;
        int unsigned         resumed_at;
        int unsigned         pending_at_second_drop;
        int unsigned         pending_at_third_drop;
        bit                  busy_at_third_drop;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        pure virtual function ITEM_T new_item(int unsigned i);

        // Sets the delays and responders of the three configs.
        virtual function void configure();
        endfunction

        // Changes the item so that model_cmp reports it.
        virtual function void corrupt(ITEM_T it);
        endfunction

        // The peers keep sending after the test drops its objection.
        protected function bit busy();
            return variant inside {LB_BUSY, LB_BUSY_ZERO, LB_SLOW};
        endfunction

        protected function ITEM_T copy(ITEM_T it);
            ITEM_T c;
            $cast(c, it.clone());
            return c;
        endfunction

        protected function void expect_copies(a2c_lane_e lane, ITEM_T list[$]);
            foreach (list[i]) expected[lane].push_back(copy(list[i]));
        endfunction

        protected function CFG_T lane_cfg(string name, VIF_T lane_vif, a2c_role_e lane_role, string lane_port);
            CFG_T cfg = CFG_T::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = lane_port;
            return cfg;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_role_e peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            int unsigned tail = busy() ? 10 * n_items : (variant == LB_TAIL) ? 60 : 0;
            if (variant inside {LB_DUT_EXTRA, LB_MODEL_EXTRA} || busy()) demote_id = "A2C_REPLAY";
            mismatch_at = $urandom_range(n_items - 1, 0);
            super.build_phase(phase);
            if (!uvm_config_db#(VIF_T)::get(this, "", port, vif)) `uvm_fatal("LB_CFG", {"no interface ", port})
            if (!uvm_config_db#(VIF_T)::get(this, "", {port, "_model"}, model_vif)) `uvm_fatal("LB_CFG", {"no interface ", port, "_model"})
            agent_cfg = lane_cfg("agent_cfg", vif, role, port);
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lane_cfg("peer_cfg", vif, peer_role, port);
            model_peer_cfg = lane_cfg("model_peer_cfg", model_vif, peer_role, {port, "_model"});
            configure();
            uvm_config_db#(CFG_T)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(CFG_T)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(CFG_T)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent          = AGENT_T::type_id::create("agent", this);
            peer           = AGENT_T::type_id::create("peer", this);
            model_peer     = AGENT_T::type_id::create("model_peer", this);
            arrivals       = lb_arrivals#(ITEM_T)::type_id::create("arrivals", this);
            model_arrivals = lb_arrivals#(ITEM_T)::type_id::create("model_arrivals", this);
            for (int unsigned i = 0; i < n_items + tail; i++) begin
                ITEM_T it = new_item(i);
                ITEM_T m;
                $cast(m, it.clone());
                case (variant)
                    LB_MODEL_LEADS: begin
                        it.gap = $urandom_range(3, 1);
                        m.gap  = 0;
                    end
                    LB_BUSY: begin
                        it.gap = $urandom_range(3, 0);
                        m.gap  = it.gap + (i == 0);
                    end
                    LB_BUSY_ZERO: begin
                        it.gap = 0;
                        m.gap  = (i == 0);
                    end
                    LB_TAIL: begin
                        it.gap = (i == n_items + 30) ? 10 : 0;
                        m.gap  = (i == 0) + it.gap;
                    end
                    // The model lane's gaps run shorter than the DUT lane's
                    // for ten transfers and longer for the next ten, so each
                    // lane leads in turn. Equal gap ranges let the model
                    // lane fall behind for a whole run on some seeds.
                    default: begin
                        it.gap = $urandom_range(3, 0);
                        m.gap  = ((i / 10) % 2 == 0) ? $urandom_range(1, 0) : $urandom_range(3, 2);
                    end
                endcase
                items.push_back(it);
                model_items.push_back(m);
            end
            // Copies, because an A2C_SRC driver writes the rdata it gets into
            // the item it sent.
            expect_copies(A2C_DUT_LANE, items);
            expect_copies(A2C_MODEL_LANE, (role == A2C_SRC) ? items : model_items);
            case (variant)
                LB_DUT_EXTRA: begin
                    items.push_back(new_item(n_items));
                    expected[A2C_DUT_LANE].push_back(copy(items[n_items]));
                    want_errors = 1;
                    want_text.push_back($sformatf("uvm_test_top.agent.drv.replay: end of test with 1 responses the DUT lane recorded and the model lane never replayed, from transaction %0d",
                                                  n_items + 1));
                end
                LB_MODEL_EXTRA: begin
                    model_items.push_back(new_item(n_items));
                    want_errors = 1;
                    want_text.push_back($sformatf("uvm_test_top.agent.drv.replay: the model lane waited for transaction %0d, which the DUT lane never recorded",
                                                  n_items + 1));
                end
                LB_DRAIN: model_items[n_items - 1].gap = 60;
                LB_MISMATCH: begin
                    want_errors = 1;
                    want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT ", mismatch_at + 1));
                    // A2C_SRC: the family's configure() makes model_peer
                    // answer transfer mismatch_at differently.
                    if (role == A2C_DST) begin
                        corrupt(model_items[mismatch_at]);
                        corrupt(expected[A2C_MODEL_LANE][mismatch_at]);
                    end else begin
                        skip_model = mismatch_at;
                    end
                end
                LB_BUSY, LB_BUSY_ZERO, LB_SLOW: begin
                    drain_quiet    = 30;
                    drain_deadline = 300;
                end
                LB_TAIL: begin
                    drain_quiet    = 30;
                    drain_deadline = 400;
                end
                // The model lane's second-to-last transfer is 40 clocks late,
                // so the first drain expires with it pending, and its last
                // two transfers are 30 clocks behind the DUT lane's.
                LB_AFTER_EXPIRY: begin
                    ITEM_T extra = new_item(n_items);
                    ITEM_T model_extra;
                    $cast(model_extra, extra.clone());
                    drain_quiet    = 10;
                    drain_deadline = 10;
                    model_items[n_items - 2].gap = 40;
                    model_items[n_items - 1].gap = 30;
                    extra.gap       = 0;
                    model_extra.gap = 30;
                    items.push_back(extra);
                    model_items.push_back(model_extra);
                    expected[A2C_DUT_LANE].push_back(copy(extra));
                    expected[A2C_MODEL_LANE].push_back(copy(model_extra));
                end
                default: ;
            endcase
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (role == A2C_SRC) begin
                peer.mon.ap.connect(arrivals.analysis_export);
                model_peer.mon.ap.connect(model_arrivals.analysis_export);
                return;
            end
            agent.mon.ap.connect(arrivals.analysis_export);
            agent.model_mon.ap.connect(model_arrivals.analysis_export);
            agent.drv.replay.drain_quiet_cycles    = drain_quiet;
            agent.drv.replay.drain_deadline_cycles = drain_deadline;
            tracker.logs.push_back(agent.drv.replay);
            // As the env marks a counted port, whose counter reports the
            // unpaired transfer.
            if (variant == LB_DUT_EXTRA) agent.model_cmp.counted = 1;
        endfunction

        protected task send(AGENT_T src, ITEM_T list[$], a2c_lane_e lane);
            lb_list_seq#(ITEM_T) seq = lb_list_seq#(ITEM_T)::type_id::create("seq");
            seq.items = list;
            seq.start(src.sqr);
            done[lane] = 1;
        endtask

        // A model lane left waiting never finishes, so after the DUT lane is
        // done the test waits only while the model lane completes a transfer
        // at least once every 50 clocks.
        virtual task wait_drop();
            int unsigned idle = 0;
            if (variant == LB_AFTER_EXPIRY) begin
                while (arrivals.items.size() < n_items - 1) clk_vif.sample_edge();
                return;
            end
            if (variant inside {LB_DRAIN, LB_TAIL} || busy()) begin
                while (arrivals.items.size() < n_items) clk_vif.sample_edge();
                return;
            end
            wait (done[A2C_DUT_LANE]);
            while (!done[A2C_MODEL_LANE] && idle < 50) begin
                int unsigned last = model_arrivals.items.size();
                clk_vif.sample_edge();
                idle = (model_arrivals.items.size() == last) ? idle + 1 : 0;
            end
            repeat (2) clk_vif.sample_edge();
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                begin
                    bit was_waiting = 0;
                    forever begin
                        clk_vif.sample_edge();
                        clocks++;
                        if (role == A2C_DST) begin
                            if (agent.drv.replay.model_waiting() && !was_waiting) model_led++;
                            was_waiting = agent.drv.replay.model_waiting();
                        end
                    end
                end
            join_none
            if (role == A2C_SRC) begin
                send(agent, items, A2C_DUT_LANE);
                repeat (2) clk_vif.sample_edge();
            end else begin
                ITEM_T first[$] = items;
                ITEM_T model_first[$] = model_items;
                if (variant == LB_AFTER_EXPIRY) begin
                    repeat (2) begin
                        void'(first.pop_back());
                        void'(model_first.pop_back());
                    end
                end
                fork
                    send(peer, first, A2C_DUT_LANE);
                    send(model_peer, model_first, A2C_MODEL_LANE);
                join_none
                wait_drop();
                pending_at_drop = agent.drv.replay.pending();
            end
            dropped_at = clocks;
            drop_time  = $realtime;
            phase.drop_objection(this);
        endtask

        // LB_AFTER_EXPIRY: the second call comes when the expired drain
        // drops. The test then holds the run phase again until the model
        // lane has made its late transfer, raises the deadline, and sends
        // the last transfer, dropping when the DUT lane has completed it.
        // The model lane started a transfer after the expiry, so only a
        // second drain keeps the run phase alive until it replays the last.
        // The fourth call comes when that drain drops, and the test sends
        // one transfer more the same way. The model lane has not started it
        // at the third drop, so only the replay log it left pending can
        // bring the third drain; the expiry of the first must not stop it.
        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (phase.get_imp() != uvm_run_phase::get()) return;
            ready_calls++;
            if (variant != LB_AFTER_EXPIRY || !(ready_calls inside {2, 4})) return;
            if (ready_calls == 2) resumed_at = clocks;
            phase.raise_objection(this, "a later transfer");
            fork last_round(phase); join_none
        endfunction

        // Sends transfer n_items - 1 in the second round and n_items in the
        // third.
        protected task last_round(uvm_phase phase);
            int unsigned i = (ready_calls == 2) ? n_items - 1 : n_items;
            ITEM_T last[$];
            ITEM_T model_last[$];
            last.push_back(items[i]);
            model_last.push_back(model_items[i]);
            while (model_arrivals.items.size() < i) clk_vif.sample_edge();
            agent.drv.replay.drain_deadline_cycles = 400;
            before_round(i);
            fork
                send(peer, last, A2C_DUT_LANE);
                send(model_peer, model_last, A2C_MODEL_LANE);
            join_none
            wait_round_drop(i);
            if (i == n_items) begin
                pending_at_third_drop = agent.drv.replay.pending();
                busy_at_third_drop    = agent.drv.lane_busy(A2C_DUT_LANE);
            end else begin
                pending_at_second_drop = agent.drv.replay.pending();
            end
            phase.drop_objection(this, "the DUT lane completed the transfer");
        endtask

        // Runs before transfer i of a later round is sent.
        virtual function void before_round(int unsigned i);
        endfunction

        // Returns when the DUT lane has completed transfer i.
        virtual task wait_round_drop(int unsigned i);
            while (arrivals.items.size() <= i) clk_vif.sample_edge();
        endtask

        protected function void check_lane(a2c_lane_e lane, lb_arrivals#(ITEM_T) got);
            int unsigned n = expected[lane].size();
            if (busy()) n = got.items.size();
            else if (got.items.size() != n) begin
                `uvm_error("LB_MODE_B", $sformatf("the %s lane reported %0d transfers, expected %0d", a2c_lane_name(lane),
                                                  got.items.size(), n))
            end
            for (int unsigned i = 0; i < n && i < got.items.size(); i++) begin
                if (lane == A2C_MODEL_LANE && i == skip_model) continue;
                if (!got.items[i].compare(expected[lane][i])) begin
                    `uvm_error("LB_MODE_B", $sformatf("%s lane transfer %0d: reported %s, expected %s", a2c_lane_name(lane), i,
                                                      got.items[i].convert2string(), expected[lane][i].convert2string()))
                end
            end
        endfunction

        protected function int unsigned drain_clocks();
            return clocks - dropped_at;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned pairs = (agent.model_cmp == null) ? 0 : agent.model_cmp.get_pairs();
            int unsigned apart = 0;
            int unsigned n = (arrivals.items.size() < model_arrivals.items.size()) ? arrivals.items.size()
                                                                                    : model_arrivals.items.size();
            super.check_phase(phase);
            check_lane(A2C_DUT_LANE, arrivals);
            check_lane(A2C_MODEL_LANE, model_arrivals);
            for (int unsigned i = 0; i < n; i++) begin
                realtime last = (arrivals.at[i] > model_arrivals.at[i]) ? arrivals.at[i] : model_arrivals.at[i];
                if (arrivals.at[i] != model_arrivals.at[i]) apart++;
                if (role == A2C_SRC && i + 1 < n && (arrivals.at[i + 1] <= last || model_arrivals.at[i + 1] <= last)) begin
                    `uvm_error("LB_MODE_B", $sformatf("transfer %0d completed on a lane before both lanes had completed transfer %0d", i + 1, i))
                end
                if (role == A2C_DST && model_arrivals.at[i] < arrivals.at[i]) begin
                    `uvm_error("LB_MODE_B", $sformatf("the model lane completed transfer %0d before the DUT lane", i))
                end
            end
            `uvm_info("LB_STATS", $sformatf("%0d and %0d transfers on the DUT and model lanes, %0d on different clocks; %0d pairs; the model lane led %0d; %0d unreplayed at the drop; the drain took %0d clocks",
                                            arrivals.items.size(), model_arrivals.items.size(), apart, pairs, model_led,
                                            pending_at_drop, drain_clocks()), UVM_NONE)
            if (role == A2C_SRC) begin
                if (apart == 0) `uvm_error("LB_MODE_B", "the lanes completed every transfer on the same clock, so per-lane completion went untested")
                if (agent.model_cmp != null && pairs != n) begin
                    `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d transfers, expected %0d", pairs, n))
                end
                return;
            end
            if (!busy() && pairs != n) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d transfers, expected %0d", pairs, n))
            case (variant)
                LB_MATCH, LB_MISMATCH: begin
                    if (model_led == 0 || model_led >= n) begin
                        `uvm_error("LB_MODE_B", $sformatf("the model lane led %0d of %0d transfers, so one lane never led", model_led, n))
                    end
                end
                LB_MODEL_LEADS: begin
                    if (model_led != n) `uvm_error("LB_MODE_B", $sformatf("the model lane led %0d of %0d transfers", model_led, n))
                end
                // One drain must hold the run phase until the model lane is
                // done: the call at the test's drop and the one at the drain's.
                LB_DRAIN: begin
                    if (pending_at_drop == 0) `uvm_error("LB_MODE_B", "the model lane had replayed every transfer at the drop, so the drain went untested")
                    if (ready_calls != 2) `uvm_error("LB_MODE_B", $sformatf("%0d phase_ready_to_end calls, expected 2", ready_calls))
                end
                LB_AFTER_EXPIRY: begin
                    `uvm_info("LB_STATS", $sformatf("%0d phase_ready_to_end calls; the first drain took %0d clocks; %0d and %0d unreplayed at the second and third drops",
                                                    ready_calls, resumed_at - dropped_at, pending_at_second_drop,
                                                    pending_at_third_drop), UVM_NONE)
                    if (ready_calls < 2) `uvm_error("LB_MODE_B", "the first drain never dropped, so the second round never ran")
                    if (ready_calls < 4) `uvm_error("LB_MODE_B", "the second drain never dropped, so the third round never ran")
                    // The clock counter races the drain on each edge, so it may be one off.
                    if (resumed_at - dropped_at + 1 < 10 || resumed_at - dropped_at > 11) begin
                        `uvm_error("LB_MODE_B", $sformatf("the first drain took %0d clocks, expected its deadline of 10", resumed_at - dropped_at))
                    end
                    if (pending_at_second_drop == 0) begin
                        `uvm_error("LB_MODE_B", "the model lane had replayed the last transfer at the second drop, so the second drain went untested")
                    end
                    if (pending_at_third_drop == 0 && !busy_at_third_drop) begin
                        `uvm_error("LB_MODE_B", "the lanes were done with the extra transfer at the third drop, so the third drain went untested")
                    end
                end
                LB_MODEL_EXTRA, LB_DUT_EXTRA: begin
                    // The clock counter races the drain on each edge, so it may be one off.
                    if (drain_clocks() + 1 < drain_deadline || drain_clocks() > drain_deadline + 1) begin
                        `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected its deadline of %0d", drain_clocks(), drain_deadline))
                    end
                end
                LB_TAIL: begin
                    if (agent.drv.replay.get_cut() != 0) `uvm_error("LB_MODE_B", "the drain cut a port that paused before its deadline")
                    if (arrivals.items.size() != n_items + 60) begin
                        `uvm_error("LB_MODE_B", "the DUT lane stopped before the end of its tail, so the tail went untested")
                    end
                    if (drain_clocks() >= drain_deadline) `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, its whole deadline", drain_clocks()))
                    if (ready_calls != 2) `uvm_error("LB_MODE_B", $sformatf("%0d phase_ready_to_end calls, expected 2", ready_calls))
                end
                LB_BUSY, LB_BUSY_ZERO, LB_SLOW: begin
                    check_cut(agent.drv.replay, n_items, pairs, arrivals.items.size(), model_arrivals.items.size());
                    if (arrivals.items.size() <= n_items) begin
                        `uvm_error("LB_MODE_B", "the DUT lane's peer stopped at the drop, so the busy port went untested")
                    end
                    if (arrivals.items.size() >= items.size()) begin
                        `uvm_error("LB_MODE_B", "the DUT lane's peer ran out of transfers, so the port paused")
                    end
                    if (ready_calls != 2) `uvm_error("LB_MODE_B", $sformatf("%0d phase_ready_to_end calls, expected 2", ready_calls))
                    if (variant == LB_SLOW && model_led == 0) begin
                        `uvm_error("LB_MODE_B", "the model lane never waited for the slow responder")
                    end
                    check_cut_time(drain_clocks(), drain_quiet, drain_deadline);
                end
                default: ;
            endcase
        endfunction
    endclass : lb_hs_mode_b

    `include "rdy_vld_lb_tests.svh"
    `include "axi4_stream_lb_tests.svh"
    `include "raw_lb_tests.svh"
    `include "status_lb_tests.svh"
    `include "apb_lb_tests.svh"
    `include "push_ack_lb_tests.svh"
    `include "notify_ack_lb_tests.svh"
    `include "req_ack_lb_tests.svh"
    `include "pop_ack_lb_tests.svh"
    `include "memory_lb_tests.svh"
    `include "external_reg_lb_tests.svh"
    `include "axi_read_lb_tests.svh"
    `include "axi_write_lb_tests.svh"
    `include "no_backpressure_lb_tests.svh"
    `include "a2c_txn_counter_lb_tests.svh"
    `include "a2c_mem_model_lb_tests.svh"
    `include "a2c_model_cmp_lb_tests.svh"
    `include "a2c_replay_drain_lb_tests.svh"
    `include "a2c_gen_base_test_lb_tests.svh"
    `include "mode_b_unsupported_lb_tests.svh"

endpackage : a2c_uvm_loopback_pkg

module a2c_uvm_loopback_tb;

    import uvm_pkg::*;
    import a2c_uvm_loopback_pkg::*;

    bit clk;
    bit rst_n;

    always #5 clk = ~clk;
    // pa2's clock in push_ack_mode_b_dst_two_clock_test.
    bit clk2;
    always #15 clk2 = ~clk2;
    // A gated clock for the tests of a clock that stops.
    bit clk3;
    always #10 if (lb_clk3_run) clk3 = ~clk3;
    // A clock of 50 times clk's period with no reset, whose rst_n a
    // generated testbench ties high.
    bit clk4;
    always #250 clk4 = ~clk4;
    // A clock that never rises.
    bit clk5;
    // clk one NBA region later, so at each edge every process on clk runs
    // before any process on clk_nba.
    bit clk_nba;
    always @(clk) clk_nba <= clk;
    // A clock whose rate a test changes through lb_clk6_half_ns.
    bit clk6;
    always #(lb_clk6_half_ns) clk6 = ~clk6;
    // A clock of clk3's period that a test can give a runt pulse.
    bit clk7;
    always #10 clk7 = ~clk7;
    always @(posedge lb_clk7_runt) begin
        @(negedge clk7);
        #0.5 clk7 = 1'b1;
        #0.001 clk7 = 1'b0;
    end
    // A clock gated in bursts, as per-transfer APB PCLK gating gives: three
    // rising edges 10ns apart, then a low gap of 47, 53 or 61ns in turn, so
    // no four of its rising edges are ever evenly spaced.
    bit clk8;
    initial begin
        realtime gaps[3] = '{47ns, 53ns, 61ns};
        for (int unsigned b = 0; lb_clk8_run; b++) begin
            repeat (3) begin
                clk8 = 1'b1;
                #5;
                clk8 = 1'b0;
                #5;
            end
            #(gaps[b % 3]);
        end
    end

    // Released on a falling edge, so no driver sees it change at the rising
    // edge it samples.
    initial begin
        repeat (5) @(negedge clk);
        rst_n = 1'b1;
    end

    a2c_clk_if clk_if(.clk(clk), .rst_n(rst_n));
    a2c_clk_if clk2_if(.clk(clk2), .rst_n(rst_n));
    a2c_clk_if clk3_if(.clk(clk3), .rst_n(rst_n));
    a2c_clk_if clk4_if(.clk(clk4), .rst_n(1'b1));
    a2c_clk_if clk5_if(.clk(clk5), .rst_n(rst_n));
    a2c_clk_if clk_nba_if(.clk(clk_nba), .rst_n(rst_n));
    a2c_clk_if clk6_if(.clk(clk6), .rst_n(rst_n));
    a2c_clk_if clk7_if(.clk(clk7), .rst_n(rst_n));
    a2c_clk_if clk8_if(.clk(clk8), .rst_n(rst_n));
    rdy_vld_if #(.data_t(lb_data_t)) rv();
    axi4_stream_if #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis();
    raw_if #(.data_t(lb_data_t)) raw();
    status_if #(.data_t(lb_data_t)) st();
    apb_if #(.addr_t(lb_apb_word_t), .data_t(lb_apb_word_t)) apb();
    // The model lanes of the Mode B tests.
    rdy_vld_if #(.data_t(lb_data_t)) rv_model();
    axi4_stream_if #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis_model();
    raw_if #(.data_t(lb_data_t)) raw_model();
    status_if #(.data_t(lb_data_t)) st_model();
    apb_if #(.addr_t(lb_apb_word_t), .data_t(lb_apb_word_t)) apb_model();
    push_ack_if #(.data_t(lb_data_t)) pa();
    notify_ack_if na();
    req_ack_if #(.data_t(lb_data_t), .rdata_t(lb_rdata_t)) ra();
    pop_ack_if #(.rdata_t(lb_data_t)) po();
    memory_if #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem();
    memory_if #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem2();
    external_reg_if #(.data_t(lb_data_t)) er();
    push_ack_if #(.data_t(lb_data_t)) pa_model();
    push_ack_if #(.data_t(lb_data_t)) pa2();
    push_ack_if #(.data_t(lb_data_t)) pa2_model();
    notify_ack_if na_model();
    req_ack_if #(.data_t(lb_data_t), .rdata_t(lb_rdata_t)) ra_model();
    pop_ack_if #(.rdata_t(lb_data_t)) po_model();
    memory_if #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem_model();
    external_reg_if #(.data_t(lb_data_t)) er_model();
    axi_read_if #(.addr_t(lb_axr_addr_t), .data_t(lb_axr_data_t), .aruser_t(lb_axr_aruser_t),
                  .ruser_t(lb_axr_ruser_t), .id_t(lb_axr_id_t)) axr();
    axi_write_if #(.addr_t(lb_axw_addr_t), .data_t(lb_axw_data_t), .strb_t(lb_axw_strb_t), .awuser_t(lb_axw_awuser_t),
                   .wuser_t(lb_axw_wuser_t), .buser_t(lb_axw_buser_t), .id_t(lb_axw_id_t)) axw();

    initial begin
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk", clk_if);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk2", clk2_if);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk3", clk3_if);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk4", clk4_if);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk5", clk5_if);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk_nba", clk_nba_if);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk6", clk6_if);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk7", clk7_if);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk8", clk8_if);
        uvm_config_db#(rv_vif_t)::set(null, "uvm_test_top", "rv", rv);
        uvm_config_db#(axis_vif_t)::set(null, "uvm_test_top", "axis", axis);
        uvm_config_db#(raw_vif_t)::set(null, "uvm_test_top", "raw", raw);
        uvm_config_db#(st_vif_t)::set(null, "uvm_test_top", "st", st);
        uvm_config_db#(apb_vif_t)::set(null, "uvm_test_top", "apb", apb);
        uvm_config_db#(rv_vif_t)::set(null, "uvm_test_top", "rv_model", rv_model);
        uvm_config_db#(axis_vif_t)::set(null, "uvm_test_top", "axis_model", axis_model);
        uvm_config_db#(raw_vif_t)::set(null, "uvm_test_top", "raw_model", raw_model);
        uvm_config_db#(st_vif_t)::set(null, "uvm_test_top", "st_model", st_model);
        uvm_config_db#(apb_vif_t)::set(null, "uvm_test_top", "apb_model", apb_model);
        uvm_config_db#(pa_vif_t)::set(null, "uvm_test_top", "pa", pa);
        uvm_config_db#(na_vif_t)::set(null, "uvm_test_top", "na", na);
        uvm_config_db#(ra_vif_t)::set(null, "uvm_test_top", "ra", ra);
        uvm_config_db#(po_vif_t)::set(null, "uvm_test_top", "po", po);
        uvm_config_db#(mem_vif_t)::set(null, "uvm_test_top", "mem", mem);
        uvm_config_db#(mem_vif_t)::set(null, "uvm_test_top", "mem2", mem2);
        uvm_config_db#(er_vif_t)::set(null, "uvm_test_top", "er", er);
        uvm_config_db#(pa_vif_t)::set(null, "uvm_test_top", "pa_model", pa_model);
        uvm_config_db#(pa_vif_t)::set(null, "uvm_test_top", "pa2", pa2);
        uvm_config_db#(pa_vif_t)::set(null, "uvm_test_top", "pa2_model", pa2_model);
        uvm_config_db#(na_vif_t)::set(null, "uvm_test_top", "na_model", na_model);
        uvm_config_db#(ra_vif_t)::set(null, "uvm_test_top", "ra_model", ra_model);
        uvm_config_db#(po_vif_t)::set(null, "uvm_test_top", "po_model", po_model);
        uvm_config_db#(mem_vif_t)::set(null, "uvm_test_top", "mem_model", mem_model);
        uvm_config_db#(er_vif_t)::set(null, "uvm_test_top", "er_model", er_model);
        uvm_config_db#(axr_vif_t)::set(null, "uvm_test_top", "axr", axr);
        uvm_config_db#(axw_vif_t)::set(null, "uvm_test_top", "axw", axw);
        run_test();
    end

endmodule : a2c_uvm_loopback_tb
