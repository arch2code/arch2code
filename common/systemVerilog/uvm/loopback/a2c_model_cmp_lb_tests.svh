// Loopback tests of a2c_uvm_pkg's Mode B classes: the in-order and status
// comparators, the midstream guard and the replay log. Included in
// a2c_uvm_loopback_pkg after the rdy_vld, status and a2c_txn_counter
// tests, whose item types and typedefs they use. The tests drive no pins:
// they write synthetic items, uvm_reg_items included, into the classes'
// exports through analysis ports of their own.

    typedef a2c_in_order_comparator #(rv_item_t) lb_cmp_t;
    typedef a2c_status_comparator #(st_item_t)   lb_st_cmp_t;
    typedef a2c_replay_log #(rv_item_t)          lb_replay_t;

    function automatic rv_item_t lb_rv_item(lb_data_t data);
        rv_item_t it = rv_item_t::type_id::create("it");
        it.data = data;
        return it;
    endfunction

    function automatic st_item_t lb_st_item(lb_data_t data);
        st_item_t it = st_item_t::type_id::create("it");
        it.data = data;
        return it;
    endfunction

    // Pairs per tag bits [1:0], so items of one key stay in order and items
    // of different keys may pass each other.
    class lb_keyed_cmp extends lb_cmp_t;
        `uvm_component_utils(lb_keyed_cmp)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function string key(rv_item_t t);
            return $sformatf("%0d", t.data.tag[1:0]);
        endfunction
    endclass : lb_keyed_cmp

    class lb_bounds_cmp extends lb_st_cmp_t;
        `uvm_component_utils(lb_bounds_cmp)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function bit [63:0] value(st_item_t t);
            return 64'(t.data);
        endfunction
    endclass : lb_bounds_cmp

    // n_items random items reach an a2c_in_order_comparator on both sides,
    // each side with its own random gaps. Every pair matches. Subclasses
    // change model items, add unpaired items to one side, reorder across
    // keys, or inject a mismatch.
    class model_cmp_match_test extends lb_mode_b_base;
        lb_cmp_t                       cmp;
        uvm_analysis_port #(rv_item_t) dut_ap;
        uvm_analysis_port #(rv_item_t) model_ap;
        lb_data_t                      dut_data[$];
        lb_data_t                      model_data[$];
        int unsigned                   want_pairs;
        // Indexed by a2c_lane_e: the items each side has sent, and the pairs
        // it led.
        int unsigned                   sent[2];
        int unsigned                   led[2];

        `uvm_component_utils(model_cmp_match_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_cmp_t create_cmp();
            return lb_cmp_t::type_id::create("cmp", this);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            cmp      = create_cmp();
            dut_ap   = new("dut_ap", this);
            model_ap = new("model_ap", this);
            for (int unsigned i = 0; i < n_items; i++) dut_data.push_back(lb_data_t'($urandom()));
            model_data = dut_data;
            want_pairs = n_items;
            build_streams();
        endfunction

        // Edits dut_data, model_data, want_pairs and the expectations.
        virtual function void build_streams();
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dut_ap.connect(cmp.dut_export);
            model_ap.connect(cmp.model_export);
        endfunction

        protected task send(a2c_lane_e lane, int unsigned from, int unsigned to);
            for (int unsigned i = from; i < to; i++) begin
                if (sent[(lane == A2C_DUT_LANE) ? A2C_MODEL_LANE : A2C_DUT_LANE] <= i) led[lane]++;
                sent[lane]++;
                if (lane == A2C_DUT_LANE) dut_ap.write(lb_rv_item(dut_data[i]));
                else model_ap.write(lb_rv_item(model_data[i]));
                repeat ($urandom_range(2, 0)) clk_vif.sample_edge();
            end
        endtask

        // The items go out in blocks of 20, the DUT side's block first in even
        // blocks and the model side's in odd ones, so each side leads half the
        // pairs and up to 20 items wait for their pair.
        virtual task run_phase(uvm_phase phase);
            int unsigned last = (dut_data.size() > model_data.size()) ? dut_data.size() : model_data.size();
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            for (int unsigned from = 0; from < last; from += 20) begin
                a2c_lane_e first = ((from / 20) % 2 == 0) ? A2C_DUT_LANE : A2C_MODEL_LANE;
                a2c_lane_e second = (first == A2C_DUT_LANE) ? A2C_MODEL_LANE : A2C_DUT_LANE;
                send(first, from, end_of(first, from + 20));
                send(second, from, end_of(second, from + 20));
            end
            phase.drop_objection(this);
        endtask

        protected function int unsigned end_of(a2c_lane_e lane, int unsigned to);
            int unsigned size = (lane == A2C_DUT_LANE) ? dut_data.size() : model_data.size();
            return (to < size) ? to : size;
        endfunction

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d pairs, %0d led by the DUT side and %0d by the model side, %0d %s",
                                            cmp.get_pairs(), led[A2C_DUT_LANE], led[A2C_MODEL_LANE], demoter.demoted, demote_id),
                      UVM_NONE)
            if (cmp.get_pairs() != want_pairs) begin
                `uvm_error("LB_MODE_B", $sformatf("expected %0d pairs, got %0d", want_pairs, cmp.get_pairs()))
            end
            if (led[A2C_DUT_LANE] == 0 || led[A2C_MODEL_LANE] == 0) begin
                `uvm_error("LB_MODE_B", "one side never led, so pairing with the other side first went untested")
            end
            super.report_phase(phase);
        endfunction
    endclass : model_cmp_match_test

    // The model's item at one index differs: one A2C_MODEL_CMP naming the
    // comparator and the pair, with both items printed.
    class model_cmp_mismatch_test extends model_cmp_match_test;
        `uvm_component_utils(model_cmp_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            int unsigned k = $urandom_range(n_items - 1, 0);
            model_data[k].value = ~model_data[k].value;
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.cmp: pair %0d: DUT %s, model %s", k + 1,
                                          lb_rv_item(dut_data[k]).convert2string(), lb_rv_item(model_data[k]).convert2string()));
        endfunction
    endclass : model_cmp_mismatch_test

    // Two DUT items with no model item: check_phase reports them once.
    class model_cmp_dut_leftover_test extends model_cmp_match_test;
        `uvm_component_utils(model_cmp_dut_leftover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            dut_data.push_back(lb_data_t'($urandom()));
            dut_data.push_back(lb_data_t'($urandom()));
            want_errors = 1;
            want_text.push_back($sformatf("end of test with 2 DUT items unpaired after %0d pairs, first %s", n_items,
                                          lb_rv_item(dut_data[n_items]).convert2string()));
        endfunction
    endclass : model_cmp_dut_leftover_test

    // Three model items with no DUT item: check_phase reports them once.
    class model_cmp_model_leftover_test extends model_cmp_match_test;
        `uvm_component_utils(model_cmp_model_leftover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            repeat (3) model_data.push_back(lb_data_t'($urandom()));
            want_errors = 1;
            want_text.push_back($sformatf("end of test with 3 model items unpaired after %0d pairs", n_items));
        endfunction
    endclass : model_cmp_model_leftover_test

    // The model side delivers the DUT's items merged across four keys in a
    // random order, each key's items still in order. The keyed comparator
    // pairs them all; the order across keys must have changed somewhere.
    class model_cmp_keyed_test extends model_cmp_match_test;
        int unsigned moved;

        `uvm_component_utils(model_cmp_keyed_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_cmp_t create_cmp();
            return lb_keyed_cmp::type_id::create("cmp", this);
        endfunction

        virtual function void build_streams();
            lb_data_t per_key[4][$];
            foreach (dut_data[i]) per_key[dut_data[i].tag[1:0]].push_back(dut_data[i]);
            model_data.delete();
            while (model_data.size() < dut_data.size()) begin
                int unsigned k = $urandom_range(3, 0);
                if (per_key[k].size() > 0) model_data.push_back(per_key[k].pop_front());
            end
            foreach (dut_data[i]) moved += (model_data[i] !== dut_data[i]);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d of %0d model items arrive at another position than the DUT's", moved, n_items),
                      UVM_NONE)
            if (moved == 0) `uvm_error("LB_MODE_B", "the model order matches the DUT order, so keys were not exercised")
            super.report_phase(phase);
        endfunction
    endclass : model_cmp_keyed_test

    // Matching streams with pair 5 injected: one A2C_MODEL_CMP, at pair 5.
    class model_cmp_inject_test extends model_cmp_match_test;
        `uvm_component_utils(model_cmp_inject_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.cmp: pair 5 (injected mismatch): DUT %s, model %s",
                                          lb_rv_item(dut_data[4]).convert2string(), lb_rv_item(model_data[4]).convert2string()));
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            cmp.inject_mismatch(5);
        endfunction
    endclass : model_cmp_inject_test

    // A status comparator under the policy configure() sets, fed by hand.
    class lb_status_cmp_base extends lb_mode_b_base;
        lb_st_cmp_t                    cmp;
        uvm_analysis_port #(st_item_t) dut_ap;
        uvm_analysis_port #(st_item_t) model_ap;

        `uvm_component_utils(lb_status_cmp_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_st_cmp_t create_cmp();
            return lb_st_cmp_t::type_id::create("cmp", this);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            cmp      = create_cmp();
            dut_ap   = new("dut_ap", this);
            model_ap = new("model_ap", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dut_ap.connect(cmp.dut_export);
            model_ap.connect(cmp.model_export);
        endfunction

        function void dut(lb_data_t v);
            dut_ap.write(lb_st_item(v));
        endfunction

        function void model(lb_data_t v);
            model_ap.write(lb_st_item(v));
        endfunction
    endclass : lb_status_cmp_base

    // stable, the default: a stable point before any value reports the
    // missing lane; values that differ between stable points are not
    // compared; the stable point that finds them different reports one
    // mismatch, at pair 2.
    class status_cmp_stable_test extends lb_status_cmp_base;
        `uvm_component_utils(status_cmp_stable_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 2;
            want_text.push_back("uvm_test_top.cmp: stable point with no value reported on the DUT lane and the model lane");
            want_text.push_back($sformatf("uvm_test_top.cmp: pair 2: DUT %s, model %s", lb_st_item('h200002).convert2string(),
                                          lb_st_item('h300003).convert2string()));
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            if (cmp.policy != A2C_STATUS_STABLE || !cmp.auto_stable) begin
                `uvm_error("LB_MODE_B", $sformatf("defaults: policy %s, auto_stable %0d", cmp.policy.name(), cmp.auto_stable))
            end
            cmp.stable_point();
            model('h100001);
            dut('h000000);
            dut('h100001);
            cmp.stable_point();
            model('h200002);
            model('h300003);
            dut('h200002);
            cmp.stable_point();
            dut('h300003);
            cmp.stable_point();
            if (cmp.get_pairs() != 3) `uvm_error("LB_MODE_B", $sformatf("expected 3 pairs, got %0d", cmp.get_pairs()))
            phase.drop_objection(this);
        endtask
    endclass : status_cmp_stable_test

    // bounds: one DUT value below lo and one model value above hi, each
    // reported once with its lane; a stable point compares nothing.
    class status_cmp_bounds_test extends lb_status_cmp_base;
        `uvm_component_utils(status_cmp_bounds_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 2;
            want_text.push_back($sformatf("uvm_test_top.cmp: DUT value %s is outside 0x100..0x200", lb_st_item('h50).convert2string()));
            want_text.push_back($sformatf("uvm_test_top.cmp: model value %s is outside 0x100..0x200",
                                          lb_st_item('h201).convert2string()));
        endfunction

        virtual function lb_st_cmp_t create_cmp();
            return lb_bounds_cmp::type_id::create("cmp", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            cmp.policy = A2C_STATUS_BOUNDS;
            cmp.lo     = 'h100;
            cmp.hi     = 'h200;
            dut('h100);
            model('h200);
            dut('h150);
            dut('h50);
            model('h201);
            model('h180);
            cmp.stable_point();
            if (cmp.get_pairs() != 0) `uvm_error("LB_MODE_B", $sformatf("bounds compared %0d pairs", cmp.get_pairs()))
            phase.drop_objection(this);
        endtask
    endclass : status_cmp_bounds_test

    // off: lanes that never agree raise nothing, and each of the six values
    // logs one A2C_STATUS line, whatever the run's default verbosity.
    class status_cmp_off_test extends lb_status_cmp_base;
        `uvm_component_utils(status_cmp_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            cmp.set_report_id_verbosity("A2C_STATUS", UVM_MEDIUM);
        endfunction

        virtual task run_phase(uvm_phase phase);
            int unsigned logged;
            phase.raise_objection(this);
            cmp.policy = A2C_STATUS_OFF;
            for (int unsigned i = 0; i < 3; i++) begin
                dut(lb_data_t'(i));
                model(lb_data_t'(i + 7));
                cmp.stable_point();
            end
            logged = uvm_report_server::get_server().get_id_count("A2C_STATUS");
            `uvm_info("LB_STATS", $sformatf("%0d A2C_STATUS lines", logged), UVM_NONE)
            if (logged != 6) `uvm_error("LB_MODE_B", $sformatf("expected 6 A2C_STATUS lines, got %0d", logged))
            phase.drop_objection(this);
        endtask
    endclass : status_cmp_off_test

    // A register for the guard's messages to name.
    class lb_reg extends uvm_reg;
        `uvm_object_utils(lb_reg)

        function new(string name = "lb_reg");
            super.new(name, 32, UVM_NO_COVERAGE);
        endfunction
    endclass : lb_reg

    // A guard over a dual-lane counter and an in-order comparator, with
    // uvm_reg_items written to it by hand as the register predictor's
    // reg_ap would.
    class lb_guard_base extends lb_mode_b_base;
        a2c_midstream_guard               guard;
        a2c_txn_counter #(rv_item_t)      counter;
        lb_cmp_t                          cmp;
        lb_reg                            ctrl;
        uvm_analysis_port #(uvm_reg_item) reg_ap;
        uvm_analysis_port #(rv_item_t)    dut_ap;
        uvm_analysis_port #(rv_item_t)    model_ap;
        // With clear, the lanes feed the counter alone.
        bit                               with_cmp = 1;

        `uvm_component_utils(lb_guard_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_MIDSTREAM";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            guard   = a2c_midstream_guard::type_id::create("guard", this);
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            cmp     = lb_cmp_t::type_id::create("cmp", this);
            ctrl    = lb_reg::type_id::create("ctrl");
            counter.port_name = "rv";
            counter.dual      = 1;
            reg_ap   = new("reg_ap", this);
            dut_ap   = new("dut_ap", this);
            model_ap = new("model_ap", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            guard.counters.push_back(counter);
            guard.comparators.push_back(cmp);
            reg_ap.connect(guard.analysis_export);
            dut_ap.connect(counter.analysis_export);
            model_ap.connect(counter.model_export);
            if (with_cmp) begin
                dut_ap.connect(cmp.dut_export);
                model_ap.connect(cmp.model_export);
            end
        endfunction

        // An access to ctrl, or with no element to offset.
        function void access(uvm_access_e kind, bit to_ctrl = 1, uvm_reg_addr_t offset = 0);
            uvm_reg_item it = uvm_reg_item::type_id::create("it");
            it.kind   = kind;
            it.offset = offset;
            if (to_ctrl) begin
                it.element      = ctrl;
                it.element_kind = UVM_REG;
            end
            reg_ap.write(it);
        endfunction

        // n items on one lane, data i, or ~i when flip is set.
        function void lane(a2c_lane_e l, int unsigned n, bit flip = 0);
            for (int unsigned i = 0; i < n; i++) begin
                lb_data_t d = flip ? ~lb_data_t'(i) : lb_data_t'(i);
                if (l == A2C_DUT_LANE) dut_ap.write(lb_rv_item(lb_data_t'(i)));
                else model_ap.write(lb_rv_item(d));
            end
        endfunction
    endclass : lb_guard_base

    // Writes while quiescent pass. A write while both lanes are short, and
    // one with no element while only the model lane is, each raise
    // A2C_MIDSTREAM; a read while short does not.
    class midstream_guard_error_test extends lb_guard_base;
        `uvm_component_utils(midstream_guard_error_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 2;
            want_text.push_back("write to ctrl while outputs have transactions pending: rv (DUT 4, model 4). Configuration may change only while the datapath is quiescent; +a2c_predict_midstream=1 relaxes the rule for debugging");
            want_text.push_back("write to address 0x14 while outputs have transactions pending: rv (DUT 0, model 4).");
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            access(UVM_WRITE);
            counter.expect_count(4);
            access(UVM_WRITE);
            access(UVM_READ);
            lane(A2C_DUT_LANE, 4);
            access(UVM_WRITE, 0, 'h14);
            lane(A2C_MODEL_LANE, 4);
            access(UVM_WRITE);
            phase.drop_objection(this);
        endtask
    endclass : midstream_guard_error_test

    // Under predict_midstream, which +a2c_predict_midstream=1 sets, a write
    // while pending logs one A2C_MIDSTREAM info and opens the comparator's
    // window: no item has arrived, so it covers pairs 1 to 4. Six mismatched pairs follow: the
    // first four are A2C_MODEL_CMP_MIDSTREAM warnings, the last two
    // A2C_MODEL_CMP errors.
    class midstream_guard_predict_test extends lb_guard_base;
        `uvm_component_utils(midstream_guard_predict_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MODEL_CMP";
            want_errors = 2;
            want_text.push_back("uvm_test_top.cmp: pair 5: DUT");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            guard.predict_midstream = 1;
            cmp.midstream_beats     = 4;
        endfunction

        virtual task run_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            phase.raise_objection(this);
            counter.expect_count(6);
            access(UVM_WRITE);
            lane(A2C_DUT_LANE, 6);
            lane(A2C_MODEL_LANE, 6, 1);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_MIDSTREAM, %0d A2C_MODEL_CMP_MIDSTREAM", srv.get_id_count("A2C_MIDSTREAM"),
                                            srv.get_id_count("A2C_MODEL_CMP_MIDSTREAM")), UVM_NONE)
            if (srv.get_id_count("A2C_MIDSTREAM") != 1) `uvm_error("LB_MODE_B", "expected one A2C_MIDSTREAM info line")
            if (srv.get_id_count("A2C_MODEL_CMP_MIDSTREAM") != 4) `uvm_error("LB_MODE_B", "expected four A2C_MODEL_CMP_MIDSTREAM warnings")
            phase.drop_objection(this);
        endtask
    endclass : midstream_guard_predict_test

    // The DUT lane records n_items / 4 transactions in one replay log, two
    // clocks after each starts, and the model lane replays them in order,
    // sampling can_replay() each clock until its next one is recorded. It
    // must get the recorded response handle and delay. The model lane has
    // the longer gaps, so it never waits; with follow set it has the
    // shorter ones and must wait for some.
    class replay_log_test extends lb_mode_b_base;
        lb_replay_t  log;
        int unsigned n;
        bit          follow = 0;
        // Indexed by a2c_lane_e: how many transactions each lane runs, and
        // whether it has run them all.
        int unsigned run[2];
        bit          done[2];
        // Replays the model lane asked for before they were recorded, and
        // all its replays.
        int unsigned early;
        int unsigned replays;
        rv_item_t    rsp_of[int unsigned];
        int unsigned delay_of[int unsigned];

        `uvm_component_utils(replay_log_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_REPLAY";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            log = lb_replay_t::type_id::create("log", this);
            n   = n_items / 4;
            run = '{n, n};
            configure();
        endfunction

        // Sets follow, run and the expectations.
        virtual function void configure();
        endfunction

        protected function int unsigned gap(a2c_lane_e lane);
            bit fast = (lane == A2C_MODEL_LANE) == follow;
            return fast ? $urandom_range(1, 0) : $urandom_range(6, 4);
        endfunction

        protected task record_all();
            for (int unsigned i = 0; i < run[A2C_DUT_LANE]; i++) begin
                repeat (gap(A2C_DUT_LANE)) clk_vif.sample_edge();
                rsp_of[i]   = lb_rv_item(lb_data_t'($urandom()));
                delay_of[i] = $urandom_range(3, 0);
                repeat (2) clk_vif.sample_edge();
                log.record(rsp_of[i], delay_of[i]);
                repeat (delay_of[i]) clk_vif.sample_edge();
            end
            done[A2C_DUT_LANE] = 1;
        endtask

        protected task replay_all();
            for (int unsigned i = 0; i < run[A2C_MODEL_LANE]; i++) begin
                rv_item_t    rsp;
                int unsigned delay;
                repeat (gap(A2C_MODEL_LANE)) clk_vif.sample_edge();
                if (!log.can_replay()) early++;
                while (!log.can_replay()) clk_vif.sample_edge();
                log.replay(rsp, delay);
                replays++;
                if (rsp != rsp_of[i] || delay != delay_of[i]) begin
                    `uvm_error("LB_REPLAY", $sformatf("transaction %0d replayed %s delay %0d, recorded %s delay %0d", i,
                                                      rsp.convert2string(), delay, rsp_of[i].convert2string(), delay_of[i]))
                end
                repeat (delay) clk_vif.sample_edge();
            end
            done[A2C_MODEL_LANE] = 1;
        endtask

        // A model lane left waiting never finishes, so after the DUT lane is
        // done the test waits only while the model lane replays a
        // transaction at least once every 50 clocks.
        virtual task run_phase(uvm_phase phase);
            int unsigned idle = 0;
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                record_all();
                replay_all();
            join_none
            wait (done[A2C_DUT_LANE]);
            while (!done[A2C_MODEL_LANE] && idle < 50) begin
                int unsigned last = replays;
                clk_vif.sample_edge();
                idle = (replays == last) ? idle + 1 : 0;
            end
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d transactions, %0d replays asked for before they were recorded", n, early), UVM_NONE)
            if (follow && early == 0) `uvm_error("LB_REPLAY", "the model lane never asked for a transaction before it was recorded")
            if (!follow && early != 0) `uvm_error("LB_REPLAY", $sformatf("the slower model lane asked early %0d times", early))
            super.report_phase(phase);
        endfunction
    endclass : replay_log_test

    // The model lane stops two transactions short: check_phase reports the
    // two records it never replayed, once.
    class replay_log_unconsumed_test extends replay_log_test;
        `uvm_component_utils(replay_log_unconsumed_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            run         = '{n, n - 2};
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.log: end of test with 2 responses the DUT lane recorded and the model lane never replayed, from transaction %0d",
                                          n - 2));
        endfunction
    endclass : replay_log_unconsumed_test

    // The faster model lane waits for transactions before they are recorded.
    class replay_log_follow_test extends replay_log_test;
        `uvm_component_utils(replay_log_follow_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            follow = 1;
        endfunction
    endclass : replay_log_follow_test

    // The DUT lane stops two transactions early, so the model lane waits for
    // one the DUT lane never records: one report.
    class replay_log_waiting_test extends replay_log_test;
        `uvm_component_utils(replay_log_waiting_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            follow      = 1;
            run         = '{n - 2, n};
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.log: the model lane waited for transaction %0d, which the DUT lane never recorded",
                                          n - 2));
        endfunction
    endclass : replay_log_waiting_test

    // The keyed reorder with one model item's value changed: one
    // A2C_MODEL_CMP that names the item's key.
    class model_cmp_keyed_mismatch_test extends model_cmp_keyed_test;
        `uvm_component_utils(model_cmp_keyed_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            int unsigned j;
            lb_data_t    was;
            super.build_streams();
            j   = $urandom_range(n_items - 1, 0);
            was = model_data[j];
            model_data[j].value = ~model_data[j].value;
            want_errors = 1;
            want_text.push_back($sformatf(" key %0d: DUT %s, model %s", was.tag[1:0], lb_rv_item(was).convert2string(),
                                          lb_rv_item(model_data[j]).convert2string()));
        endfunction
    endclass : model_cmp_keyed_mismatch_test

    // 30 mismatched pairs under the default max_reported of 10: ten print in
    // full and check_phase adds one summary error, eleven in all.
    class model_cmp_cap_test extends model_cmp_match_test;
        `uvm_component_utils(model_cmp_cap_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            for (int unsigned i = 0; i < 30; i++) model_data[i].value = ~model_data[i].value;
            want_errors = 11;
            want_text.push_back("uvm_test_top.cmp: pair 10: DUT");
            want_text.push_back("uvm_test_top.cmp: 30 mismatches in all, 20 not printed, 20 of those outside a midstream window");
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (demoter.count("pair 11:") != 0) `uvm_error("LB_MODE_B", "pair 11 printed beyond max_reported")
            super.report_phase(phase);
        endfunction
    endclass : model_cmp_cap_test

    // The DUT leftovers with counted set: a counter covers the port, so
    // check_phase reports nothing.
    class model_cmp_counted_test extends model_cmp_dut_leftover_test;
        `uvm_component_utils(model_cmp_counted_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            super.build_streams();
            want_errors = 0;
            want_text.delete();
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            cmp.counted = 1;
        endfunction
    endclass : model_cmp_counted_test

    // A window opened with 10 DUT items queued and no model item covers
    // pairs 1 to 10 + midstream_beats. With midstream_beats 4 and 20
    // mismatched pairs, 14 are A2C_MODEL_CMP_MIDSTREAM warnings and 6 are
    // A2C_MODEL_CMP errors, the first at pair 15.
    class midstream_window_anchor_test extends lb_guard_base;
        `uvm_component_utils(midstream_window_anchor_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MODEL_CMP";
            want_errors = 6;
            want_text.push_back("uvm_test_top.cmp: pair 15: DUT");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            guard.predict_midstream = 1;
            cmp.midstream_beats     = 4;
            cmp.max_reported        = 100;
        endfunction

        virtual task run_phase(uvm_phase phase);
            int unsigned warned;
            phase.raise_objection(this);
            counter.expect_count(20);
            lane(A2C_DUT_LANE, 10);
            access(UVM_WRITE);
            lane(A2C_DUT_LANE, 10);
            lane(A2C_MODEL_LANE, 20, 1);
            warned = uvm_report_server::get_server().get_id_count("A2C_MODEL_CMP_MIDSTREAM");
            `uvm_info("LB_STATS", $sformatf("%0d A2C_MODEL_CMP_MIDSTREAM", warned), UVM_NONE)
            if (warned != 14) `uvm_error("LB_MODE_B", $sformatf("expected 14 A2C_MODEL_CMP_MIDSTREAM warnings, got %0d", warned))
            phase.drop_objection(this);
        endtask
    endclass : midstream_window_anchor_test

    // A reported shortfall still counts as pending. The DUT lane delivers 2
    // of 4 and the wait reports it, demoted by a second demoter: a write
    // then names the 2 written off. A second expect_count() writes them off
    // and declares 3 more on each lane, which the next write names. Once
    // both lanes have their 3, a write passes. The lanes' streams do not
    // pair up, so no comparator is fed.
    class midstream_guard_shortfall_test extends lb_guard_base;
        lb_recording_demoter count_demoter;

        `uvm_component_utils(midstream_guard_shortfall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            with_cmp    = 0;
            want_errors = 2;
            want_text.push_back("write to ctrl while outputs have transactions pending: rv (DUT 2, model 0).");
            want_text.push_back("write to ctrl while outputs have transactions pending: rv (DUT 3, model 3).");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            count_demoter = lb_recording_demoter::type_id::create("count_demoter");
            count_demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, count_demoter);
        endfunction

        function void expect_pending(int unsigned outstanding, int unsigned pending);
            if (counter.outstanding() != outstanding || counter.pending() != pending) begin
                `uvm_error("LB_MODE_B", $sformatf("outstanding %0d and pending %0d, expected %0d and %0d", counter.outstanding(),
                                              counter.pending(), outstanding, pending))
            end
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            counter.expect_count(4);
            lane(A2C_DUT_LANE, 2);
            lane(A2C_MODEL_LANE, 4);
            counter.wait_for_count(clk_vif, 5, 0);
            expect_pending(0, 2);
            access(UVM_WRITE);
            counter.expect_count(3);
            expect_pending(6, 6);
            access(UVM_WRITE);
            lane(A2C_DUT_LANE, 3);
            lane(A2C_MODEL_LANE, 3);
            expect_pending(0, 0);
            access(UVM_WRITE);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            if (count_demoter.demoted != 1 || count_demoter.count("rv DUT lane: deadline") != 1) begin
                `uvm_error("LB_MODE_B", $sformatf("expected one DUT lane A2C_TXN_COUNT, got %p", count_demoter.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : midstream_guard_shortfall_test

    // A status comparator's window covers the next stable point only: of
    // two mismatched stable points after it opens, the first is a warning
    // and the second an error.
    class status_cmp_midstream_test extends lb_status_cmp_base;
        `uvm_component_utils(status_cmp_midstream_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 1;
            want_text.push_back("uvm_test_top.cmp: pair 2: DUT");
        endfunction

        virtual task run_phase(uvm_phase phase);
            int unsigned warned;
            phase.raise_objection(this);
            dut('h1);
            model('h2);
            cmp.open_midstream_window();
            cmp.stable_point();
            cmp.stable_point();
            warned = uvm_report_server::get_server().get_id_count("A2C_MODEL_CMP_MIDSTREAM");
            if (warned != 1) `uvm_error("LB_MODE_B", $sformatf("expected one A2C_MODEL_CMP_MIDSTREAM warning, got %0d", warned))
            phase.drop_objection(this);
        endtask
    endclass : status_cmp_midstream_test
