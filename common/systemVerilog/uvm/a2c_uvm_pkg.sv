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

    // Reads r into value when it has a type a knob may be set as: int
    // unsigned, as the generated base test sets it, int, uvm_config_int, the
    // uvm_bitstream_t of +uvm_set_config_int, and with as_flag set also bit.
    // Returns 0 for any other type, leaving value alone. With c null it
    // only checks the type, so the resource records no read.
    function automatic bit a2c_read_config(uvm_component c, uvm_resource_base r, bit as_flag, ref int unsigned value);
        uvm_resource#(int unsigned)    as_uint;
        uvm_resource#(int)             as_int;
        uvm_resource#(uvm_bitstream_t) as_bits;
        uvm_resource#(bit)             as_bit;
        if ($cast(as_uint, r)) begin
            if (c != null) value = as_uint.read(c);
        end else if ($cast(as_int, r)) begin
            if (c != null) value = as_int.read(c);
        end else if ($cast(as_bits, r)) begin
            if (c != null) value = as_bits.read(c);
        end else if (as_flag && $cast(as_bit, r)) begin
            if (c != null) value = as_bit.read(c);
        end else begin
            return 0;
        end
        return 1;
    endfunction

    // Reads the knob field of c from the config_db. Of the entries whose
    // scope matches c, the one uvm_config_db#(T)::get() would return if
    // every entry had type T wins: those of the highest precedence, and of
    // them the one set last. During build_phase a set's precedence falls
    // with the setter's depth, so a test's set beats its env's. How specific
    // a scope is plays no part, so a later set for "env*" beats an earlier
    // one for "env.agent" from the same component. So a set of one accepted
    // type overrides a set of another exactly as it would one of its own.
    //
    // A winning entry of a type a2c_read_config() does not accept is
    // skipped, as if it had never been set, with an A2C_CFG warning: the
    // knob then takes the best entry of an accepted type, so a stray set
    // costs only itself and not the base test's value under it, or keeps
    // its value when there is none. Leaves value alone and returns 0 when
    // nothing is read.
    function automatic bit a2c_config_get(uvm_component c, string field, bit as_flag, ref int unsigned value);
        uvm_resource_pool            rp = uvm_resource_pool::get();
        uvm_resource_types::rsrc_q_t q;
        uvm_resource_types::rsrc_q_t accepted;
        uvm_resource_base            r;
        string                       types = as_flag ? "bit, int unsigned, int or uvm_config_int" : "int unsigned, int or uvm_config_int";
        string                       fix = as_flag ? "Set it as bit" : "Set it as int unsigned";
        int unsigned                 unused;
        process                      p = process::self();
        string                       state;
        // lookup_regex() builds a new queue, and so does accepted = new().
        // IEEE 1800 section 18.14.1 seeds each new object's generator from
        // the creating thread's, which advances that thread's random state. The
        // state is put back, as uvm_resource_pool::lookup_name() does around
        // its own new queue, so reading a knob leaves the caller's later
        // randomization alone.
        if (p != null) state = p.get_randstate();
        // lookup_regex(), not lookup_name(): VCS's lookup_name() drops each
        // entry that does not outrank the first match, so an accepted entry
        // under a rejected one of equal precedence would never be seen.
        q        = rp.lookup_regex(field, c.get_full_name());
        accepted = new();
        if (p != null) p.set_randstate(state);
        r = rp.get_highest_precedence(q);
        if (r == null) return 0;
        if (a2c_read_config(c, r, as_flag, value)) return 1;
        for (int i = 0; i < q.size(); i++) begin
            if (a2c_read_config(null, q.get(i), as_flag, unused)) accepted.push_back(q.get(i));
        end
        r = rp.get_highest_precedence(accepted);
        if (r == null) begin
            `uvm_warning("A2C_CFG", $sformatf("%s: the config_db entry that sets %s is not of type %s, so it is ignored and the knob keeps %0d. %s",
                                              c.get_full_name(), field, types, value, fix))
            return 0;
        end
        void'(a2c_read_config(c, r, as_flag, value));
        `uvm_warning("A2C_CFG", $sformatf("%s: the config_db entry that sets %s is not of type %s, so it is ignored and the knob takes %0d from the next entry of an accepted type. %s",
                                          c.get_full_name(), field, types, value, fix))
        return 1;
    endfunction

    function automatic bit a2c_get_config_int(uvm_component c, string field, ref int unsigned value);
        return a2c_config_get(c, field, 1'b0, value);
    endfunction

    // As a2c_get_config_int() for a flag that bit is accepted for too; any
    // non-zero value sets the flag.
    function automatic void a2c_get_config_bit(uvm_component c, string field, ref bit value);
        int unsigned n = value;
        if (a2c_config_get(c, field, 1'b1, n)) value = (n != 0);
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
        string       port_name = "";
        bit          dual = 0;
        // A clock with no edge for this many of its periods has stopped. A
        // generated base test sets it from +a2c_clock_stop_cycles through
        // a2c_clock_stop_cycles in the config_db.
        int unsigned clock_stop_cycles = 1000;

        // Indexed by a2c_lane_e.
        protected int unsigned expected[2];
        protected int unsigned received[2];
        // Reported missing and not yet arrived.
        protected int unsigned missing[2];

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            void'(a2c_get_config_int(this, "a2c_clock_stop_cycles", clock_stop_cycles));
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
        // lane has its count. A clock with no edge for clock_stop_cycles
        // periods has stopped: a shortfall is reported then, and a quiet
        // window ends.
        task wait_for_count(virtual a2c_clk_if clk_vif, int unsigned deadline_cycles, int unsigned quiet_cycles);
            int unsigned cycles = 0;
            bit          failed = 0;
            bit          running = 1;
            string       why;
            while (outstanding() > 0 && cycles < deadline_cycles && running) begin
                clk_vif.next_sample(clock_stop_cycles, running);
                if (running) cycles++;
            end
            if (running) why = $sformatf("deadline of %0d clocks passed", deadline_cycles);
            else why = $sformatf("the clock stopped after %0d clocks", cycles);
            for (int lane = 0; lane < lanes(); lane++) begin
                if (received[lane] < expected[lane]) begin
                    `uvm_error("A2C_TXN_COUNT", $sformatf("%s: %s: expected %0d transactions, received %0d (%0d missing)",
                                                      where(lane), why, expected[lane], received[lane],
                                                      expected[lane] - received[lane]))
                    missing[lane] += expected[lane] - received[lane];
                    expected[lane] = received[lane];
                    failed = 1;
                end
            end
            if (failed) return;
            for (int unsigned c = 0; c < quiet_cycles && running; c++) clk_vif.next_sample(clock_stop_cycles, running);
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
    //
    // cut(s) ends the comparison after pair s, for a run that
    // a2c_replay_drain ends after transaction s, and uncut() undoes it. A
    // comparator a replay log drives must override both; this cut() stops
    // the run with A2C_CFG, so a comparator cannot ignore a cut by omission.
    //
    // lane_dead(), which a Mode B master calls when it declares a lane
    // dead, ends the comparison there: check_pair() compares the pairs
    // completed up to and including the time step of the death, whatever
    // the order of the monitor and the master in that step, and none after
    // it, so the dead lane causes no mismatch. The master's A2C_SKEW error
    // has failed the run, so check_phase() reports the death as one
    // UVM_MEDIUM line: the lane, the time, and per lane the items it
    // delivered that were never compared, its seen[] count less the pairs.
    // Only a subclass that reports through check_pair() and counts each
    // lane's items in seen[] gets this; lane_dead() is virtual, so a
    // subclass may override it. is_dead() and died_at() let any checker
    // that holds the comparator ask about a lane.
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
        // Indexed by a2c_lane_e.
        protected bit          dead[2];
        protected realtime     dead_at[2];

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void stable_point();
        endfunction

        virtual function void lane_dead(a2c_lane_e lane);
            if (dead[lane]) return;
            dead[lane]    = 1;
            dead_at[lane] = $realtime;
        endfunction

        function bit stopped();
            return dead[A2C_DUT_LANE] || dead[A2C_MODEL_LANE];
        endfunction

        function bit is_dead(a2c_lane_e lane);
            return dead[lane];
        endfunction

        // The time of the lane's death, or 0 while it lives.
        function realtime died_at(a2c_lane_e lane);
            return dead[lane] ? dead_at[lane] : 0;
        endfunction

        // Whether a lane died before the current time step.
        protected function bit past_death();
            foreach (dead[l]) if (dead[l] && dead_at[l] < $realtime) return 1;
            return 0;
        endfunction

        // The items lane delivered that were never compared.
        function int unsigned uncompared(a2c_lane_e lane);
            return (seen[lane] > pairs) ? seen[lane] - pairs : 0;
        endfunction

        virtual function void cut(int unsigned s);
            `uvm_fatal("A2C_CFG", $sformatf("%s: %s does not override cut(), which the end-of-test drain calls to end the comparison after pair %0d",
                                            get_full_name(), get_type_name(), s))
        endfunction

        virtual function void uncut();
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
            if (past_death()) return;
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
            if (unprinted != 0) begin
                what = $sformatf("%s: %0d mismatches in all, %0d not printed, %0d of those outside a midstream window",
                                 get_full_name(), mismatches, unprinted, unprinted_errors);
                if (unprinted_errors > 0) `uvm_error("A2C_MODEL_CMP", what)
                else `uvm_warning("A2C_MODEL_CMP_MIDSTREAM", what)
            end
            if (!stopped()) return;
            what = "";
            foreach (dead[lane]) begin
                if (!dead[lane]) continue;
                what = {what, (what == "") ? "" : " and ", $sformatf("the %s lane dead at %0t", a2c_lane_name(a2c_lane_e'(lane)), dead_at[lane])};
            end
            `uvm_info("A2C_MODEL_CMP", $sformatf("%s: the comparison stopped after %0d pairs: the master declared %s. %0d DUT and %0d model items were not compared",
                                             get_full_name(), pairs, what, uncompared(A2C_DUT_LANE), uncompared(A2C_MODEL_LANE)), UVM_MEDIUM)
        endfunction
    endclass : a2c_comparator_base

    // Pairs the DUT's item n with the model's item n, in arrival order on each
    // side, and compares them with T's compare(), as UVM's
    // uvm_in_order_comparator does, but reports a mismatch as an error.
    // check_phase() reports the items either side has left unpaired as
    // A2C_MODEL_CMP, unless counted is set or a lane is dead. A subclass that
    // overrides key() pairs in order per key instead, for a protocol that
    // orders only within an ID, such as AXI; the key also appears in the
    // mismatch message. After cut(s) the DUT side's items after its first s
    // are held, and of each key the model side keeps as many items as the DUT
    // side's first s carry with that key and holds the rest, so the sides may
    // complete different keys in different orders across the cut. Without a
    // key that keeps the model side's first s. Held items are never compared,
    // and are dropped at the end of the test unless uncut() releases them.
    class a2c_in_order_comparator #(type T = uvm_sequence_item) extends a2c_comparator_base;
        uvm_analysis_imp_a2c_dut #(T, a2c_in_order_comparator#(T))   dut_export;
        uvm_analysis_imp_a2c_model #(T, a2c_in_order_comparator#(T)) model_export;

        // An item, its place in its side's arrival order, from 1, and its
        // key.
        typedef struct {
            T            t;
            int unsigned n;
            string       k;
        } entry_t;

        // A DUT item with a key that is not "", and its place.
        typedef struct {
            string       k;
            int unsigned n;
        } keyed_t;

        // Items waiting for their pair, per key. One side's queue for a key
        // is empty whenever the other side's is not.
        protected entry_t dut_q[string][$];
        protected entry_t model_q[string][$];
        // Indexed by a2c_lane_e: the items after the cut, in arrival order.
        protected entry_t held[2][$];
        // The pair the comparison ends after, or 0.
        protected int unsigned limit;
        // The DUT items with a key, in arrival order. An unkeyed
        // comparator records none.
        protected keyed_t      dut_keyed[$];
        // Per key: the model items not held, and after a cut the DUT items
        // within its first limit. Those not arrived yet count under key "",
        // so without a key the model side keeps its first limit at once.
        protected int unsigned model_kept[string];
        protected int unsigned quota[string];

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
            entry_t e;
            seen[A2C_DUT_LANE]++;
            e.t = t;
            e.n = seen[A2C_DUT_LANE];
            e.k = key(t);
            if (e.k != "") dut_keyed.push_back('{k: e.k, n: e.n});
            if (limit != 0 && e.n > limit) begin
                held[A2C_DUT_LANE].push_back(e);
                return;
            end
            pair_dut(e);
            if (limit == 0 || e.k == "") return;
            quota[e.k]++;
            quota[""]--;
            release_model(e.k);
        endfunction

        protected function int unsigned kept_of(string k);
            return model_kept.exists(k) ? model_kept[k] : 0;
        endfunction

        protected function int unsigned quota_of(string k);
            return quota.exists(k) ? quota[k] : 0;
        endfunction

        virtual function void write_a2c_model(T t);
            entry_t e;
            seen[A2C_MODEL_LANE]++;
            e.t = t;
            e.n = seen[A2C_MODEL_LANE];
            e.k = key(t);
            if (limit != 0 && kept_of(e.k) >= quota_of(e.k)) begin
                held[A2C_MODEL_LANE].push_back(e);
                return;
            end
            model_kept[e.k]++;
            pair_model(e);
        endfunction

        // Pairs the model side's held items of key k that its quota now
        // covers, oldest first.
        protected function void release_model(string k);
            for (int i = 0; i < held[A2C_MODEL_LANE].size() && kept_of(k) < quota_of(k); ) begin
                entry_t e = held[A2C_MODEL_LANE][i];
                if (e.k != k) begin
                    i++;
                    continue;
                end
                held[A2C_MODEL_LANE].delete(i);
                model_kept[k]++;
                pair_model(e);
            end
        endfunction

        protected function void pair_dut(entry_t e);
            entry_t m;
            if (model_q.exists(e.k) && model_q[e.k].size() > 0) begin
                m = model_q[e.k].pop_front();
                compare_pair(e.t, m.t, e.k);
            end else begin
                dut_q[e.k].push_back(e);
            end
        endfunction

        protected function void pair_model(entry_t e);
            entry_t d;
            if (dut_q.exists(e.k) && dut_q[e.k].size() > 0) begin
                d = dut_q[e.k].pop_front();
                compare_pair(d.t, e.t, e.k);
            end else begin
                model_q[e.k].push_back(e);
            end
        endfunction

        // Each key's queue holds its side's items in arrival order, so the
        // items after s are at the back of each.
        protected function void hold_after(ref entry_t q[string][$], input a2c_lane_e lane, input int unsigned s);
            entry_t later[$];
            foreach (q[k]) begin
                while (q[k].size() > 0 && q[k][q[k].size() - 1].n > s) later.push_back(q[k].pop_back());
            end
            later.sort with (item.n);
            held[lane] = {later, held[lane]};
        endfunction

        // A model item already compared stays compared, so a key whose
        // model side has gone past its quota holds only its waiting items.
        virtual function void cut(int unsigned s);
            entry_t later[$];
            limit = s;
            quota.delete();
            quota[""] = s;
            foreach (dut_keyed[i]) begin
                if (dut_keyed[i].n > s) break;
                quota[dut_keyed[i].k]++;
                quota[""]--;
            end
            hold_after(dut_q, A2C_DUT_LANE, s);
            foreach (model_q[k]) begin
                while (model_q[k].size() > 0 && kept_of(k) > quota_of(k)) begin
                    later.push_back(model_q[k].pop_back());
                    model_kept[k]--;
                end
            end
            later = {later, held[A2C_MODEL_LANE]};
            later.sort with (item.n);
            held[A2C_MODEL_LANE] = later;
        endfunction

        virtual function void uncut();
            limit = 0;
            quota.delete();
            while (held[A2C_DUT_LANE].size() > 0) pair_dut(held[A2C_DUT_LANE].pop_front());
            while (held[A2C_MODEL_LANE].size() > 0) begin
                entry_t e = held[A2C_MODEL_LANE].pop_front();
                model_kept[e.k]++;
                pair_model(e);
            end
        endfunction

        // A subclass may hold a pair and check it when a later one arrives.
        protected virtual function void compare_pair(T dut, T model, string k);
            check_pair(dut.compare(model), dut, model, k);
        endfunction

        protected function void report_unpaired(string side, entry_t q[string][$]);
            int unsigned n = 0;
            string       first = "";
            string       first_key = "";
            foreach (q[k]) begin
                if (q[k].size() > 0 && first == "") begin
                    first     = q[k][0].t.convert2string();
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
            if (counted || stopped()) return;
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
    // It takes the writes a2c_reg_write_subscriber converts. A write while any
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

    // Converts each write in the bus items a register bus monitor reports
    // into a uvm_reg_item for a2c_midstream_guard, as uvm_reg_predictor
    // converts bus items, and samples no pins itself. The item carries the
    // kind and offset from the adapter's bus2reg(), and the register or
    // memory the map places at that offset, or a null element for an
    // unmapped one. A memory write, an unmapped write and each bus word of a
    // multi-word register are all passed on. The predictor's reg_ap reports
    // only writes that complete a whole register.
    class a2c_reg_write_subscriber #(type BUS_T = uvm_sequence_item) extends uvm_subscriber #(BUS_T);
        uvm_reg_map                       map;
        uvm_reg_adapter                   adapter;
        uvm_analysis_port #(uvm_reg_item) ap;

        `uvm_component_param_utils(a2c_reg_write_subscriber#(BUS_T))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual function void write(BUS_T t);
            uvm_reg_bus_op rw;
            uvm_reg_item   item;
            uvm_reg        rg;
            uvm_mem        mem;
            rw.byte_en = '1;
            adapter.bus2reg(t, rw);
            if (rw.kind != UVM_WRITE) return;
            item = uvm_reg_item::type_id::create("item");
            item.kind   = UVM_WRITE;
            item.offset = rw.addr;
            item.map    = map;
            item.value  = new[1];
            item.value[0] = rw.data;
            rg = map.get_reg_by_offset(rw.addr, 0);
            if (rg != null) begin
                item.element      = rg;
                item.element_kind = UVM_REG;
            end else begin
                mem = map.get_mem_by_offset(rw.addr);
                if (mem != null) begin
                    item.element      = mem;
                    item.element_kind = UVM_MEM;
                end
            end
            ap.write(item);
        endfunction
    endclass : a2c_reg_write_subscriber

    // What a Mode B responder driver tells its a2c_replay_log about the two
    // lanes it serves, for the end-of-test drain. lane_starts() and
    // lane_busy() must change away from the rising edge of the log's
    // clk_vif, at the falling edge or the drive point, as the built-in
    // drivers do: the drain reads them at the rising edge. A driver that
    // counts in an @(posedge clk) process races the drain, which can end in
    // that time step before the count moves and leave a false A2C_REPLAY.
    interface class a2c_replay_lanes;
        // Whether the lane is inside a transaction, from the clock it
        // starts.
        pure virtual function bit lane_busy(a2c_lane_e l);
        // The transactions the lane has started so far.
        pure virtual function int unsigned lane_starts(a2c_lane_e l);
        // The transactions the lane has completed so far.
        pure virtual function int unsigned lane_done(a2c_lane_e l);
    endclass : a2c_replay_lanes

    typedef class a2c_replay_drain;
    typedef class a2c_replay_log_base;

    // A monitor that a Mode B master tells when it declares the lane of the
    // monitor's pin set dead.
    interface class a2c_lane_watch;
        pure virtual function void lane_dead();
    endclass : a2c_lane_watch

    // The passive agents on one pin set, which the active agent of its port
    // tells of a death and of a cut as it tells its own monitors and
    // model_cmp. A Mode B master declaring lane l dead tells mons of lane
    // l's pin set and cmps of the DUT lane's; the replay log of a Mode B
    // slave cuts cmps of its DUT lane's pin set with its own cmp, and a
    // passive monitor takes log, the slave's log, to read the cut.
    class a2c_pin_watchers;
        // The passive agents' monitors on this pin set.
        a2c_lane_watch      mons[$];
        // The model_cmps of the passive Mode B agents whose DUT lane is this
        // pin set.
        a2c_comparator_base cmps[$];
        // The replay log of the active Mode B slave with a lane on this pin
        // set, or null.
        a2c_replay_log_base log;
        // The full name of the active Mode B agent whose DUT lane is this
        // pin set, or "".
        string              owner;
    endclass : a2c_pin_watchers

    // Finds a pin set's watchers by the pin set's virtual interface, so the
    // agents of a port meet however the env arranges them, whatever their
    // number and build order. Each virtual interface type has its own table.
    // An agent registers in connect_phase and reads log and owner from
    // end_of_elaboration_phase on, when every agent has registered. Two
    // handles match only if they point at one interface instance: a second
    // instance bound to the same nets gets an entry of its own. A uvm_pool
    // cannot hold these, as an associative array cannot take a virtual
    // interface for its index.
    class a2c_pin_registry #(type VIF_T = int);
        protected static VIF_T            vifs[$];
        protected static a2c_pin_watchers sets[$];

        static function a2c_pin_watchers of(VIF_T vif);
            a2c_pin_watchers w;
            foreach (vifs[i]) if (vifs[i] == vif) return sets[i];
            w = new();
            vifs.push_back(vif);
            sets.push_back(w);
            return w;
        endfunction

        // For a passive Mode B agent at end_of_elaboration_phase. A port the
        // env leaves to other drivers, such as an internal port of a top
        // design, has no owner and needs none, so this is an info. It names
        // the config field, not the instance: %p of a virtual interface
        // prints a handle on Xcelium and every signal on VCS.
        static function void note_unowned(VIF_T vif, uvm_component agent, string port_name);
            if (of(vif).owner != "") return;
            `uvm_info_context("A2C_PASSIVE", $sformatf("%s: no active Mode B agent has the interface instance in this agent's cfg.vif as its own, so the agent learns of no lane death and no drain cut on the port. If an active agent drives the port, give it this same interface instance: another instance on the same nets does not match",
                                                       port_name), UVM_LOW, agent)
        endfunction
    endclass : a2c_pin_registry

    // What a2c_replay_drain reads of an a2c_replay_log, whatever its
    // response type.
    virtual class a2c_replay_log_base extends uvm_component;
        a2c_replay_lanes    driver;
        virtual a2c_clk_if  clk_vif;
        // The agent's model_cmp, which a cut also cuts.
        a2c_comparator_base cmp;
        // The passive agents on the DUT lane's pin set, whose model_cmps a
        // cut also cuts, or null.
        a2c_pin_watchers    watchers;
        // In cycles of clk_vif.
        int unsigned        drain_quiet_cycles = 1000;
        int unsigned        drain_deadline_cycles = 200000;
        // The clocks the lanes have, after a cut, to complete the
        // transactions it keeps. Below 0 it takes drain_deadline_cycles.
        int                 drain_catchup_cycles = -1;
        int unsigned        clock_stop_cycles = 1000;
        // Reports a cut as UVM_INFO, not an A2C_CUT warning, for a test
        // whose ports are meant to stay busy to the end.
        bit                 drain_cut_expected;
        // Indexed by a2c_lane_e: lane_starts() when the last drain ended, so
        // a run phase that resumes drains again when a lane has started a
        // transaction since.
        int unsigned        starts_at_drain[2];
        // Clocks since the DUT lane last started a transaction. The drain
        // counts them, and after a drain that cut the log goes on counting
        // them until the next drain starts.
        int unsigned        since_start;

        protected int unsigned replayed;
        // The transaction the model lane waits for, counted from 0, or -1,
        // and since when.
        protected int          waiting = -1;
        protected realtime     waiting_since;
        // The transactions the run keeps when the drain cut it, or 0, and
        // when it cut. catchup_end is when the drain gave up waiting for the
        // lanes to reach the cut, at the end of drain_catchup_cycles or on a
        // stopped clock, or 0.
        protected int unsigned cut_at;
        protected realtime     cut_time;
        protected realtime     catchup_end;
        // Whether the drain cut the log on its first clock because its DUT
        // lane had not paused since an earlier drain cut it.
        protected bit          recut;
        // Set by the driver before check_phase() when the model lane holds a
        // pick whose request it has not made, which the driver reports. A
        // cut that pick blocks is not short of catch-up clocks.
        bit                    pick_blocked;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // A generated base test sets these on every log through the
        // config_db as int unsigned, and the flag as bit, from
        // +a2c_drain_quiet_cycles, +a2c_drain_deadline_cycles,
        // +a2c_drain_catchup_cycles, +a2c_clock_stop_cycles and
        // +a2c_drain_cut_expected. A test overrides one log's in its own
        // build_phase(), after super.build_phase(), on the log's path, as
        // int unsigned, int or uvm_config_int, with the config_db's own
        // precedence whatever the type (a2c_get_config_int()); a
        // +uvm_set_config_int on the command line works too.
        virtual function void build_phase(uvm_phase phase);
            int unsigned catchup;
            super.build_phase(phase);
            void'(a2c_get_config_int(this, "a2c_drain_quiet_cycles", drain_quiet_cycles));
            void'(a2c_get_config_int(this, "a2c_drain_deadline_cycles", drain_deadline_cycles));
            if (a2c_get_config_int(this, "a2c_drain_catchup_cycles", catchup)) drain_catchup_cycles = catchup;
            void'(a2c_get_config_int(this, "a2c_clock_stop_cycles", clock_stop_cycles));
            a2c_get_config_bit(this, "a2c_drain_cut_expected", drain_cut_expected);
        endfunction

        function int unsigned catchup_cycles();
            return (drain_catchup_cycles < 0) ? drain_deadline_cycles : drain_catchup_cycles;
        endfunction

        // A log with no clk_vif stays out of the drain, as the drain could
        // not watch it.
        virtual function void start_of_simulation_phase(uvm_phase phase);
            super.start_of_simulation_phase(phase);
            if (driver == null) return;
            if (drain_deadline_cycles < drain_quiet_cycles) begin
                `uvm_error("A2C_CFG", $sformatf("%s: drain_deadline_cycles (+a2c_drain_deadline_cycles), %0d, is below drain_quiet_cycles (+a2c_drain_quiet_cycles), %0d, so the log can never be quiet for its window before the deadline",
                                                get_full_name(), drain_deadline_cycles, drain_quiet_cycles))
            end
            if (clk_vif == null) begin
                `uvm_error("A2C_CFG", $sformatf("%s: the replay log has no clk_vif, so the end-of-test drain cannot watch it", get_full_name()))
                return;
            end
            a2c_replay_drain::register(this);
        endfunction

        // The responses recorded and not yet replayed.
        pure virtual function int unsigned pending();

        // Whether the model lane's last can_replay() found its transaction
        // unrecorded, so the model lane leads and waits for the DUT lane.
        function bit model_waiting();
            return waiting >= 0;
        endfunction

        // Neither lane is inside a transaction, no recorded response waits
        // for the model lane, and the model lane waits for no record.
        function bit idle();
            return pending() == 0 && !model_waiting() && !driver.lane_busy(A2C_DUT_LANE) && !driver.lane_busy(A2C_MODEL_LANE);
        endfunction

        function string lane_counts();
            return $sformatf("DUT lane %0d started, %0d done; model lane %0d started, %0d done", driver.lane_starts(A2C_DUT_LANE),
                             driver.lane_done(A2C_DUT_LANE), driver.lane_starts(A2C_MODEL_LANE), driver.lane_done(A2C_MODEL_LANE));
        endfunction

        // What keeps the log from settling, for the drain's A2C_DRAIN
        // warnings. Names a busy lane before the quiet window; a larger
        // window does not help a lane stuck inside a transaction.
        function string unsettled();
            string why = "";
            string busy = "";
            if (cut_at != 0) return $sformatf("the lanes have not both completed the %0d transactions the cut keeps; %s", cut_at, lane_counts());
            if (model_waiting()) why = $sformatf("the model lane waits for transaction %0d, which the DUT lane has not recorded", waiting + 1);
            if (pending() > 0) begin
                if (why != "") why = {why, ", and "};
                why = {why, $sformatf("%0d transactions the DUT lane recorded wait for the model lane", pending())};
            end
            for (int l = 0; l < 2; l++) begin
                a2c_lane_e lane = a2c_lane_e'(l);
                if (!driver.lane_busy(lane)) continue;
                if (busy != "") busy = {busy, " and "};
                busy = {busy, $sformatf("the %s lane (%0d started, %0d done)", a2c_lane_name(lane), driver.lane_starts(lane),
                                        driver.lane_done(lane))};
            end
            if (busy != "") begin
                if (why != "") why = {why, ", and "};
                why = {why, busy, (driver.lane_busy(A2C_DUT_LANE) && driver.lane_busy(A2C_MODEL_LANE)) ? " are" : " is",
                       " inside a transaction"};
                return why;
            end
            if (why == "") begin
                why = $sformatf("the lanes were never idle for drain_quiet_cycles (+a2c_drain_quiet_cycles), %0d clocks, in a row",
                                drain_quiet_cycles);
            end
            return {why, "; ", lane_counts()};
        endfunction

        // Keeps the transactions the DUT lane has started, on both lanes,
        // and drops the later ones of either lane at the end of the test.
        function void cut(bit first_clock);
            cut_at   = driver.lane_starts(A2C_DUT_LANE);
            cut_time = $realtime;
            recut    = first_clock;
            if (cmp != null) cmp.cut(cut_at);
            if (watchers != null) foreach (watchers.cmps[i]) watchers.cmps[i].cut(cut_at);
        endfunction

        function void uncut();
            cut_at = 0;
            recut  = 0;
            if (cmp != null) cmp.uncut();
            if (watchers != null) foreach (watchers.cmps[i]) watchers.cmps[i].uncut();
        endfunction

        function int unsigned get_cut();
            return cut_at;
        endfunction

        function bit cut_reached();
            return cut_at != 0 && driver.lane_done(A2C_DUT_LANE) >= cut_at && driver.lane_done(A2C_MODEL_LANE) >= cut_at;
        endfunction

        function void end_catchup();
            catchup_end = $realtime;
        endfunction

        // Only the end of the run phase drains. UVM 1.2 calls the run
        // phase's phase_ready_to_end() only once the runtime phases running
        // beside it, main_phase() among them, have ended too, so a
        // hand-written test that objects only in main_phase() still drains,
        // from its drop when the phases after main_phase() hold no
        // objection (push_ack_mode_b_dst_main_phase_test).
        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (driver == null || phase.get_imp() != uvm_run_phase::get()) return;
            a2c_replay_drain::request(phase, this);
        endfunction

        // A cut that a lane did not reach is an A2C_REPLAY error, and the
        // transactions a cut drops an A2C_CUT warning, or UVM_INFO with
        // drain_cut_expected set. A cut that dropped nothing names no death.
        // The A2C_REPLAY error names the deaths up to the drain's give-up, as
        // a death during the catch-up can be what kept the lanes short. A
        // phase jump that ends the run phase during the catch-up leaves no
        // give-up, so the error is then dated now.
        virtual function void check_phase(uvm_phase phase);
            int unsigned dropped[2];
            string       what;
            string       death = a2c_replay_drain::death_context(cut_time);
            string       by_give_up = a2c_replay_drain::death_context((catchup_end != 0) ? catchup_end : $realtime);
            super.check_phase(phase);
            if (cut_at == 0) return;
            if (!cut_reached() && pick_blocked) begin
                `uvm_error("A2C_REPLAY", $sformatf("%s: the drain cut the run after transaction %0d, and the lanes did not both complete it, because the model lane holds a pick whose request it has not made, which the driver reports: %s%s",
                                                   get_full_name(), cut_at, lane_counts(), by_give_up))
            end else if (!cut_reached()) begin
                `uvm_error("A2C_REPLAY", $sformatf("%s: the drain cut the run after transaction %0d, and the lanes did not both complete it in the %0d clocks after the cut (drain_catchup_cycles, +a2c_drain_catchup_cycles): %s%s",
                                                   get_full_name(), cut_at, catchup_cycles(), lane_counts(), by_give_up))
            end
            foreach (dropped[l]) begin
                int unsigned n = driver.lane_starts(a2c_lane_e'(l));
                dropped[l] = (n > cut_at) ? n - cut_at : 0;
            end
            what = $sformatf("%s: the drain cut the run after pair %0d; %0d DUT lane and %0d model lane transactions after it go unchecked",
                             get_full_name(), cut_at, dropped[A2C_DUT_LANE], dropped[A2C_MODEL_LANE]);
            if (dropped[A2C_DUT_LANE] + dropped[A2C_MODEL_LANE] == 0) begin
                `uvm_info("A2C_CUT", what, UVM_LOW)
            end else if (drain_cut_expected) begin
                `uvm_info("A2C_CUT", {what, "; drain_cut_expected (+a2c_drain_cut_expected) is set", death}, UVM_LOW)
            end else if (recut) begin
                `uvm_warning("A2C_CUT", {what, ". An earlier drain cut the run, and the DUT lane had not paused for drain_quiet_cycles (+a2c_drain_quiet_cycles) clocks since, so this drain cut it again on its first clock; set +a2c_drain_cut_expected=1 (drain_cut_expected) where the ports are meant to stay busy", death})
            end else begin
                `uvm_warning("A2C_CUT", {what, ". The DUT lane did not pause for drain_quiet_cycles (+a2c_drain_quiet_cycles) clocks before the deadline; lower +a2c_drain_deadline_cycles (drain_deadline_cycles) to cut sooner, or set +a2c_drain_cut_expected=1 (drain_cut_expected) where the ports are meant to stay busy", death})
            end
        endfunction
    endclass : a2c_replay_log_base

    // Lets one responder serve both lanes of a Mode B port from one shared
    // model. The DUT lane applies each transaction and record()s its
    // response and delay; the model lane replays them in order and never
    // applies a transaction's effect. A driver sets driver and clk_vif, and
    // a2c_replay_drain then holds the end of the run phase while the model
    // lane catches up.
    class a2c_replay_log #(type T = uvm_sequence_item) extends a2c_replay_log_base;
        // Recorded and not yet replayed, oldest first, with each record's
        // delay and time. Parallel queues, not one of a struct holding T:
        // VCS W-2024.09 gives every specialization one struct type, so a log
        // of one T rejects the T of another.
        protected T            records[$];
        protected int unsigned delays[$];
        protected realtime     recorded_at[$];

        `uvm_component_param_utils(a2c_replay_log#(T))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function void record(T rsp, int unsigned delay);
            records.push_back(rsp);
            delays.push_back(delay);
            recorded_at.push_back($realtime);
        endfunction

        virtual function int unsigned pending();
            return records.size();
        endfunction

        // Whether the model lane's next transaction is recorded. Until it
        // is, check_phase() counts the model lane as waiting for it.
        function bit can_replay();
            int w = (records.size() == 0) ? int'(replayed) : -1;
            if (w >= 0 && w != waiting) waiting_since = $realtime;
            waiting = w;
            return records.size() != 0;
        endfunction

        // T may be a class handle or a value type; rsp is the recorded
        // handle, not a copy.
        function void replay(output T rsp, output int unsigned delay);
            if (records.size() == 0) begin
                `uvm_fatal("A2C_REPLAY", $sformatf("%s: the model lane replays transaction %0d, which the DUT lane has not recorded",
                                                   get_full_name(), replayed + 1))
            end
            rsp   = records.pop_front();
            delay = delays.pop_front();
            void'(recorded_at.pop_front());
            replayed++;
        endfunction

        // A cut log's records and wait past the cut go unchecked, and the
        // base reports those before it.
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (cut_at != 0) return;
            if (records.size() > 0) begin
                `uvm_error("A2C_REPLAY", $sformatf("%s: end of test with %0d responses the DUT lane recorded and the model lane never replayed, from transaction %0d%s",
                                               get_full_name(), records.size(), replayed + 1,
                                               a2c_replay_drain::death_context(recorded_at[0])))
            end
            if (waiting >= 0) begin
                `uvm_error("A2C_REPLAY", $sformatf("%s: the model lane waited for transaction %0d, which the DUT lane never recorded%s",
                                               get_full_name(), waiting + 1, a2c_replay_drain::death_context(waiting_since)))
            end
        endfunction
    endclass : a2c_replay_log

    // The one end-of-test drain every a2c_replay_log shares, so ports that
    // keep each other busy end together. Each time the run phase's last
    // objection drops, UVM calls phase_ready_to_end() on every log, and the
    // first call starts a drain: always the first time, and later only when
    // a lane has started a transaction since the last drain ended, because
    // every drain ends with each log settled, cut or given up. A drain
    // undoes the cuts of the one before it, as the run phase has resumed. It
    // watches each log at the rising edges of its own clk_vif, when no
    // driver moves, counts the log's quiet window and deadline in those
    // clocks, and drops once every log has settled or been given up:
    //   - a log settles once it has been idle() for drain_quiet_cycles
    //     clocks in a row with no lane starting a transaction, so a stream
    //     that pauses and then ends late is checked in full;
    //   - a log not settled at drain_deadline_cycles whose DUT lane started
    //     a transaction in its last drain_quiet_cycles clocks, as traffic
    //     that never pauses does, is cut after the transactions the DUT lane
    //     has started then. It settles once both lanes have completed them,
    //     and is given up if they have not within drain_catchup_cycles
    //     clocks more, which its check_phase() reports as A2C_REPLAY. A log
    //     the last drain cut, whose DUT lane has not gone drain_quiet_cycles
    //     clocks without starting a transaction since, is cut on the first
    //     clock instead of at the deadline;
    //   - any other log not settled at its deadline is given up with an
    //     A2C_DRAIN warning, and its check_phase() reports what is left;
    //   - a log whose clock has not risen for clock_stop_cycles periods and
    //     a half has a stopped clock. It settles if it is idle() and not
    //     cut, and is otherwise given up with an A2C_DRAIN warning. If the
    //     clock of a settled log rises again, the drain watches the log
    //     again from that edge, with a new quiet window and deadline. A log
    //     given up on a stopped clock is not watched again when the clock
    //     resumes: its A2C_DRAIN warning is already out and cannot be taken
    //     back, its check_phase() reports what the lanes have left by the
    //     end of the test, and the drain's end must not hang on a clock
    //     that may never return.
    // A Mode B master that declares a lane dead tells lane_dead(), which
    // only keeps the death for the reports: the drain goes on watching every
    // log, since a master's port has no log of its own. A report of an event,
    // such as a cut, a held pick or a record the model lane never replayed,
    // ends with death_context() of the time the event happened, which names
    // each death whose lane began to trail before it. The master declares a
    // death lane_skew_cycles or lone_lane_cycles clocks after that, so a
    // stall the event came out of may be declared long after the event. A
    // lane that began to trail after the event cannot have caused it. The
    // clause says only that the two may be related, since a stalled model
    // may as well be what made the lane fall behind.
    class a2c_replay_drain;
        protected static a2c_replay_log_base logs[$];
        protected static bit                 running;
        protected static bit                 drained;
        // The drains started, so a log's flow count stops at the next one.
        protected static int unsigned        drains;
        // Indexed as logs, for the drain running.
        protected static bit                 settled[];
        protected static bit                 given_up[];
        // Each lane's lane_starts() at the watcher's last update.
        protected static int unsigned        seen_starts[][2];
        // Counts the watchers' updates, so the drain wakes on each.
        protected static int unsigned        updates;
        // Each death: the port whose master declared it, the lane, when the
        // lane began to trail, and when the master declared it dead.
        protected static string              dead_who[$];
        protected static a2c_lane_e          dead_lane[$];
        protected static realtime            dead_since[$];
        protected static realtime            dead_time[$];

        static function void register(a2c_replay_log_base log);
            logs.push_back(log);
        endfunction

        // since is when the lane began to trail: the other lane's handshake
        // or completion it did not follow, or, for a lane left alone, its
        // last progress.
        static function void lane_dead(a2c_lane_e lane, string who, realtime since = $realtime);
            dead_who.push_back(who);
            dead_lane.push_back(lane);
            dead_since.push_back(since);
            dead_time.push_back($realtime);
        endfunction

        // The clause that ends a report of an event at time at: the deaths
        // whose lanes began to trail before at, leaving out those on port
        // except, or "". A lane that began to trail in the event's own time
        // step is left out, and so is a death declared in the time step the
        // clause is made, so the clause does not depend on the order of the
        // processes in either step.
        static function string death_context(realtime at, string except = "");
            string s = "";
            foreach (dead_time[i]) begin
                if (dead_since[i] >= at || dead_time[i] == $realtime || dead_who[i] == except) continue;
                s = {s, (s == "") ? "; " : " and ",
                     $sformatf("the %s lane of %s %swas declared dead at %0t (A2C_SKEW)", a2c_lane_name(dead_lane[i]), dead_who[i],
                               (dead_since[i] < dead_time[i]) ? $sformatf("began to trail at %0t and ", dead_since[i]) : "", dead_time[i])};
            end
            return (s == "") ? "" : {s, ", which may be related"};
        endfunction

        static function void request(uvm_phase phase, a2c_replay_log_base log);
            if (running || !needed()) return;
            running = 1;
            phase.raise_objection(log, "the model lanes are draining");
            fork
                drain(phase, log);
            join_none
        endfunction

        protected static function bit needed();
            if (!drained) return 1;
            foreach (logs[i]) begin
                for (int l = 0; l < 2; l++) begin
                    if (logs[i].driver.lane_starts(a2c_lane_e'(l)) != logs[i].starts_at_drain[l]) return 1;
                end
            end
            return 0;
        endfunction

        // Whether a lane of log i has started a transaction since its
        // watcher's last update.
        protected static function bit started(int unsigned i);
            for (int l = 0; l < 2; l++) begin
                if (logs[i].driver.lane_starts(a2c_lane_e'(l)) != seen_starts[i][l]) return 1;
            end
            return 0;
        endfunction

        protected static function void update(int unsigned i);
            for (int l = 0; l < 2; l++) seen_starts[i][l] = logs[i].driver.lane_starts(a2c_lane_e'(l));
            updates++;
        endfunction

        // The drain wakes on a watcher's update and reads every settled[] in
        // that time step, before the watchers of other logs whose clocks rise
        // then may have run, and a driver may have started a transaction at
        // the falling edge before. So a log settled and not cut must still be
        // idle(), with no start since its watcher looked, for the drain to
        // end; otherwise the drain waits for that watcher's update.
        protected static function bit still_settled(int unsigned i);
            if (logs[i].get_cut() != 0) return 1;
            return logs[i].idle() && !started(i);
        endfunction

        protected static function void give_up(int unsigned i);
            settled[i]  = 0;
            given_up[i] = 1;
            update(i);
        endfunction

        // Returns whether the log settled.
        protected static function bit clock_stopped(int unsigned i);
            if (logs[i].get_cut() == 0 && logs[i].idle()) begin
                settled[i] = 1;
                update(i);
                return 1;
            end
            `uvm_warning_context("A2C_DRAIN", $sformatf("the clock stopped before the log settled: %s%s", logs[i].unsettled(), death_context($realtime)),
                                 logs[i])
            give_up(i);
            return 0;
        endfunction

        protected static function void count_start(a2c_replay_log_base log, ref int unsigned starts);
            log.since_start = (log.driver.lane_starts(A2C_DUT_LANE) != starts) ? 0 : log.since_start + 1;
            starts = log.driver.lane_starts(A2C_DUT_LANE);
        endfunction

        protected static task watch(int unsigned i, bit recut);
            a2c_replay_log_base log = logs[i];
            int unsigned        quiet = log.drain_quiet_cycles;
            int unsigned        stop = log.clock_stop_cycles;
            int unsigned        deadline = recut ? 1 : log.drain_deadline_cycles;
            int unsigned        cycles = 0;
            int unsigned        idle = 0;
            int unsigned        starts = log.driver.lane_starts(A2C_DUT_LANE);
            bit                 ticking;
            if (!recut) log.since_start = quiet;
            forever begin
                log.clk_vif.next_rise(stop, ticking);
                if (!ticking) begin
                    if (!clock_stopped(i)) return;
                    @(posedge log.clk_vif.clk);
                    cycles   = 0;
                    idle     = 0;
                    deadline = log.drain_deadline_cycles;
                end
                cycles++;
                idle = (log.idle() && !started(i)) ? idle + 1 : 0;
                count_start(log, starts);
                settled[i] = idle >= quiet;
                update(i);
                if (settled[i] || cycles < deadline) continue;
                if (log.since_start < quiet) break;
                // A re-cut log whose DUT lane has just paused.
                if (cycles < log.drain_deadline_cycles) begin
                    deadline = log.drain_deadline_cycles;
                    continue;
                end
                `uvm_warning_context("A2C_DRAIN", $sformatf("the drain reached its deadline, drain_deadline_cycles (+a2c_drain_deadline_cycles), of %0d clocks before the log settled: %s%s",
                                                            log.drain_deadline_cycles, log.unsettled(), death_context($realtime)), log)
                give_up(i);
                return;
            end
            log.cut(cycles < log.drain_deadline_cycles);
            for (int unsigned c = 0; !log.cut_reached(); c++) begin
                if (c == log.catchup_cycles()) begin
                    log.end_catchup();
                    give_up(i);
                    break;
                end
                log.clk_vif.next_rise(stop, ticking);
                if (!ticking) begin
                    log.end_catchup();
                    void'(clock_stopped(i));
                    break;
                end
                count_start(log, starts);
            end
            if (!given_up[i]) begin
                settled[i] = 1;
                update(i);
            end
            // Goes on counting since_start to the end of the drain, so the
            // next drain re-cuts the log only if its DUT lane is still
            // flowing. @(posedge) rather than next_rise(), which returns at
            // once, in a zero-time loop, on a stopped clock.
            forever begin
                @(posedge log.clk_vif.clk);
                count_start(log, starts);
            end
        endtask

        // Goes on counting since_start for a log the drain cut, until its
        // DUT lane pauses for drain_quiet_cycles clocks or the next drain
        // starts.
        protected static task count_flow(a2c_replay_log_base log, int unsigned drain);
            int unsigned starts = log.driver.lane_starts(A2C_DUT_LANE);
            while (log.since_start < log.drain_quiet_cycles) begin
                @(posedge log.clk_vif.clk);
                if (drains != drain) return;
                count_start(log, starts);
            end
        endtask

        protected static task drain(uvm_phase phase, a2c_replay_log_base holder);
            bit recut[] = new[logs.size()];
            drains++;
            settled     = new[logs.size()];
            given_up    = new[logs.size()];
            seen_starts = new[logs.size()];
            foreach (logs[i]) recut[i] = logs[i].get_cut() != 0 && logs[i].since_start < logs[i].drain_quiet_cycles;
            foreach (logs[i]) logs[i].uncut();
            foreach (logs[i]) begin
                automatic int unsigned k = i;
                automatic bit          r = recut[i];
                for (int l = 0; l < 2; l++) seen_starts[i][l] = logs[i].driver.lane_starts(a2c_lane_e'(l));
                fork
                    watch(k, r);
                join_none
            end
            forever begin
                bit          finished = 1;
                int unsigned seen = updates;
                foreach (logs[i]) finished &= (settled[i] && still_settled(i)) || given_up[i];
                if (finished) break;
                wait (updates != seen);
            end
            disable fork;
            drained = 1;
            foreach (logs[i]) begin
                automatic a2c_replay_log_base log = logs[i];
                for (int l = 0; l < 2; l++) log.starts_at_drain[l] = log.driver.lane_starts(a2c_lane_e'(l));
                if (log.get_cut() == 0) continue;
                fork
                    count_flow(log, drains);
                join_none
            end
            running = 0;
            phase.drop_objection(holder, "the model lanes are drained");
        endtask
    endclass : a2c_replay_drain

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

    function automatic bit a2c_contains(string s, string sub);
        for (int i = 0; i + sub.len() <= s.len(); i++) begin
            if (s.substr(i, i + sub.len() - 1) == sub) return 1;
        end
        return 0;
    endfunction

    // Turns each UVM_ERROR with id demote_id into UVM_INFO and counts it, so a
    // negative test can pass when the check it provokes fires. With
    // demote_text set, only the messages that contain it are demoted.
    class a2c_error_demoter extends uvm_report_catcher;
        string       demote_id = "";
        string       demote_text = "";
        int unsigned demoted;

        `uvm_object_utils(a2c_error_demoter)

        function new(string name = "a2c_error_demoter");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_severity() == UVM_ERROR && get_id() == demote_id
                    && (demote_text == "" || a2c_contains(get_message(), demote_text))) begin
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
