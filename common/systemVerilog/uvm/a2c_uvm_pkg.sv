`ifndef A2C_UVM_PKG_SV
`define A2C_UVM_PKG_SV

`timescale 1ns/1ps

// What the interface agent packages and the generated environments share.
package a2c_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"

    // The side of the interface an agent plays, the opposite of the DUT
    // port's modport: a DUT dst input gets an A2C_SRC agent.
    typedef enum {A2C_SRC, A2C_DST} a2c_role_e;

    // The A2C_TXN line every monitor logs per transaction: the time in ns,
    // the port, the role, the item's fields, and the packed value in hex so a
    // SystemC test can rebuild the payload with sc_unpack().
    function automatic string a2c_txn(string path, a2c_role_e role, string fields, string hex);
        return $sformatf("A2C_TXN %0.3f %s %s %s hex=%s", $realtime, path,
                         (role == A2C_SRC) ? "src" : "dst", fields, hex);
    endfunction

    // The two pin sets of a Mode B port: the DUT under test, which is the
    // RTL, and the model DUT that is its reference.
    typedef enum {A2C_DUT_LANE, A2C_MODEL_LANE} a2c_lane_e;

    // A ?: of two string literals is a packed value, which %s pads with
    // spaces to the longer literal, so the name is chosen with an if.
    function automatic string a2c_lane_name(a2c_lane_e lane);
        if (lane == A2C_DUT_LANE) return "DUT";
        return "model";
    endfunction

    `uvm_analysis_imp_decl(_a2c_dut)
    `uvm_analysis_imp_decl(_a2c_model)

    // Counts the transactions one output port delivers against the number
    // the test expects, with no check of their content. Each
    // wait_for_count() holds the test until every expected transaction has
    // arrived and then for a quiet window, so an extra one from the DUT
    // arrives inside the test, and reports a shortfall or an excess.
    // check_phase() reports what no wait_for_count() has. Every report is an
    // A2C_TXN_COUNT UVM_ERROR naming the port. A transaction that arrives
    // after its shortfall was reported is logged as late, not counted again,
    // until the next expect_count() declares new traffic.
    //
    // With dual set, the counter also counts the model DUT's stream on
    // model_export. Each lane is held to the same expect_count(), and every
    // report names its lane. With dual clear the counter counts
    // analysis_export alone, its messages name no lane, and a transaction on
    // model_export is an A2C_CFG error. The base class holds everything but
    // the exports, so a2c_midstream_guard can list counters of any item type.
    virtual class a2c_txn_counter_base extends uvm_component;
        string port_name = "";
        bit    dual = 0;

        // Indexed by a2c_lane_e.
        protected int unsigned expected[2];
        protected int unsigned received[2];
        // Reported missing and not yet arrived.
        protected int unsigned missing[2];

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected function int unsigned lanes();
            return dual ? 2 : 1;
        endfunction

        // The port and, with dual set, the lane that every message starts with.
        protected function string where(int lane);
            if (!dual) return port_name;
            return {port_name, " ", a2c_lane_name(a2c_lane_e'(lane)), " lane"};
        endfunction

        protected function void count(a2c_lane_e lane);
            if (lane == A2C_MODEL_LANE && !dual) begin
                `uvm_error("A2C_CFG", $sformatf("%s: model_export received a transaction, but dual is not set", port_name))
                return;
            end
            if (missing[lane] > 0) begin
                missing[lane]--;
                `uvm_info("A2C_TXN_COUNT", $sformatf("%s: late transaction, reported missing earlier; %0d still missing",
                                                 where(lane), missing[lane]), UVM_LOW)
                return;
            end
            received[lane]++;
        endfunction

        function void expect_count(int unsigned n);
            foreach (expected[lane]) begin
                expected[lane] += n;
                missing[lane]   = 0;
            end
        endfunction

        protected function int unsigned lane_outstanding(int lane);
            return (received[lane] < expected[lane]) ? expected[lane] - received[lane] : 0;
        endfunction

        // The expected transactions not yet received, summed over the lanes.
        // A shortfall a wait_for_count() has reported is no longer outstanding.
        function int unsigned outstanding();
            int unsigned n = 0;
            for (int lane = 0; lane < lanes(); lane++) n += lane_outstanding(lane);
            return n;
        endfunction

        // One lane's expected transactions that have not arrived, counting a
        // reported shortfall until its transactions arrive late or the next
        // expect_count() writes it off. A lane the counter does not use has
        // none.
        function int unsigned lane_pending(a2c_lane_e lane);
            if (lane >= lanes()) return 0;
            return lane_outstanding(lane) + missing[lane];
        endfunction

        function int unsigned pending();
            return lane_pending(A2C_DUT_LANE) + lane_pending(A2C_MODEL_LANE);
        endfunction

        // After a report the lane's expected count is set to its received
        // count, so a later wait_for_count() or check_phase does not report
        // the same transactions again. The quiet window starts once every
        // lane has its count.
        task wait_for_count(virtual a2c_clk_if clk_vif, int unsigned deadline_cycles, int unsigned quiet_cycles);
            int unsigned cycles = 0;
            bit          failed = 0;
            while (outstanding() > 0 && cycles < deadline_cycles) begin
                clk_vif.sample_edge();
                cycles++;
            end
            for (int lane = 0; lane < lanes(); lane++) begin
                if (received[lane] < expected[lane]) begin
                    `uvm_error("A2C_TXN_COUNT", $sformatf("%s: deadline of %0d clocks passed: expected %0d transactions, received %0d (%0d missing)",
                                                      where(lane), deadline_cycles, expected[lane], received[lane],
                                                      expected[lane] - received[lane]))
                    missing[lane] += expected[lane] - received[lane];
                    expected[lane] = received[lane];
                    failed = 1;
                end
            end
            if (failed) return;
            repeat (quiet_cycles) clk_vif.sample_edge();
            for (int lane = 0; lane < lanes(); lane++) begin
                if (received[lane] > expected[lane]) begin
                    `uvm_error("A2C_TXN_COUNT", $sformatf("%s: by the end of the quiet window received %0d transactions, expected %0d (%0d extra)",
                                                      where(lane), received[lane], expected[lane],
                                                      received[lane] - expected[lane]))
                    expected[lane] = received[lane];
                    failed = 1;
                end
            end
            if (failed) return;
            if (dual) begin
                `uvm_info("A2C_TXN_COUNT", $sformatf("%s: received the %0d expected transactions on the DUT lane and the %0d on the model lane",
                                                 port_name, received[A2C_DUT_LANE], received[A2C_MODEL_LANE]), UVM_LOW)
            end else begin
                `uvm_info("A2C_TXN_COUNT", $sformatf("%s: received the %0d expected transactions", port_name, received[A2C_DUT_LANE]), UVM_LOW)
            end
        endtask

        virtual function void check_phase(uvm_phase phase);
            for (int lane = 0; lane < lanes(); lane++) begin
                if (received[lane] < expected[lane]) begin
                    `uvm_error("A2C_TXN_COUNT", $sformatf("%s: end of test with %0d of %0d expected transactions outstanding, which no wait_for_count covered",
                                                      where(lane), lane_outstanding(lane), expected[lane]))
                end
                if (received[lane] > expected[lane]) begin
                    `uvm_error("A2C_TXN_COUNT", $sformatf("%s: end of test: received %0d transactions, expected %0d (%0d extra)",
                                                      where(lane), received[lane], expected[lane], received[lane] - expected[lane]))
                end
            end
        endfunction
    endclass : a2c_txn_counter_base

    class a2c_txn_counter #(type T = uvm_sequence_item) extends a2c_txn_counter_base;
        // The DUT lane.
        uvm_analysis_imp #(T, a2c_txn_counter#(T))           analysis_export;
        uvm_analysis_imp_a2c_model #(T, a2c_txn_counter#(T)) model_export;

        `uvm_component_param_utils(a2c_txn_counter#(T))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            analysis_export = new("analysis_export", this);
            model_export    = new("model_export", this);
        endfunction

        virtual function void write(T t);
            count(A2C_DUT_LANE);
        endfunction

        virtual function void write_a2c_model(T t);
            count(A2C_MODEL_LANE);
        endfunction
    endclass : a2c_txn_counter

    // What every Mode B comparator shares, so the env and a2c_midstream_guard
    // can hold comparators of any item type in one list.
    //
    // Pairs count from 1. A mismatch is a UVM_ERROR with id A2C_MODEL_CMP.
    // The first max_reported mismatches print both items; later ones are
    // counted, and check_phase() reports how many went unprinted as one more
    // A2C_MODEL_CMP UVM_ERROR, or as an A2C_MODEL_CMP_MIDSTREAM warning when
    // every unprinted one fell in a midstream window.
    //
    // a2c_midstream_guard calls open_midstream_window() on a register write
    // under +a2c_predict_midstream=1. Mismatches inside the window are
    // UVM_WARNINGs with id A2C_MODEL_CMP_MIDSTREAM. The window covers the
    // pairs whose index is above the slower side's item count at the write
    // and at most the faster side's count plus midstream_beats, so it holds
    // the beats already in flight on either lane plus the pipeline. The env
    // sets midstream_beats in its user region to the block's pipeline depth
    // in output beats.
    //
    // inject_mismatch(n) makes pair n report a mismatch whatever its items
    // hold, so a test can prove the check fires.
    //
    // The env's contract: at each return of wait_for_outputs() it calls
    // stable_point() on every comparator with auto_stable set. A port that
    // settles later gets auto_stable cleared in the env user region and
    // stable_point() called from the block's own event. The env sets counted
    // on a port whose a2c_txn_counter already reports a missing or extra
    // transaction, so check_phase() does not report the unpaired items again.
    virtual class a2c_comparator_base extends uvm_component;
        int unsigned midstream_beats = 64;
        int unsigned max_reported = 10;
        bit          auto_stable = 1;
        bit          counted = 0;

        protected int unsigned pairs;
        // Indexed by a2c_lane_e: the items each side has delivered.
        protected int unsigned seen[2];
        protected int unsigned window_lo;
        protected int unsigned window_hi;
        protected int unsigned inject_pair;
        protected int unsigned mismatches;
        protected int unsigned unprinted;
        protected int unsigned unprinted_errors;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void stable_point();
        endfunction

        virtual function void open_midstream_window();
            int unsigned slower = (seen[A2C_DUT_LANE] < seen[A2C_MODEL_LANE]) ? seen[A2C_DUT_LANE] : seen[A2C_MODEL_LANE];
            int unsigned faster = (seen[A2C_DUT_LANE] < seen[A2C_MODEL_LANE]) ? seen[A2C_MODEL_LANE] : seen[A2C_DUT_LANE];
            // A window still open keeps its start.
            if (pairs >= window_hi) window_lo = slower;
            if (faster + midstream_beats > window_hi) window_hi = faster + midstream_beats;
        endfunction

        function void inject_mismatch(int unsigned pair);
            inject_pair = pair;
        endfunction

        function int unsigned get_pairs();
            return pairs;
        endfunction

        // Whether the pair just counted falls in a midstream window.
        protected virtual function bit in_midstream_window();
            return pairs > window_lo && pairs <= window_hi;
        endfunction

        protected function void check_pair(bit same, uvm_object dut, uvm_object model, string key = "");
            string what;
            bit    midstream;
            pairs++;
            midstream = in_midstream_window();
            if (same && pairs != inject_pair) return;
            mismatches++;
            if (mismatches > max_reported) begin
                if (unprinted == 0) begin
                    `uvm_info("A2C_MODEL_CMP", $sformatf("%s: %0d mismatches printed; later ones are counted and reported at check_phase",
                                                     get_full_name(), max_reported), UVM_NONE)
                end
                unprinted++;
                if (!midstream) unprinted_errors++;
                return;
            end
            what = $sformatf("%s: pair %0d", get_full_name(), pairs);
            if (key != "") what = {what, " key ", key};
            if (pairs == inject_pair) what = {what, " (injected mismatch)"};
            what = {what, ": DUT ", dut.convert2string(), ", model ", model.convert2string()};
            if (midstream) begin
                `uvm_warning("A2C_MODEL_CMP_MIDSTREAM", {what, "; inside the midstream window of a register write"})
            end else begin
                `uvm_error("A2C_MODEL_CMP", what)
            end
        endfunction

        virtual function void check_phase(uvm_phase phase);
            string what;
            if (unprinted == 0) return;
            what = $sformatf("%s: %0d mismatches in all, %0d not printed, %0d of those outside a midstream window",
                             get_full_name(), mismatches, unprinted, unprinted_errors);
            if (unprinted_errors > 0) `uvm_error("A2C_MODEL_CMP", what)
            else `uvm_warning("A2C_MODEL_CMP_MIDSTREAM", what)
        endfunction
    endclass : a2c_comparator_base

    // Pairs the DUT's item n with the model's item n, in arrival order on
    // each side, and compares them with T's compare(), as UVM's
    // uvm_in_order_comparator does, but reports a mismatch as an error.
    // check_phase() reports the items either side has left unpaired as
    // A2C_MODEL_CMP, unless counted is set. A subclass that overrides key()
    // pairs in order per key instead, for a protocol that orders only within
    // an ID, such as AXI; the key also appears in the mismatch message.
    class a2c_in_order_comparator #(type T = uvm_sequence_item) extends a2c_comparator_base;
        uvm_analysis_imp_a2c_dut #(T, a2c_in_order_comparator#(T))   dut_export;
        uvm_analysis_imp_a2c_model #(T, a2c_in_order_comparator#(T)) model_export;

        // Items waiting for their pair, per key. One side's queue for a key
        // is empty whenever the other side's is not.
        protected T dut_q[string][$];
        protected T model_q[string][$];

        `uvm_component_param_utils(a2c_in_order_comparator#(T))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dut_export   = new("dut_export", this);
            model_export = new("model_export", this);
        endfunction

        virtual function string key(T t);
            return "";
        endfunction

        virtual function void write_a2c_dut(T t);
            string k = key(t);
            seen[A2C_DUT_LANE]++;
            if (model_q.exists(k) && model_q[k].size() > 0) compare_pair(t, model_q[k].pop_front(), k);
            else dut_q[k].push_back(t);
        endfunction

        virtual function void write_a2c_model(T t);
            string k = key(t);
            seen[A2C_MODEL_LANE]++;
            if (dut_q.exists(k) && dut_q[k].size() > 0) compare_pair(dut_q[k].pop_front(), t, k);
            else model_q[k].push_back(t);
        endfunction

        protected function void compare_pair(T dut, T model, string k);
            check_pair(dut.compare(model), dut, model, k);
        endfunction

        protected function void report_unpaired(string side, T q[string][$]);
            int unsigned n = 0;
            string       first = "";
            string       first_key = "";
            foreach (q[k]) begin
                if (q[k].size() > 0 && first == "") begin
                    first     = q[k][0].convert2string();
                    first_key = k;
                end
                n += q[k].size();
            end
            if (n == 0) return;
            if (first_key != "") first = {"in key order, key ", first_key, ", ", first};
            `uvm_error("A2C_MODEL_CMP", $sformatf("%s: end of test with %0d %s items unpaired after %0d pairs, first %s",
                                              get_full_name(), n, side, pairs, first))
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (counted) return;
            report_unpaired("DUT", dut_q);
            report_unpaired("model", model_q);
        endfunction
    endclass : a2c_in_order_comparator

    // The checks a status port gets in Mode B. The model updates a status
    // level sooner than the RTL, so the two are not compared beat for beat.
    // The policy decides what is checked:
    //   A2C_STATUS_STABLE  at each stable_point(), the latest DUT value against
    //                      the latest model value, as one pair; a lane that has
    //                      reported no value yet is an A2C_MODEL_CMP error;
    //   A2C_STATUS_BOUNDS  every value either lane reports lies within lo..hi,
    //                      or it is an A2C_MODEL_CMP error naming the lane; a
    //                      value has_xz() flags is an A2C_XZ error instead,
    //                      and its bounds are not read;
    //   A2C_STATUS_OFF     each value is logged with id A2C_STATUS, unchecked.
    // A midstream window covers the next stable point only. bounds reads each
    // item through value(), which a subclass defines for an item whose
    // payload converts to an unsigned value of 64 bits or fewer; the default
    // stops the run with A2C_CFG. has_xz() flags none by default, so a
    // subclass whose payload can carry X or Z must override it as well as
    // value(), or bounds reads an X item as an in-range value.
    typedef enum {A2C_STATUS_STABLE, A2C_STATUS_BOUNDS, A2C_STATUS_OFF} a2c_status_policy_e;

    class a2c_status_comparator #(type T = uvm_sequence_item) extends a2c_comparator_base;
        uvm_analysis_imp_a2c_dut #(T, a2c_status_comparator#(T))   dut_export;
        uvm_analysis_imp_a2c_model #(T, a2c_status_comparator#(T)) model_export;

        a2c_status_policy_e policy = A2C_STATUS_STABLE;
        bit [63:0]          lo = '0;
        bit [63:0]          hi = '1;

        protected T   latest[2];
        protected bit window_open;

        `uvm_component_param_utils(a2c_status_comparator#(T))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dut_export   = new("dut_export", this);
            model_export = new("model_export", this);
        endfunction

        virtual function bit [63:0] value(T t);
            `uvm_fatal("A2C_CFG", $sformatf("%s: the bounds policy needs a subclass that defines value()", get_full_name()))
            return '0;
        endfunction

        virtual function bit has_xz(T t);
            return 0;
        endfunction

        virtual function void open_midstream_window();
            window_open = 1;
        endfunction

        protected virtual function bit in_midstream_window();
            in_midstream_window = window_open;
            window_open = 0;
        endfunction

        protected function void observe(a2c_lane_e lane, T t);
            bit [63:0] v;
            latest[lane] = t;
            seen[lane]++;
            case (policy)
                A2C_STATUS_BOUNDS: begin
                    if (has_xz(t)) begin
                        `uvm_error("A2C_XZ", $sformatf("%s: %s value %s has X or Z", get_full_name(), a2c_lane_name(lane), t.convert2string()))
                        return;
                    end
                    v = value(t);
                    if (v < lo || v > hi) begin
                        `uvm_error("A2C_MODEL_CMP", $sformatf("%s: %s value %s is outside 0x%0h..0x%0h",
                                                          get_full_name(), a2c_lane_name(lane), t.convert2string(), lo, hi))
                    end
                end
                A2C_STATUS_OFF: `uvm_info("A2C_STATUS", $sformatf("%s: %s value %s", get_full_name(), a2c_lane_name(lane), t.convert2string()),
                                          UVM_MEDIUM)
                default: ;
            endcase
        endfunction

        virtual function void write_a2c_dut(T t);
            observe(A2C_DUT_LANE, t);
        endfunction

        virtual function void write_a2c_model(T t);
            observe(A2C_MODEL_LANE, t);
        endfunction

        virtual function void stable_point();
            string none = "";
            if (policy != A2C_STATUS_STABLE) return;
            foreach (latest[lane]) begin
                if (latest[lane] != null) continue;
                if (none != "") none = {none, " and "};
                none = {none, "the ", a2c_lane_name(a2c_lane_e'(lane)), " lane"};
            end
            if (none != "") begin
                `uvm_error("A2C_MODEL_CMP", $sformatf("%s: stable point with no value reported on %s", get_full_name(), none))
                return;
            end
            check_pair(latest[A2C_DUT_LANE].compare(latest[A2C_MODEL_LANE]), latest[A2C_DUT_LANE], latest[A2C_MODEL_LANE]);
        endfunction
    endclass : a2c_status_comparator

    // Holds Mode B to configuration changes while the datapath is quiescent.
    // It subscribes to the register predictor's reg_ap. A write while any
    // listed counter has pending transactions on either lane, a reported
    // shortfall included, is a UVM_ERROR with id A2C_MIDSTREAM. With
    // +a2c_predict_midstream=1 the write is logged as UVM_INFO instead and
    // opens the midstream window of every listed comparator. Traffic counts
    // only once a test has declared it with expect_count().
    class a2c_midstream_guard extends uvm_component;
        uvm_analysis_imp #(uvm_reg_item, a2c_midstream_guard) analysis_export;
        a2c_txn_counter_base                                  counters[$];
        a2c_comparator_base                                   comparators[$];
        bit                                                   predict_midstream;

        `uvm_component_utils(a2c_midstream_guard)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            analysis_export = new("analysis_export", this);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            int unsigned v;
            super.build_phase(phase);
            if ($value$plusargs("a2c_predict_midstream=%d", v)) predict_midstream = (v != 0);
        endfunction

        virtual function void write(uvm_reg_item t);
            string target;
            string busy = "";
            if (t.kind != UVM_WRITE) return;
            foreach (counters[i]) begin
                a2c_txn_counter_base c = counters[i];
                if (c.pending() == 0) continue;
                if (busy != "") busy = {busy, ", "};
                if (c.dual) busy = {busy, $sformatf("%s (DUT %0d, model %0d)", c.port_name, c.lane_pending(A2C_DUT_LANE),
                                                    c.lane_pending(A2C_MODEL_LANE))};
                else busy = {busy, $sformatf("%s (%0d)", c.port_name, c.pending())};
            end
            if (busy == "") return;
            if (t.element != null) target = t.element.get_full_name();
            else target = $sformatf("address 0x%0h", t.offset);
            if (!predict_midstream) begin
                `uvm_error("A2C_MIDSTREAM", $sformatf("write to %s while outputs have transactions pending: %s. Configuration may change only while the datapath is quiescent; +a2c_predict_midstream=1 relaxes the rule for debugging",
                                                  target, busy))
                return;
            end
            `uvm_info("A2C_MIDSTREAM", $sformatf("write to %s while outputs have transactions pending: %s; +a2c_predict_midstream=1 opens each comparator's midstream window",
                                             target, busy), UVM_LOW)
            foreach (comparators[i]) comparators[i].open_midstream_window();
        endfunction
    endclass : a2c_midstream_guard

    // Lets one responder serve both lanes of a Mode B port from one shared
    // model. The DUT lane applies each transaction and record()s its
    // response and delay; the model lane replays them in order and never
    // applies a transaction's effect.
    class a2c_replay_log #(type T = uvm_sequence_item) extends uvm_component;
        typedef struct {
            T            rsp;
            int unsigned delay;
        } record_t;

        // Recorded and not yet replayed, oldest first.
        protected record_t     records[$];
        protected int unsigned replayed;
        // The transaction the model lane waits for, or -1.
        protected int          waiting = -1;

        `uvm_component_param_utils(a2c_replay_log#(T))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function void record(T rsp, int unsigned delay);
            records.push_back('{rsp: rsp, delay: delay});
        endfunction

        // Whether the model lane's next transaction is recorded. Until it
        // is, check_phase() counts the model lane as waiting for it.
        function bit can_replay();
            waiting = (records.size() == 0) ? int'(replayed) : -1;
            return records.size() != 0;
        endfunction

        // T may be a class handle or a value type; rsp is the recorded
        // handle, not a copy.
        function void replay(output T rsp, output int unsigned delay);
            if (records.size() == 0) begin
                `uvm_fatal("A2C_REPLAY", $sformatf("%s: the model lane replays transaction %0d, which the DUT lane has not recorded",
                                                   get_full_name(), replayed))
            end
            rsp   = records[0].rsp;
            delay = records[0].delay;
            void'(records.pop_front());
            replayed++;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            if (records.size() > 0) begin
                `uvm_error("A2C_REPLAY", $sformatf("%s: end of test with %0d responses the DUT lane recorded and the model lane never replayed, from transaction %0d",
                                               get_full_name(), records.size(), replayed))
            end
            if (waiting >= 0) begin
                `uvm_error("A2C_REPLAY", $sformatf("%s: the model lane waited for transaction %0d, which the DUT lane never recorded",
                                               get_full_name(), waiting))
            end
        endfunction
    endclass : a2c_replay_log

    // What a2c_mem_model returns for a word nothing has written.
    typedef enum {A2C_MEM_FILL_ZERO, A2C_MEM_FILL_RANDOM, A2C_MEM_FILL_FIXED} a2c_mem_fill_e;

    // A sparse memory of word_t words keyed by a 64-bit index, which a test
    // can preload and inspect. A read of an unwritten word returns the fill
    // value without storing it, so exists() reports only written words. The
    // random fill is a hash of seed and the index, so every read of one
    // unwritten word returns the same value whatever the order of reads.
    // seed is drawn from the creating thread's generator, so it follows the
    // simulation seed. The first read of an unwritten word logs one A2C_MEM
    // info line per model; later ones are not logged.
    class a2c_mem_model #(type word_t = logic [31:0]) extends uvm_object;
        a2c_mem_fill_e fill = A2C_MEM_FILL_ZERO;
        // The word an A2C_MEM_FILL_FIXED model returns.
        word_t         fill_value = '0;
        bit [31:0]     seed;

        protected word_t store[bit [63:0]];
        protected bit    unwritten_read;

        `uvm_object_param_utils(a2c_mem_model#(word_t))

        function new(string name = "a2c_mem_model");
            super.new(name);
            seed = $urandom();
        endfunction

        function void write(bit [63:0] index, word_t data);
            store[index] = data;
        endfunction

        function bit exists(bit [63:0] index);
            return store.exists(index);
        endfunction

        // The splitmix64 finalizer.
        protected static function bit [63:0] mix(bit [63:0] z);
            z = (z ^ (z >> 30)) * 64'hbf58_476d_1ce4_e5b9;
            z = (z ^ (z >> 27)) * 64'h94d0_49bb_1331_11eb;
            return z ^ (z >> 31);
        endfunction

        // Bits 64k to 64k+63 of the word come from the hash of seed, k and index.
        protected function word_t random_fill(bit [63:0] index);
            bit [$bits(word_t)-1:0] bits;
            bit [63:0]              chunk;
            for (int unsigned i = 0; i < $bits(word_t); i++) begin
                if (i % 64 == 0) chunk = mix(index ^ mix({seed, 32'(i / 64)}));
                bits[i] = chunk[i % 64];
            end
            return word_t'(bits);
        endfunction

        function word_t read(bit [63:0] index);
            word_t data;
            if (store.exists(index)) return store[index];
            if (!unwritten_read) begin
                unwritten_read = 1;
                `uvm_info("A2C_MEM", $sformatf("%s: read of unwritten index 0x%0h returns the %s fill; later unwritten reads are not logged",
                                               get_name(), index, fill.name()), UVM_LOW)
            end
            case (fill)
                A2C_MEM_FILL_ZERO:   data = '0;
                A2C_MEM_FILL_RANDOM: data = random_fill(index);
                A2C_MEM_FILL_FIXED:  data = fill_value;
            endcase
            return data;
        endfunction
    endclass : a2c_mem_model

    // Turns each UVM_ERROR with id demote_id into UVM_INFO and counts it, so a
    // negative test can pass when the check it provokes fires.
    class a2c_error_demoter extends uvm_report_catcher;
        string       demote_id = "";
        int unsigned demoted;

        `uvm_object_utils(a2c_error_demoter)

        function new(string name = "a2c_error_demoter");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_severity() == UVM_ERROR && get_id() == demote_id) begin
                demoted++;
                set_severity(UVM_INFO);
                // The action was chosen for UVM_ERROR and still holds
                // UVM_COUNT; without this the quit count would still rise.
                set_action(UVM_DISPLAY);
                set_message({"expected, demoted to info: ", get_message()});
            end
            return THROW;
        endfunction
    endclass : a2c_error_demoter

    // The AXI burst and response encodings and the helpers below, shared by
    // the axi_read and axi_write agents.
    typedef enum bit [1:0] {AXI_FIXED = 2'b00, AXI_INCR = 2'b01, AXI_WRAP = 2'b10} axi_burst_e;
    typedef enum bit [1:0] {AXI_OKAY = 2'b00, AXI_EXOKAY = 2'b01, AXI_SLVERR = 2'b10, AXI_DECERR = 2'b11} axi_resp_e;

    // The address of beat n of an AXI burst, and the bytes it carries: from
    // that address to the end of its (1 << size)-byte window. FIXED repeats
    // the start address, INCR steps from the aligned start, and WRAP steps
    // within the window of (len + 1) << size bytes that holds the start. A
    // reserved burst type steps as INCR.
    function automatic void axi_beat(bit [63:0] start, bit [2:0] size, bit [7:0] len, bit [1:0] burst,
                                     int unsigned n, output bit [63:0] addr, output int unsigned bytes);
        bit [63:0] nbytes = 64'd1 << size;
        bit [63:0] span   = nbytes * (64'(len) + 1);
        bit [63:0] boundary;
        case (burst)
            AXI_FIXED: addr = start;
            AXI_WRAP: begin
                boundary = (start / span) * span;
                addr     = boundary + (start - boundary + n * nbytes) % span;
            end
            default: addr = (n == 0) ? start : (start & ~(nbytes - 1)) + n * nbytes;
        endcase
        bytes = int'(nbytes - (addr & (nbytes - 1)));
    endfunction

    // An inclusive range of byte addresses an AXI slave answers with SLVERR.
    typedef struct {
        bit [63:0] lo;
        bit [63:0] hi;
    } axi_addr_range_t;

    function automatic bit axi_in_error_range(bit [63:0] addr, axi_addr_range_t ranges[$]);
        foreach (ranges[i]) begin
            if (addr >= ranges[i].lo && addr <= ranges[i].hi) return 1;
        end
        return 0;
    endfunction

endpackage : a2c_uvm_pkg

`endif // A2C_UVM_PKG_SV
