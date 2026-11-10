// Loopback tests of a2c_rt_checker and the monitors' a2c_flow_counts, on
// the lb_rt_pipe stand-in DUT between rv_in and rv_out, axis_in and
// axis_out, and their model twins, and on the pa pin set with no DUT.
// Included in a2c_uvm_loopback_pkg after a2c_gen_base_test_lb_tests.svh,
// whose lb_gen_base the knob tests extend. Clock periods: clk 10ns, rising
// 5ns after each falling edge, where the monitors sample; clk2 30ns.

    // The axis pipe's payload, every field of a beat.
    typedef struct packed {
        lb_tdata_t  tdata;
        logic [3:0] tstrb;
        logic [3:0] tkeep;
        logic       tlast;
        lb_tid_t    tid;
        lb_tdest_t  tdest;
        lb_tuser_t  tuser;
    } lb_axis_beat_t;

    typedef a2c_rt_checker #(rv_item_t, rv_item_t)     lb_rv_rt_t;
    typedef a2c_rt_checker #(axis_item_t, axis_item_t) lb_axis_rt_t;
    typedef axi4_stream_tlast_rule #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) lb_axis_tlast_rule_t;

    // A user's unit rule on a struct payload: tag bit 3 ends a unit, as an
    // end-of-frame flag does.
    class lb_rv_eof_rule extends a2c_unit_rule #(rv_item_t);
        `uvm_object_utils(lb_rv_eof_rule)

        function new(string name = "lb_rv_eof_rule");
            super.new(name);
        endfunction

        virtual function bit is_unit_end(rv_item_t t);
            return t.data.tag[3];
        endfunction
    endclass : lb_rv_eof_rule

    // Keeps every report whose id starts with A2C_RT, or is one of also[],
    // with its time and severity, and demotes those errors to infos.
    class lb_rt_demoter extends uvm_report_catcher;
        string       also[$];
        string       ids[$];
        string       msgs[$];
        realtime     at[$];
        uvm_severity sevs[$];

        `uvm_object_utils(lb_rt_demoter)

        function new(string name = "lb_rt_demoter");
            super.new(name);
        endfunction

        protected function bit watched(string id);
            if (id.len() >= 6 && id.substr(0, 5) == "A2C_RT" && id != "A2C_RUN_TIMEOUT") return 1;
            foreach (also[i]) if (also[i] == id) return 1;
            return 0;
        endfunction

        virtual function action_e catch();
            if (!watched(get_id())) return THROW;
            ids.push_back(get_id());
            msgs.push_back(get_message());
            at.push_back($realtime);
            sevs.push_back(get_severity());
            if (get_severity() == UVM_ERROR) begin
                set_severity(UVM_INFO);
                set_action(UVM_DISPLAY);
                set_message({"expected, demoted to info: ", get_message()});
            end
            return THROW;
        endfunction

        // The reports of id at severity whose text holds sub.
        function int unsigned count(string id, uvm_severity sev = UVM_ERROR, string sub = "");
            int unsigned n = 0;
            foreach (ids[i]) n += ids[i] == id && sevs[i] == sev && (sub == "" || a2c_contains(msgs[i], sub));
            return n;
        endfunction

        // The time of the first such report, or -1.
        function realtime first_at(string id, uvm_severity sev = UVM_ERROR);
            foreach (ids[i]) if (ids[i] == id && sevs[i] == sev) return at[i];
            return -1;
        endfunction

        function int unsigned errors();
            int unsigned n = 0;
            foreach (sevs[i]) n += sevs[i] == UVM_ERROR;
            return n;
        endfunction
    endclass : lb_rt_demoter

    // Sends units of beats on an rdy_vld port. Tag bit 3 marks a unit's
    // last beat. Each beat waits 0 to max_gap clocks; the first of each line
    // after the first, h_blank more; the first of each unit after the
    // first, v_blank more; and gap_at gets gap_len more.
    class lb_rt_rv_seq extends uvm_sequence #(rv_item_t);
        int unsigned units = 1;
        int unsigned beats = 64;
        int unsigned line;
        int unsigned h_blank;
        int unsigned v_blank;
        int unsigned max_gap;
        int          gap_at = -1;
        int unsigned gap_len;

        `uvm_object_utils(lb_rt_rv_seq)

        function new(string name = "lb_rt_rv_seq");
            super.new(name);
        endfunction

        virtual task body();
            for (int unsigned u = 0; u < units; u++) begin
                for (int unsigned b = 0; b < beats; b++) begin
                    rv_item_t it = rv_item_t::type_id::create("it");
                    start_item(it);
                    if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
                    it.data.tag = (b == beats - 1) ? 4'h8 : 4'h0;
                    it.gap      = $urandom_range(max_gap, 0);
                    if (line != 0 && b != 0 && b % line == 0) it.gap += h_blank;
                    if (u != 0 && b == 0) it.gap += v_blank;
                    if (gap_at >= 0 && u * beats + b == gap_at) it.gap += gap_len;
                    finish_item(it);
                end
            end
        endtask
    endclass : lb_rt_rv_seq

    // What every rv checker test shares. A src agent on rv_in drives the
    // pipe u_rt_rv, a dst agent on rv_out takes its output, and rt judges
    // it; with mode_b set each agent's model lane is the u_rt_rv_model pipe.
    // configure() sets the pipe, the sequence and the checker; check()
    // checks what the test is about. The run ends drain clocks after
    // rv_out has delivered out_beats(), or at max_clocks. report_phase
    // passes only on exactly want[id] errors of each watched id, and none
    // of any other.
    class lb_rt_rv_base extends lb_base_test;
        rv_agent_t              src;
        rv_agent_t              dst;
        rv_config_t             src_cfg;
        rv_config_t             dst_cfg;
        lb_rv_rt_t              rt;
        lb_rt_demoter           demoter;
        lb_rt_rv_seq            seq;
        lb_arrivals#(rv_item_t) in_seen;
        lb_arrivals#(rv_item_t) out_seen;
        bit                     mode_b;
        int unsigned            want[string];
        int unsigned            drain = 100;
        int unsigned            max_clocks = 20000;
        int unsigned            clocks;

        `uvm_component_utils(lb_rt_rv_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
        endfunction

        virtual function void check();
        endfunction

        virtual function int unsigned out_beats();
            int unsigned n = seq.units * seq.beats;
            int unsigned limit = lb_rt_pipe_cfg[LB_RT_RV].pass_limit;
            return (limit != 0 && limit < n) ? limit : n;
        endfunction

        protected function rv_config_t lane_cfg(string name, string pins, a2c_role_e role);
            rv_config_t cfg = rv_config_t::type_id::create(name);
            if (!uvm_config_db#(rv_vif_t)::get(this, "", pins, cfg.vif)) `uvm_fatal("LB_CFG", {"no interface ", pins})
            if (mode_b && !uvm_config_db#(rv_vif_t)::get(this, "", {pins, "_model"}, cfg.model_vif)) `uvm_fatal("LB_CFG", {"no interface ", pins, "_model"})
            cfg.clk_vif   = clk_vif;
            cfg.role      = role;
            cfg.port_name = pins;
            return cfg;
        endfunction

        // The checker's subclass, for a test that overrides anchor().
        virtual function lb_rv_rt_t new_checker();
            return lb_rv_rt_t::type_id::create("rt", this);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            demoter = lb_rt_demoter::type_id::create("demoter");
            uvm_report_cb::add(null, demoter);
            seq = lb_rt_rv_seq::type_id::create("seq");
            if (mode_b) uvm_config_db#(bit)::set(this, "rt", "a2c_dual_dut", 1'b1);
            src_cfg = lane_cfg("src_cfg", "rv_in", A2C_SRC);
            dst_cfg = lane_cfg("dst_cfg", "rv_out", A2C_DST);
            rt      = new_checker();
            configure();
            uvm_config_db#(rv_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(rv_config_t)::set(this, "dst", "cfg", dst_cfg);
            src      = rv_agent_t::type_id::create("src", this);
            dst      = rv_agent_t::type_id::create("dst", this);
            in_seen  = lb_arrivals#(rv_item_t)::type_id::create("in_seen", this);
            out_seen = lb_arrivals#(rv_item_t)::type_id::create("out_seen", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            src.mon.ap.connect(in_seen.analysis_export);
            dst.mon.ap.connect(out_seen.analysis_export);
            rt.connect_in(src.mon);
            rt.connect_out(dst.mon, null, dst.model_cmp);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    clocks++;
                end
            join_none
            fork
                seq.start(src.sqr);
            join_none
            while (out_seen.items.size() < out_beats() && clocks < max_clocks) clk_vif.sample_edge();
            repeat (drain) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        // The rising edge a monitor's report at time t samples for.
        protected function realtime edge_of(realtime t);
            return t + 5ns;
        endfunction

        protected function void expect_at(string id, realtime t);
            realtime got = demoter.first_at(id);
            if (got != t) `uvm_error("LB_RT", $sformatf("the first %s came at %0t, expected %0t", id, got, t))
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            check();
        endfunction

        virtual function void report_phase(uvm_phase phase);
            int unsigned listed = 0;
            foreach (want[id]) begin
                listed += want[id];
                if (demoter.count(id) != want[id]) begin
                    `uvm_error("LB_RT", $sformatf("expected %0d %s errors, got %0d: %p", want[id], id, demoter.count(id), demoter.msgs))
                end
            end
            if (demoter.errors() != listed) `uvm_error("LB_RT", $sformatf("expected %0d demoted errors in all, got %0d: %p", listed, demoter.errors(), demoter.msgs))
            `uvm_info("LB_STATS", $sformatf("%0d beats in, %0d out, %0d clocks; worst lag %0d, gap %0d, refusal %0d; %0d units checked",
                                            in_seen.items.size(), out_seen.items.size(), clocks, rt.worst_lag(), rt.worst_gap(),
                                            rt.worst_refusal(), rt.units_checked()), UVM_NONE)
            super.report_phase(phase);
        endfunction
    endclass : lb_rt_rv_base

    // A good pipe of depth 8 under random sink ready and random input gaps,
    // with all three rules on. The sink's ready-low clocks never count: not
    // as gap, not against the lag, and the refusals of a full pipe on the
    // clocks the sink stalls the output are excluded.
    class rt_rv_good_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_good_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].depth = 8;
            dst_cfg.ready_pct = 60;
            seq.units   = 4;
            seq.beats   = 64;
            seq.max_gap = 2;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            // The pipe holds 8 beats and adds 5 clocks.
            rt.lag_cycles     = 4 + 1 + 8 + 4;
            rt.latency_cycles = 6;
            rt.gap_cycles     = 4;
            rt.refusal_cycles = 64;
        endfunction

        virtual function void check();
            if (rt.units_checked() != 4) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 4", rt.units_checked()))
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected the pipe's 5", rt.worst_lag()))
        endfunction
    endclass : rt_rv_good_test

    class rt_rv_burst_test extends rt_rv_good_test;
        `uvm_component_utils(rt_rv_burst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            super.configure();
            dst_cfg.burst     = 1;
            dst_cfg.burst_max = 12;
        endfunction
    endclass : rt_rv_burst_test

    // Units of four lines with horizontal and vertical blanking and random
    // gaps, the sink always ready. The credit window covers the pipe's 5
    // clocks, so the idle the blanking causes at the output is credited and
    // a gap bound of 3 holds.
    class rt_rv_blank_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_blank_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            seq.units   = 3;
            seq.beats   = 64;
            seq.line    = 16;
            seq.h_blank = 20;
            seq.v_blank = 60;
            seq.max_gap = 1;
            rt.in_rule        = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule       = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles     = 6;
            rt.latency_cycles = 7;
            rt.gap_cycles     = 3;
            rt.refusal_cycles = 1;
        endfunction

        virtual function void check();
            if (rt.units_checked() != 3) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 3", rt.units_checked()))
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected the pipe's 5", rt.worst_lag()))
        endfunction
    endclass : rt_rv_blank_test

    // The blanking of rt_rv_blank_test with a credit window of 1 clock,
    // shorter than the pipe's 5: the output's idle after the first H blank
    // of each unit outlasts the input's within the window, so the gap
    // reaches 3 once per unit. The first comes 24 clocks after beat 15
    // entered: its last 4 idle clocks lie past the window.
    class rt_rv_blank_no_credit_test extends rt_rv_blank_test;
        `uvm_component_utils(rt_rv_blank_no_credit_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            super.configure();
            seq.max_gap       = 0;
            rt.latency_cycles = 1;
            want["A2C_RT_GAP"] = 3;
        endfunction

        virtual function void check();
            expect_at("A2C_RT_GAP", edge_of(in_seen.at[15]) + 24 * 10ns);
        endfunction
    endclass : rt_rv_blank_no_credit_test

    // A pipe 1% too slow, 99 beats per 100 clocks, on one unit of 400 beats
    // the source sends back to back. Its lag reaches the bound of 6 one clock
    // after the pipe's own 5, before the unit ends, so one A2C_RT_DEADLINE
    // comes then, and the unit's late end adds an info.
    class rt_rv_slow_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_slow_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].emit_n = 99;
            lb_rt_pipe_cfg[LB_RT_RV].emit_m = 100;
            seq.beats   = 400;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles = 6;
            want["A2C_RT_DEADLINE"] = 1;
        endfunction

        virtual function void check();
            expect_at("A2C_RT_DEADLINE", edge_of(in_seen.at[399]) + 6 * 10ns);
            if (demoter.count("A2C_RT_DEADLINE", UVM_INFO, "reported late, ended") != 1) begin
                `uvm_error("LB_RT", "no info of the late unit's end")
            end
            if (rt.worst_lag() <= 6) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected above 6", rt.worst_lag()))
        endfunction
    endclass : rt_rv_slow_test

    // One stall of 40 clocks after the pipe's 100th beat, the input back to
    // back: the gap reaches its bound of 30 thirty clocks after the 100th
    // beat, with no credit.
    class rt_rv_stall_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_stall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 100;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = 40;
            seq.beats   = 400;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.gap_cycles = 30;
            want["A2C_RT_GAP"] = 1;
        endfunction

        virtual function void check();
            expect_at("A2C_RT_GAP", edge_of(out_seen.at[99]) + 30 * 10ns);
            if (rt.worst_gap() != 40) `uvm_error("LB_RT", $sformatf("worst gap %0d, expected the stall's 40", rt.worst_gap()))
        endfunction
    endclass : rt_rv_stall_test

    // The pipe refuses one clock in ten of a 200-beat unit the source sends
    // back to back: the refusal reaches its bound of 15 on the clock of the
    // 15th refused offer.
    class rt_rv_refusal_test extends lb_rt_rv_base;
        realtime refused_at[$];

        `uvm_component_utils(rt_rv_refusal_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].refuse_every = 10;
            seq.beats   = 200;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.refusal_cycles = 15;
            want["A2C_RT_REFUSAL"] = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (src_cfg.vif.vld === 1'b1 && src_cfg.vif.rdy !== 1'b1) refused_at.push_back(edge_of($realtime));
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            if (refused_at.size() < 15) `uvm_error("LB_RT", $sformatf("only %0d refused clocks", refused_at.size()))
            else expect_at("A2C_RT_REFUSAL", refused_at[14]);
        endfunction
    endclass : rt_rv_refusal_test

    // A pipe of depth 4 behind a sink that holds ready low in long runs:
    // the pipe refuses input while it is full, nearly always on clocks the
    // sink stalls the output, which do not count. Only the clocks after a
    // stall ends, before the pipe has room again, count, far below the
    // refused clocks on the pins.
    class rt_rv_refusal_excluded_test extends lb_rt_rv_base;
        int unsigned refused;

        `uvm_component_utils(rt_rv_refusal_excluded_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].depth = 4;
            dst_cfg.ready_pct = 25;
            dst_cfg.burst     = 1;
            dst_cfg.burst_max = 20;
            seq.beats   = 128;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.refusal_cycles = 100;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                forever begin
                    clk_vif.sample_edge();
                    refused += src_cfg.vif.vld === 1'b1 && src_cfg.vif.rdy !== 1'b1;
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            if (refused < 200) `uvm_error("LB_RT", $sformatf("only %0d refused clocks on the pins, so the exclusion went untested", refused))
            if (rt.worst_refusal() * 2 > refused) begin
                `uvm_error("LB_RT", $sformatf("the checker counted %0d of the %0d refused clocks", rt.worst_refusal(), refused))
            end
        endfunction
    endclass : rt_rv_refusal_excluded_test

    // One unit of 32 beats through the pipe's 5 clocks, sink always ready:
    // its lag is exactly 5. A bound of 5, the first failing value, fails it
    // on the clock the unit ends, which gives the error and then the info.
    class rt_rv_lag_at_bound_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_lag_at_bound_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            seq.beats   = 32;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles = 5;
            want["A2C_RT_DEADLINE"] = 1;
        endfunction

        virtual function void check();
            expect_at("A2C_RT_DEADLINE", edge_of(in_seen.at[31]) + 5 * 10ns);
            if (demoter.count("A2C_RT_DEADLINE", UVM_INFO, "ended 0 clocks after its deadline") != 1) begin
                `uvm_error("LB_RT", "no info of the unit ending on its deadline")
            end
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected 5", rt.worst_lag()))
        endfunction
    endclass : rt_rv_lag_at_bound_test

    // The same with a bound of 6, one above the lag: no report.
    class rt_rv_lag_below_bound_test extends rt_rv_lag_at_bound_test;
        `uvm_component_utils(rt_rv_lag_below_bound_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            super.configure();
            rt.lag_cycles = 6;
            want.delete("A2C_RT_DEADLINE");
        endfunction

        virtual function void check();
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected 5", rt.worst_lag()))
            if (rt.units_checked() != 1) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 1", rt.units_checked()))
        endfunction
    endclass : rt_rv_lag_below_bound_test

    // Output units of 8 beats against input units of 16, paired 1:1, and
    // only 8 beats sent: output unit 0 ends while input unit 0 is open.
    class rt_rv_unit_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_unit_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            a2c_beat_count_rule#(rv_item_t) in_rule  = a2c_beat_count_rule#(rv_item_t)::type_id::create("in_rule");
            a2c_beat_count_rule#(rv_item_t) out_rule = a2c_beat_count_rule#(rv_item_t)::type_id::create("out_rule");
            in_rule.beats_per_unit  = 16;
            out_rule.beats_per_unit = 8;
            rt.in_rule  = in_rule;
            rt.out_rule = out_rule;
            seq.beats   = 8;
            rt.lag_cycles = 100;
            want["A2C_RT_UNIT"] = 1;
        endfunction

        virtual function void check();
            expect_at("A2C_RT_UNIT", edge_of(out_seen.at[7]));
        endfunction
    endclass : rt_rv_unit_test

    // Wiring a rule cannot run on is an A2C_CFG error each: the lag and
    // refusal rules with no input and no in_rule, the gap rule with no
    // out_rule and no counter, and a second checker with no output.
    class rt_rv_cfg_test extends lb_rt_rv_base;
        lb_rv_rt_t unwired;

        `uvm_component_utils(rt_rv_cfg_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            seq.units = 1;
            seq.beats = 8;
            rt.lag_cycles     = 5;
            rt.refusal_cycles = 5;
            rt.gap_cycles     = 5;
            unwired = lb_rv_rt_t::type_id::create("unwired", this);
            begin
                a2c_beat_count_rule#(rv_item_t) zero_in  = a2c_beat_count_rule#(rv_item_t)::type_id::create("in_rule");
                lb_rv_eof_rule                  zero_out = lb_rv_eof_rule::type_id::create("out_rule");
                zero_in.beats_per_unit = 0;
                zero_out.ends_per_unit = 0;
                unwired.in_rule  = zero_in;
                unwired.out_rule = zero_out;
            end
            demoter.also.push_back("A2C_CFG");
            want["A2C_CFG"] = 6;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            src.mon.ap.connect(in_seen.analysis_export);
            dst.mon.ap.connect(out_seen.analysis_export);
            rt.connect_out(dst.mon);
        endfunction

        virtual function void check();
            string texts[] = '{"rt_lag_cycles 5 needs an input from connect_in() and both in_rule and out_rule; missing: the input in_rule out_rule",
                               "rt_refusal_cycles 5 needs an input from connect_in() and an in_rule; missing: the input in_rule",
                               "rt_gap_cycles 5 needs an out_rule, or the output's a2c_txn_counter passed to connect_out()",
                               "unwired: no output connected",
                               "unwired: in_rule ",
                               "unwired: out_rule "};
            foreach (texts[i]) begin
                if (demoter.count("A2C_CFG", UVM_ERROR, texts[i]) != 1) `uvm_error("LB_RT", $sformatf("no A2C_CFG reading '%s': %p", texts[i], demoter.msgs))
            end
        endfunction
    endclass : rt_rv_cfg_test

    // The sink holds ready low over each unit's first offered beat, then in
    // the middle of the next unit, both times before the unit's input ends.
    // Every ready-low clock from the unit's first offered beat delays its
    // end by one clock and is credited, so both units' lag stays the pipe's
    // 5 and the bound of 6 holds.
    class rt_rv_sink_hold_test extends lb_rt_rv_base;
        realtime held_until[2];

        `uvm_component_utils(rt_rv_sink_hold_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            dst_cfg.ready_pct = 0;
            seq.units   = 2;
            seq.beats   = 64;
            seq.v_blank = 60;
            rt.in_rule    = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule   = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles = 6;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    do clk_vif.sample_edge(); while (dst_cfg.vif.vld !== 1'b1);
                    repeat (20) clk_vif.sample_edge();
                    dst_cfg.ready_pct = 100;
                    held_until[0] = $realtime;
                    while (out_seen.items.size() < seq.beats + 8) clk_vif.sample_edge();
                    dst_cfg.ready_pct = 0;
                    repeat (30) clk_vif.sample_edge();
                    dst_cfg.ready_pct = 100;
                    held_until[1] = $realtime;
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            if (rt.units_checked() != 2) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 2", rt.units_checked()))
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected the pipe's 5", rt.worst_lag()))
            for (int u = 0; u < 2; u++) begin
                if (held_until[u] == 0 || held_until[u] >= in_seen.at[(u + 1) * seq.beats - 1]) begin
                    `uvm_error("LB_RT", $sformatf("unit %0d's hold ended at %0t, not before its input ended", u, held_until[u]))
                end
            end
        endfunction
    endclass : rt_rv_sink_hold_test

    // An output one unit behind its input: anchor(j) is input unit j + 1.
    class lb_rv_behind_rt extends lb_rv_rt_t;
        `uvm_component_utils(lb_rv_behind_rt)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function int unsigned anchor(int unsigned j);
            return j + 1;
        endfunction
    endclass : lb_rv_behind_rt

    // One unit sent back to back; the sink holds ready low for hold clocks
    // from the pipe's 9th output beat. A pipe of the given depth absorbs
    // what it can hold and refuses the rest, which moves the input end later
    // by the refused clocks, so the deadline credit is the hold less those
    // refusals and the lag reads the pipe's 5 whatever the depth. A subclass
    // adds holds, each from an output beat count, and an input gap.
    class rt_rv_stall_buffer_test extends lb_rt_rv_base;
        int unsigned depth;
        int unsigned hold = 30;
        int unsigned hold_from[$] = '{8};
        int unsigned hold_len[$];
        // The refused clocks of the unit the test wants: at least, at most.
        int unsigned refused_min;
        int unsigned refused_max;
        int unsigned refused;
        realtime     hold_end;

        `uvm_component_utils(rt_rv_stall_buffer_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].depth = depth;
            seq.beats  = 64;
            rt.in_rule    = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule   = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles = 6;
            if (hold_len.size() == 0) hold_len.push_back(hold);
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (src_cfg.vif.vld === 1'b1 && src_cfg.vif.rdy !== 1'b1) refused++;
                end
                foreach (hold_from[h]) begin
                    while (out_seen.items.size() < hold_from[h]) clk_vif.sample_edge();
                    dst_cfg.ready_pct = 0;
                    repeat (hold_len[h]) clk_vif.sample_edge();
                    dst_cfg.ready_pct = 100;
                    hold_end = $realtime;
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            if (rt.units_checked() != 1) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 1", rt.units_checked()))
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected the pipe's 5 (%0d refused)", rt.worst_lag(), refused))
            check_refused();
        endfunction

        protected function void check_refused();
            if (refused < refused_min || refused > refused_max) begin
                `uvm_error("LB_RT", $sformatf("%0d clocks refused, expected %0d to %0d", refused, refused_min, refused_max))
            end
            if (hold_end == 0 || hold_end >= in_seen.at[seq.beats - 1]) `uvm_error("LB_RT", "the last hold did not end before the input end")
        endfunction
    endclass : rt_rv_stall_buffer_test

    // A buffer of 8 beats: the stall turns into refusals.
    class rt_rv_stall_small_buffer_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_stall_small_buffer_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            depth       = 8;
            refused_min = hold - 8;
            refused_max = hold;
        endfunction
    endclass : rt_rv_stall_small_buffer_test

    // An unbounded buffer absorbs the stall: nothing is refused.
    class rt_rv_stall_large_buffer_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_stall_large_buffer_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            refused_max = 0;
        endfunction
    endclass : rt_rv_stall_large_buffer_test

    // A buffer of 24 beats absorbs part of the stall and refuses the rest.
    class rt_rv_stall_partial_buffer_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_stall_partial_buffer_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            depth       = 24;
            refused_min = 1;
            refused_max = hold - 8 - 1;
        endfunction
    endclass : rt_rv_stall_partial_buffer_test

    // An unbounded buffer that refuses one clock in three for its own
    // reasons, through the stall too. Those refusals are subtracted from
    // the stall's credit though the stall did not cause them, so the lag
    // reads at most the smaller of the hold and the refusals above the
    // pipe's 5, and never below it.
    class rt_rv_stall_own_refusal_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_stall_own_refusal_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            refused_min = 1;
            refused_max = 64;
        endfunction

        virtual function void configure();
            super.configure();
            lb_rt_pipe_cfg[LB_RT_RV].refuse_every = 3;
            rt.lag_cycles = 6 + hold;
        endfunction

        virtual function void check();
            int unsigned most = 5 + ((hold < refused) ? hold : refused);
            if (rt.units_checked() != 1) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 1", rt.units_checked()))
            if (rt.worst_lag() < 5 || rt.worst_lag() > most) begin
                `uvm_error("LB_RT", $sformatf("worst lag %0d, expected 5 to %0d (%0d refused)", rt.worst_lag(), most, refused))
            end
            check_refused();
        endfunction
    endclass : rt_rv_stall_own_refusal_test

    // The input pauses 60 clocks after beat 32 and the pipe empties. The
    // sink holds ready low from the 32nd output beat until after the input
    // resumes: the clocks with nothing offered are no stall and earn no
    // credit, and the stall once the pipe offers again is credited, so the
    // lag reads the pipe's 5.
    class rt_rv_stall_unoffered_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_stall_unoffered_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold_from   = '{32};
            hold_len    = '{70};
            refused_max = 0;
        endfunction

        virtual function void configure();
            super.configure();
            seq.gap_at  = 32;
            seq.gap_len = 60;
        endfunction
    endclass : rt_rv_stall_unoffered_test

    // A buffer of 8 beats: the first hold turns into refusals, then the
    // pipe catches up in a 60-clock input gap after beat 40 and sits idle
    // with its sink ready, which restarts the stall and refusal counts. The
    // first hold, made up during the gap, is not credited, nor are its
    // refusals subtracted from the short second hold after the gap, so the
    // lag reads the pipe's 5.
    class rt_rv_stall_caught_up_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_stall_caught_up_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            depth       = 8;
            hold_from   = '{8, 48};
            hold_len    = '{30, 2};
            refused_min = 30 - 8;
            refused_max = 30 + 2;
        endfunction

        virtual function void configure();
            super.configure();
            seq.gap_at  = 40;
            seq.gap_len = 60;
        endfunction
    endclass : rt_rv_stall_caught_up_test

    // An unbounded buffer holding a backlog from a 20-clock sink hold stops
    // emitting for 10 clocks of its own with the sink ready. That bubble
    // restarts the counts, so the hold before it loses its credit: the lag
    // reads the hold above the true 15, never below it, and fails a bound
    // of 20 with a message that names the restart.
    class rt_rv_stall_bubble_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_stall_bubble_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold_len    = '{20};
            refused_max = 0;
        endfunction

        virtual function void configure();
            super.configure();
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 40;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = 10;
            rt.lag_cycles = 20;
            want["A2C_RT_DEADLINE"] = 1;
        endfunction

        virtual function void check();
            if (rt.worst_lag() < 15) `uvm_error("LB_RT", $sformatf("worst lag %0d, below the true 15", rt.worst_lag()))
            if (demoter.count("A2C_RT_DEADLINE", UVM_ERROR, "less a stall credit of 0 clocks") != 1
                || demoter.count("A2C_RT_DEADLINE", UVM_ERROR, "with its sink ready at never") != 0) begin
                `uvm_error("LB_RT", $sformatf("no deadline naming the restart: %p", demoter.msgs))
            end
            check_refused();
        endfunction
    endclass : rt_rv_stall_bubble_test

    // Two units through a buffer of 8 beats; the sink holds ready low over
    // the last beats of output unit 0 while the input is already in unit 1,
    // so the full pipe refuses unit 1's input before output unit 1 offers
    // its first beat. Those refusals outnumber unit 1's stalls, which are
    // none, so its credit stays at 0 and its lag reads its span from input
    // end to output end; the backlog never lets the output idle, so nothing
    // restarts the counts.
    class rt_rv_refused_next_unit_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_refused_next_unit_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            depth     = 8;
            hold_from = '{60};
            hold_len  = '{30};
        endfunction

        virtual function void configure();
            super.configure();
            seq.units     = 2;
            rt.lag_cycles = 0;
        endfunction

        virtual function void check();
            int unsigned last = 2 * seq.beats - 1;
            int unsigned span = (out_seen.at[last] - in_seen.at[last]) / 10ns;
            if (rt.units_checked() != 2) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 2", rt.units_checked()))
            if (span <= 5) `uvm_error("LB_RT", $sformatf("unit 1 spans %0d clocks, so its lag cannot tell a credit from none", span))
            if (rt.worst_lag() != span) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected unit 1's span of %0d with no credit", rt.worst_lag(), span))
            if (refused < 30 - 8) `uvm_error("LB_RT", $sformatf("only %0d clocks refused", refused))
        endfunction
    endclass : rt_rv_refused_next_unit_test

    // One output unit of 64 beats over four input units of 16, through a
    // buffer of 8 beats; the sink holds ready low for 20 clocks from the
    // 9th output beat, during input unit 1, and the full pipe refuses that
    // input. The output started before its anchor, input unit 3, so the
    // refusals count from its first offered beat, net its stalls, and the
    // lag reads the pipe's 5.
    class rt_rv_stall_ratio_test extends rt_rv_stall_buffer_test;
        `uvm_component_utils(rt_rv_stall_ratio_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            depth    = 8;
            hold_len = '{20};
        endfunction

        virtual function void configure();
            a2c_beat_count_rule#(rv_item_t) out_rule;
            super.configure();
            out_rule = a2c_beat_count_rule#(rv_item_t)::type_id::create("out_rule");
            out_rule.beats_per_unit = 64;
            rt.out_rule         = out_rule;
            rt.in_units_per_out = 4;
            seq.units = 4;
            seq.beats = 16;
        endfunction

        virtual function void check();
            if (rt.units_checked() != 1) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 1", rt.units_checked()))
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected the pipe's 5 (%0d refused)", rt.worst_lag(), refused))
            if (refused < 20 - 8) `uvm_error("LB_RT", $sformatf("only %0d clocks refused", refused))
        endfunction
    endclass : rt_rv_stall_ratio_test

    // As rt_rv_stall_ratio_test with one output unit of 64 beats over two
    // input units of 32 and anchor(j) = j + 1: the stall and its refusals
    // fall in input unit 0, before the anchor.
    class rt_rv_stall_anchor_test extends rt_rv_stall_ratio_test;
        `uvm_component_utils(rt_rv_stall_anchor_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_rv_rt_t new_checker();
            return lb_rv_behind_rt::type_id::create("rt", this);
        endfunction

        virtual function void configure();
            super.configure();
            rt.in_units_per_out = 1;
            seq.units = 2;
            seq.beats = 32;
        endfunction
    endclass : rt_rv_stall_anchor_test

    // The DUT stalls for 40 clocks while the sink holds ready low over the
    // stall: the gap counts only clocks the sink was ready, so none fails.
    class rt_rv_unready_stall_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_unready_stall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 20;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = 40;
            seq.beats   = 100;
            rt.in_rule    = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule   = lb_rv_eof_rule::type_id::create("out_rule");
            rt.gap_cycles = 10;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    while (out_seen.items.size() < 20) clk_vif.sample_edge();
                    dst_cfg.ready_pct = 0;
                    repeat (50) clk_vif.sample_edge();
                    dst_cfg.ready_pct = 100;
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            if (rt.worst_gap() >= 5) `uvm_error("LB_RT", $sformatf("worst gap %0d with the sink not ready over the stall", rt.worst_gap()))
        endfunction
    endclass : rt_rv_unready_stall_test

    // The pipe refuses every other input clock while its output is still
    // empty and the sink is not ready. With no beat offered on the output
    // the sink stalls nothing, so every refused clock counts.
    class rt_rv_refusal_unready_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_refusal_unready_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].latency      = 40;
            lb_rt_pipe_cfg[LB_RT_RV].refuse_every = 2;
            dst_cfg.ready_pct = 0;
            seq.beats = 16;
            rt.in_rule        = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule       = lb_rv_eof_rule::type_id::create("out_rule");
            rt.refusal_cycles = 5;
            want["A2C_RT_REFUSAL"] = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    repeat (60) clk_vif.sample_edge();
                    dst_cfg.ready_pct = 100;
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            if (out_seen.at[0] <= in_seen.at[seq.beats - 1]) `uvm_error("LB_RT", "the output started before the input ended, so the refusals were not all on an empty output")
        endfunction
    endclass : rt_rv_refusal_unready_test

    // A lag bound lowered by set_limits() before the last unit's input
    // ends applies to that unit only. Output runs at a quarter rate, so its
    // deadline passes while the earlier units, under the old bound, are
    // still due.
    class rt_rv_set_limits_test extends lb_rt_rv_base;
        // The unit the lower bound applies to; the units before it are all
        // still due at its deadline.
        int unsigned lowered = 1;

        `uvm_component_utils(rt_rv_set_limits_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].emit_n = 1;
            lb_rt_pipe_cfg[LB_RT_RV].emit_m = 4;
            seq.units = lowered + 1;
            seq.beats = 16;
            rt.in_rule    = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule   = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles = 1000;
            want["A2C_RT_DEADLINE"] = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    while (in_seen.items.size() <= lowered * seq.beats) clk_vif.sample_edge();
                    rt.set_limits(-1, 10, -1);
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            expect_at("A2C_RT_DEADLINE", edge_of(in_seen.at[(lowered + 1) * seq.beats - 1]) + 10 * 10ns);
            if (out_seen.at[lowered * seq.beats - 1] <= demoter.first_at("A2C_RT_DEADLINE")) begin
                `uvm_error("LB_RT", "a unit before the lowered one ended before its deadline, so the search past pending units went untested")
            end
            if (demoter.count("A2C_RT_DEADLINE", UVM_INFO, $sformatf("output unit %0d, reported late", lowered)) != 1) begin
                `uvm_error("LB_RT", $sformatf("no late info for unit %0d: %p", lowered, demoter.msgs))
            end
        endfunction
    endclass : rt_rv_set_limits_test

    // As rt_rv_set_limits_test with two units pending under the old bound
    // ahead of the lowered one.
    class rt_rv_set_limits_third_test extends rt_rv_set_limits_test;
        `uvm_component_utils(rt_rv_set_limits_third_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            lowered = 2;
        endfunction
    endclass : rt_rv_set_limits_third_test

    // a2c_rt_off turns every rule off for the run: bounds set on the fields
    // before end_of_elaboration and through set_limits() during the run
    // stay 0, though the pipe stalls, refuses and lags past each of them.
    class rt_rv_off_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            uvm_config_db#(bit)::set(this, "rt", "a2c_rt_off", 1'b1);
            lb_rt_pipe_cfg[LB_RT_RV].refuse_every = 3;
            lb_rt_pipe_cfg[LB_RT_RV].stall_after  = 20;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len    = 20;
            seq.beats = 64;
            rt.in_rule        = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule       = lb_rv_eof_rule::type_id::create("out_rule");
            rt.gap_cycles     = 2;
            rt.lag_cycles     = 2;
            rt.refusal_cycles = 2;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    repeat (10) clk_vif.sample_edge();
                    rt.set_limits(2, 2, 2);
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            if (rt.gap_cycles != 0 || rt.lag_cycles != 0 || rt.refusal_cycles != 0) begin
                `uvm_error("LB_RT", $sformatf("bounds gap %0d, lag %0d, refusal %0d with a2c_rt_off set", rt.gap_cycles, rt.lag_cycles, rt.refusal_cycles))
            end
            if (rt.worst_gap() < 2 || rt.worst_lag() < 2 || rt.worst_refusal() < 2) begin
                `uvm_error("LB_RT", $sformatf("worst gap %0d, lag %0d, refusal %0d: the run would not have failed the bounds",
                                              rt.worst_gap(), rt.worst_lag(), rt.worst_refusal()))
            end
        endfunction
    endclass : rt_rv_off_test

    // As rt_rv_off_test with the bounds written to the fields during the
    // run: the rules measure and raise nothing.
    class rt_rv_off_runtime_test extends rt_rv_off_test;
        `uvm_component_utils(rt_rv_off_runtime_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    repeat (10) clk_vif.sample_edge();
                    rt.gap_cycles     = 2;
                    rt.lag_cycles     = 2;
                    rt.refusal_cycles = 2;
                end
            join_none
            lb_rt_rv_base::run_phase(phase);
        endtask

        virtual function void check();
            if (rt.worst_gap() < 2 || rt.worst_lag() < 2 || rt.worst_refusal() < 2) begin
                `uvm_error("LB_RT", $sformatf("worst gap %0d, lag %0d, refusal %0d: the run would not have failed the bounds",
                                              rt.worst_gap(), rt.worst_lag(), rt.worst_refusal()))
            end
        endfunction
    endclass : rt_rv_off_runtime_test

    // With the lag rule off, an output unit cut short by the pipe never
    // ends; the summary counts it as neither pending nor never completed.
    class rt_rv_lag_off_pending_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_lag_off_pending_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].pass_limit = 40;
            seq.beats = 64;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
        endfunction

        virtual function void check();
            if (demoter.count("A2C_RT", UVM_INFO, "0 never completed (see A2C_TXN_COUNT), 0 pending with the deadline not reached") != 1) begin
                `uvm_error("LB_RT", $sformatf("no summary with nothing pending: %p", demoter.msgs))
            end
        endfunction
    endclass : rt_rv_lag_off_pending_test

    // Gap only, from the output counter: the unit closes when the counter
    // has nothing pending, so the 200-clock blank between two declared
    // bursts is no gap. No input is connected, so there is no credit.
    class rt_rv_counter_units_test extends lb_rt_rv_base;
        a2c_txn_counter #(rv_item_t) counter;

        `uvm_component_utils(rt_rv_counter_units_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            seq.units     = 2;
            seq.beats     = 32;
            seq.v_blank   = 200;
            rt.gap_cycles = 50;
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv_out";
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(counter.analysis_export);
            src.mon.ap.connect(in_seen.analysis_export);
            dst.mon.ap.connect(out_seen.analysis_export);
            rt.connect_out(dst.mon, counter);
        endfunction

        virtual task run_phase(uvm_phase phase);
            counter.expect_count(seq.beats);
            fork
                begin
                    while (out_seen.items.size() < seq.beats) clk_vif.sample_edge();
                    repeat (10) clk_vif.sample_edge();
                    counter.expect_count(seq.beats);
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            if (out_seen.at[seq.beats] - out_seen.at[seq.beats - 1] < 150 * 10ns) `uvm_error("LB_RT", "the blank between the bursts was under 150 clocks")
        endfunction
    endclass : rt_rv_counter_units_test

    // As rt_rv_blank_test with rt_latency_cycles 0, which takes the lag
    // bound as the credit window.
    class rt_rv_blank_lag_window_test extends rt_rv_blank_test;
        `uvm_component_utils(rt_rv_blank_lag_window_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            super.configure();
            rt.latency_cycles = 0;
            rt.lag_cycles     = 7;
        endfunction
    endclass : rt_rv_blank_lag_window_test

    // The input runs on clk3, at half the output's rate, with no idle; the
    // DUT then stalls 40 clocks. An output clock on which the input monitor
    // took no sample says nothing about the input, so the stall gets no
    // credit and fails the gap bound of 30.
    class rt_rv_slow_input_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_slow_input_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            virtual a2c_clk_if clk3_vif;
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            lb_rt_rv_in_clk3 = 1;
            src_cfg.clk_vif  = clk3_vif;
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 20;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = 40;
            seq.beats = 64;
            rt.in_rule        = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule       = lb_rv_eof_rule::type_id::create("out_rule");
            rt.latency_cycles = 10;
            rt.gap_cycles     = 30;
            want["A2C_RT_GAP"] = 1;
        endfunction

        virtual function void check();
            if (rt.worst_gap() < 38) `uvm_error("LB_RT", $sformatf("worst gap %0d, expected about the stall's 40", rt.worst_gap()))
        endfunction
    endclass : rt_rv_slow_input_test

    // Output at half rate trails its input, and the DUT stalls 20 clocks
    // after the input unit has ended, inside the testbench's vertical blank.
    // The testbench can no longer starve a unit whose input has ended, so
    // the blank earns no credit and the stall fails the gap bound of 10.
    class rt_rv_after_input_stall_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_after_input_stall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].emit_n      = 1;
            lb_rt_pipe_cfg[LB_RT_RV].emit_m      = 2;
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 30;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = 20;
            seq.units   = 2;
            seq.beats   = 32;
            seq.v_blank = 100;
            rt.in_rule        = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule       = lb_rv_eof_rule::type_id::create("out_rule");
            rt.latency_cycles = 30;
            rt.gap_cycles     = 10;
            want["A2C_RT_GAP"] = 1;
        endfunction

        virtual function void check();
            if (out_seen.at[29] <= in_seen.at[seq.beats - 1]) `uvm_error("LB_RT", "the stall began before the input unit ended")
            if (out_seen.at[30] >= in_seen.at[seq.beats]) `uvm_error("LB_RT", "the stall ended after the next input unit began")
        endfunction
    endclass : rt_rv_after_input_stall_test

    // Mode B. The model pipe takes 20 clocks and refuses every second
    // clock, so the source, which starts a beat only once both lanes took
    // the last, withholds the DUT lane's input often. The DUT lane is
    // judged alone, and the lag, gap and refusal bounds of a pipe that is
    // only fed slowly hold.
    class rt_rv_mode_b_slow_model_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_mode_b_slow_model_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV_MODEL].latency      = 20;
            lb_rt_pipe_cfg[LB_RT_RV_MODEL].refuse_every = 2;
            seq.units   = 3;
            seq.beats   = 48;
            seq.max_gap = 1;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles     = 6;
            rt.latency_cycles = 6;
            rt.gap_cycles     = 2;
            rt.refusal_cycles = 1;
        endfunction

        virtual function void check();
            if (rt.units_checked() != 3) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 3", rt.units_checked()))
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected the DUT pipe's 5", rt.worst_lag()))
        endfunction
    endclass : rt_rv_mode_b_slow_model_test

    // Mode B with a fast model pipe and a DUT pipe 1% too slow: the DUT lane
    // is judged and fails its deadline, named as the DUT lane.
    class rt_rv_mode_b_slow_dut_test extends rt_rv_slow_test;
        `uvm_component_utils(rt_rv_mode_b_slow_dut_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction

        virtual function void configure();
            super.configure();
            lb_rt_pipe_cfg[LB_RT_RV_MODEL].latency = 1;
        endfunction

        virtual function void check();
            super.check();
            if (demoter.count("A2C_RT_DEADLINE", UVM_ERROR, "rv_out DUT lane: output unit 0") != 1) begin
                `uvm_error("LB_RT", $sformatf("the deadline error does not name the DUT lane: %p", demoter.msgs))
            end
        endfunction
    endclass : rt_rv_mode_b_slow_dut_test

    // The checker raises at most max_reported failures, here 2 of 5 units
    // late, and check_phase one more error for the other 3.
    class rt_rv_max_reported_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_max_reported_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].emit_n = 1;
            lb_rt_pipe_cfg[LB_RT_RV].emit_m = 2;
            seq.units   = 5;
            seq.beats   = 40;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles   = 20;
            rt.max_reported = 2;
            want["A2C_RT_DEADLINE"] = 2;
            want["A2C_RT"] = 1;
        endfunction

        virtual function void check();
            if (demoter.count("A2C_RT", UVM_ERROR, "5 real-time failures in all, 3 not printed") != 1) begin
                `uvm_error("LB_RT", $sformatf("no check_phase count of the unprinted failures: %p", demoter.msgs))
            end
        endfunction
    endclass : rt_rv_max_reported_test

    // On the model DUT the checker measures and raises nothing: the slow
    // pipe of rt_rv_max_reported_test fails 5 units unseen, which the
    // summary counts.
    class rt_rv_model_dut_test extends rt_rv_max_reported_test;
        `uvm_component_utils(rt_rv_model_dut_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_config_db#(bit)::set(this, "rt", "a2c_model_dut", 1'b1);
            super.build_phase(phase);
        endfunction

        virtual function void configure();
            super.configure();
            rt.max_reported = 10;
            want.delete("A2C_RT_DEADLINE");
            want.delete("A2C_RT");
        endfunction

        virtual function void check();
            if (demoter.count("A2C_RT", UVM_INFO, "the DUT is the SystemC model") != 1) `uvm_error("LB_RT", "no measure-only info")
            if (demoter.count("A2C_RT", UVM_INFO, "measured only, on the model DUT: 5 failures not raised") != 1) begin
                `uvm_error("LB_RT", $sformatf("the summary does not count the 5 failures: %p", demoter.msgs))
            end
        endfunction
    endclass : rt_rv_model_dut_test

    // With on_model set the checker judges the model DUT too.
    class rt_rv_on_model_test extends rt_rv_model_dut_test;
        `uvm_component_utils(rt_rv_on_model_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_config_db#(int unsigned)::set(this, "rt", "a2c_rt_on_model", 1);
            super.build_phase(phase);
        endfunction

        virtual function void configure();
            super.configure();
            want["A2C_RT_DEADLINE"] = 5;
        endfunction

        virtual function void check();
            if (demoter.count("A2C_RT", UVM_INFO, "the DUT is the SystemC model") != 0) `uvm_error("LB_RT", "a measure-only info with on_model set")
        endfunction
    endclass : rt_rv_on_model_test

    // No unit rule: the output's counter marks it active from the first
    // transfer after expect_count() until the count is in, so the gap rule
    // still finds the stall, and the idle before and after does not count.
    class rt_rv_counter_gap_test extends lb_rt_rv_base;
        a2c_txn_counter #(rv_item_t) counter;

        `uvm_component_utils(rt_rv_counter_gap_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 50;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = 40;
            seq.beats     = 200;
            rt.gap_cycles = 30;
            drain         = 300;
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv_out";
            want["A2C_RT_GAP"] = 1;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(counter.analysis_export);
            src.mon.ap.connect(in_seen.analysis_export);
            dst.mon.ap.connect(out_seen.analysis_export);
            rt.connect_in(src.mon);
            rt.connect_out(dst.mon, counter);
        endfunction

        virtual task run_phase(uvm_phase phase);
            counter.expect_count(200);
            super.run_phase(phase);
        endtask

        virtual function void check();
            expect_at("A2C_RT_GAP", edge_of(out_seen.at[49]) + 30 * 10ns);
        endfunction
    endclass : rt_rv_counter_gap_test

    // 4:1: output units of 16 beats against input units of 4, the output
    // anchored on the last input unit of its four.
    class rt_rv_ratio_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_ratio_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            a2c_beat_count_rule#(rv_item_t) in_rule  = a2c_beat_count_rule#(rv_item_t)::type_id::create("in_rule");
            a2c_beat_count_rule#(rv_item_t) out_rule = a2c_beat_count_rule#(rv_item_t)::type_id::create("out_rule");
            in_rule.beats_per_unit  = 4;
            out_rule.beats_per_unit = 16;
            rt.in_rule          = in_rule;
            rt.out_rule         = out_rule;
            rt.in_units_per_out = 4;
            seq.beats     = 64;
            rt.lag_cycles = 6;
        endfunction

        virtual function void check();
            if (rt.units_checked() != 4) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 4", rt.units_checked()))
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected 5", rt.worst_lag()))
        endfunction
    endclass : rt_rv_ratio_test

    // 1:2: two output units of 16 beats per input unit of 32, through a pipe
    // of 40 clocks, so both end after their input unit: the first 25 clocks
    // after it, the second 41.
    class rt_rv_split_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_split_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            a2c_beat_count_rule#(rv_item_t) out_rule = a2c_beat_count_rule#(rv_item_t)::type_id::create("out_rule");
            out_rule.beats_per_unit = 16;
            lb_rt_pipe_cfg[LB_RT_RV].latency = 40;
            rt.in_rule          = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule         = out_rule;
            rt.out_units_per_in = 2;
            seq.units     = 2;
            seq.beats     = 32;
            rt.lag_cycles = 42;
        endfunction

        virtual function void check();
            if (rt.units_checked() != 4) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 4", rt.units_checked()))
            if (rt.worst_lag() != 41) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected 41", rt.worst_lag()))
        endfunction
    endclass : rt_rv_split_test

    // Units of 8 beats through a pipe of 12 clocks, so output unit j ends
    // 5 clocks after input unit j + 1. The pipe drops the fifth unit, whose
    // anchor never comes.
    class rt_rv_anchor_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_anchor_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_rv_rt_t new_checker();
            return lb_rv_behind_rt::type_id::create("rt", this);
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].latency    = 12;
            lb_rt_pipe_cfg[LB_RT_RV].pass_limit = 32;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            seq.units     = 5;
            seq.beats     = 8;
            rt.lag_cycles = 6;
        endfunction

        virtual function void check();
            if (rt.units_checked() != 4) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 4", rt.units_checked()))
            if (rt.worst_lag() != 5) `uvm_error("LB_RT", $sformatf("worst lag %0d, expected 5", rt.worst_lag()))
        endfunction
    endclass : rt_rv_anchor_test

    // The run timeout, fixed at 600 clocks, ends a run whose pipe hangs
    // after 10 beats while unit 0's deadline of 2000 clocks is still ahead:
    // the checker raises nothing and its summary names the pending unit and
    // the timeout.
    class rt_rv_pending_timeout_test extends lb_rt_rv_base;
        a2c_run_timeout run_timeout;

        `uvm_component_utils(rt_rv_pending_timeout_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            demoter.also.push_back("A2C_RUN_TIMEOUT");
            run_timeout = a2c_run_timeout::type_id::create("run_timeout", this);
            configure_timeout();
        endfunction

        virtual function void configure_timeout();
            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_cycles", 600);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            run_timeout.clk_vif = clk_vif;
            run_timeout.clock   = "clk";
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 10;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = 1000000;
            seq.beats   = 64;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.lag_cycles = 2000;
            max_clocks    = 1000000;
            want["A2C_RUN_TIMEOUT"] = 1;
        endfunction

        virtual function void check();
            if (demoter.count("A2C_RT", UVM_INFO, "1 pending with the deadline not reached; the run timeout ended the run phase") != 1) begin
                `uvm_error("LB_RT", $sformatf("the summary does not name the pending unit and the timeout: %p", demoter.msgs))
            end
        endfunction
    endclass : rt_rv_pending_timeout_test

    // A derived run timeout of 300 clocks defers to the deadline rule
    // counting on unit 0, which then reports before the timeout expires.
    class rt_rv_defer_test extends rt_rv_pending_timeout_test;
        // clock_stop_cycles + 1 and the 10-clock margin, plus the clock the
        // count reads the rule's clocks left on before the rule steps.
        localparam int unsigned DEFER_AFTER = 1000 + 1 + 10 + 1;

        `uvm_component_utils(rt_rv_defer_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_timeout();
            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_floor_cycles", 300);
            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_factor", 0);
        endfunction

        virtual function void configure();
            super.configure();
            rt.lag_cycles = 600;
            want["A2C_RT_DEADLINE"] = 1;
        endfunction

        virtual function void check();
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_INFO, "the real-time deadline rule (rt_lag_cycles) of rv_out (uvm_test_top.rt)") != 1) begin
                `uvm_error("LB_RT", $sformatf("the deferral does not name the deadline rule: %p", demoter.msgs))
            end
            expect_at("A2C_RT_DEADLINE", edge_of(in_seen.at[63]) + 600 * 10ns);
            if (demoter.first_at("A2C_RUN_TIMEOUT") <= demoter.first_at("A2C_RT_DEADLINE")) begin
                `uvm_error("LB_RT", "the run timeout expired before the deadline rule reported")
            end
            if (demoter.first_at("A2C_RUN_TIMEOUT") - demoter.first_at("A2C_RT_DEADLINE") != DEFER_AFTER * 10ns) begin
                `uvm_error("LB_RT", $sformatf("the run timeout expired %0t after the deadline, expected %0d clocks",
                                              demoter.first_at("A2C_RUN_TIMEOUT") - demoter.first_at("A2C_RT_DEADLINE"), DEFER_AFTER))
            end
        endfunction
    endclass : rt_rv_defer_test

    // rt_rv_defer_test with a2c_rt_off set and the lag bound of 600 written
    // during the run: the deadline rule measures but counts toward no
    // report, so the run timeout expires at its budget of 300 clocks with
    // no deferral.
    class rt_rv_defer_off_test extends rt_rv_defer_test;
        realtime released_at;

        `uvm_component_utils(rt_rv_defer_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure();
            super.configure();
            uvm_config_db#(bit)::set(this, "rt", "a2c_rt_off", 1'b1);
            want.delete("A2C_RT_DEADLINE");
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    clk_vif.wait_reset_release();
                    released_at = $realtime;
                    repeat (10) clk_vif.sample_edge();
                    rt.lag_cycles = 600;
                end
            join_none
            lb_rt_rv_base::run_phase(phase);
        endtask

        virtual function void check();
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_INFO, "defers to them") != 0) `uvm_error("LB_RT", $sformatf("the timeout deferred to a checker that is off: %p", demoter.msgs))
            if (demoter.first_at("A2C_RUN_TIMEOUT") != released_at + 300 * 10ns) begin
                `uvm_error("LB_RT", $sformatf("A2C_RUN_TIMEOUT came at %0t, expected the budget's %0t", demoter.first_at("A2C_RUN_TIMEOUT"), released_at + 300 * 10ns))
            end
        endfunction
    endclass : rt_rv_defer_off_test

    // Output on clk3, which stops while the deadline rule counts, with no
    // other rule counting. The run timeout leaves the stopped checker out,
    // names it, and expires at its budget without a deferral.
    class rt_rv_defer_stopped_test extends rt_rv_pending_timeout_test;
        virtual a2c_clk_if clk3_vif;

        `uvm_component_utils(rt_rv_defer_stopped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_timeout();
            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_floor_cycles", 300);
            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_factor", 0);
        endfunction

        virtual function void configure();
            super.configure();
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            lb_rt_rv_out_clk3    = 1;
            dst_cfg.clk_vif      = clk3_vif;
            rt.lag_cycles        = 600;
            rt.clock_stop_cycles = 10;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    repeat (150) clk_vif.sample_edge();
                    lb_clk3_run = 0;
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            string left = "Left out, clock stopped: the real-time deadline rule (rt_lag_cycles) of rv_out (uvm_test_top.rt)";
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_ERROR, left) != 1) `uvm_error("LB_RT", $sformatf("the timeout does not leave out the stopped checker: %p", demoter.msgs))
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_INFO, "defers to them") != 0) `uvm_error("LB_RT", $sformatf("the timeout deferred to a stopped checker: %p", demoter.msgs))
        endfunction
    endclass : rt_rv_defer_stopped_test

    // Mode B: the DUT pipe hangs after 20 beats and fills, so the source's
    // DUT lane trails and is declared dead at the 50-clock skew bound. The
    // checker stops judging then: the gap of 300 the hang reaches later on
    // the DUT lane raises nothing, and the summary says why.
    class rt_rv_lane_death_test extends lb_rt_rv_base;
        `uvm_component_utils(rt_rv_lane_death_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_config_db#(int unsigned)::set(this, "src*", "a2c_lane_skew_cycles", 50);
            super.build_phase(phase);
            demoter.also.push_back("A2C_SKEW");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            // The DUT lane's missing beats are the death's, already reported.
            dst.model_cmp.counted = 1;
        endfunction

        virtual function void configure();
            lb_rt_pipe_cfg[LB_RT_RV].stall_after       = 20;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len         = 1000000;
            lb_rt_pipe_cfg[LB_RT_RV].depth             = 4;
            lb_rt_pipe_cfg[LB_RT_RV_MODEL].emit_n      = 1;
            lb_rt_pipe_cfg[LB_RT_RV_MODEL].emit_m      = 4;
            seq.beats   = 400;
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
            rt.gap_cycles = 300;
            rt.lag_cycles = 400;
            drain         = 1800;
            want["A2C_SKEW"] = 1;
        endfunction

        // The DUT lane's 20 beats, then long enough for the model lane.
        virtual function int unsigned out_beats();
            return 20;
        endfunction

        virtual function void check();
            if (demoter.count("A2C_RT", UVM_INFO, "stopped judging at") != 1) begin
                `uvm_error("LB_RT", $sformatf("the summary does not say the checker stopped: %p", demoter.msgs))
            end
            if (clocks < 1500) `uvm_error("LB_RT", $sformatf("the run took %0d clocks, too few for the gap bound to pass after the death", clocks))
        endfunction
    endclass : rt_rv_lane_death_test

    // The axis pipe's output on clk2, three times clk's period, against an
    // input on clk paced one beat in four clocks. Units of four lines, each
    // ended by tlast, so the checker stamps input events on another clock.
    class rt_axis_clk2_test extends lb_base_test;
        axis_agent_t                src;
        axis_agent_t                dst;
        lb_axis_rt_t                rt;
        lb_rt_demoter               demoter;
        lb_arrivals#(axis_item_t)   out_seen;
        virtual a2c_clk_if          clk2_vif;
        int unsigned                want_refusals;

        `uvm_component_utils(rt_axis_clk2_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            axis_config_t        src_cfg = axis_config_t::type_id::create("src_cfg");
            axis_config_t        dst_cfg = axis_config_t::type_id::create("dst_cfg");
            lb_axis_tlast_rule_t in_rule = lb_axis_tlast_rule_t::type_id::create("in_rule");
            lb_axis_tlast_rule_t out_rule = lb_axis_tlast_rule_t::type_id::create("out_rule");
            super.build_phase(phase);
            demoter = lb_rt_demoter::type_id::create("demoter");
            uvm_report_cb::add(null, demoter);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk2", clk2_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk2'")
            lb_rt_axis_clk2 = 1;
            lb_rt_pipe_cfg[LB_RT_AXIS].latency = 2;
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis_in", src_cfg.vif)) `uvm_fatal("LB_CFG", "no interface axis_in")
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis_out", dst_cfg.vif)) `uvm_fatal("LB_CFG", "no interface axis_out")
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "axis_in";
            dst_cfg.clk_vif   = clk2_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "axis_out";
            uvm_config_db#(axis_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(axis_config_t)::set(this, "dst", "cfg", dst_cfg);
            src      = axis_agent_t::type_id::create("src", this);
            dst      = axis_agent_t::type_id::create("dst", this);
            out_seen = lb_arrivals#(axis_item_t)::type_id::create("out_seen", this);
            rt       = lb_axis_rt_t::type_id::create("rt", this);
            in_rule.ends_per_unit  = 4;
            out_rule.ends_per_unit = 4;
            rt.in_rule        = in_rule;
            rt.out_rule       = out_rule;
            rt.lag_cycles     = 8;
            rt.latency_cycles = 8;
            rt.gap_cycles     = 4;
            rt.refusal_cycles = 1;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(out_seen.analysis_export);
            rt.connect_in(src.mon);
            rt.connect_out(dst.mon);
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_list_seq#(axis_item_t) seq = lb_list_seq#(axis_item_t)::type_id::create("seq");
            phase.raise_objection(this);
            for (int unsigned i = 0; i < 96; i++) begin
                axis_item_t it = axis_item_t::type_id::create("it");
                if (!it.randomize()) `uvm_fatal("LB_RAND", "axi4_stream item randomize failed")
                it.tlast = (i % 8 == 7);
                it.gap   = 3;
                seq.items.push_back(it);
            end
            clk_vif.wait_reset_release();
            seq.start(src.sqr);
            while (out_seen.items.size() < 96) clk2_vif.sample_edge();
            repeat (20) clk2_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (rt.units_checked() != 3) `uvm_error("LB_RT", $sformatf("%0d units checked, expected 3", rt.units_checked()))
            if (rt.worst_lag() == 0 || rt.worst_lag() >= 8) `uvm_error("LB_RT", $sformatf("worst lag %0d clocks of clk2, expected 1 to 7", rt.worst_lag()))
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (demoter.errors() != want_refusals || demoter.count("A2C_RT_REFUSAL") != want_refusals) begin
                `uvm_error("LB_RT", $sformatf("expected %0d A2C_RT_REFUSAL errors and no other: %p", want_refusals, demoter.msgs))
            end
            `uvm_info("LB_STATS", $sformatf("worst lag %0d, gap %0d, refusal %0d", rt.worst_lag(), rt.worst_gap(), rt.worst_refusal()), UVM_NONE)
            super.report_phase(phase);
        endfunction
    endclass : rt_axis_clk2_test

    // As rt_axis_clk2_test with the pipe refusing every third input clock,
    // which beats offered every fourth clock meet now and then: each of the
    // three input units has refused clocks, and the bound of 3 fails each
    // once.
    class rt_axis_refusal_test extends rt_axis_clk2_test;
        `uvm_component_utils(rt_axis_refusal_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            lb_rt_pipe_cfg[LB_RT_AXIS].refuse_every = 3;
            rt.refusal_cycles = 3;
            want_refusals     = 3;
        endfunction
    endclass : rt_axis_refusal_test

    // push_ack with no DUT: pa src to pa dst, an ack 25 clocks after each
    // push, and a 30-clock pause before beat 10. A clock push waits for ack
    // is the sink's and never a gap; push low with the unit open is, and its
    // gap reaches 20 twenty clocks after beat 9. The flow counts add up.
    class rt_pa_gap_test extends lb_base_test;
        pa_agent_t                         src;
        pa_agent_t                         dst;
        a2c_rt_checker #(pa_item_t, pa_item_t) rt;
        lb_rt_demoter                      demoter;
        lb_arrivals#(pa_item_t)            out_seen;

        `uvm_component_utils(rt_pa_gap_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            pa_config_t                     src_cfg = pa_config_t::type_id::create("src_cfg");
            pa_config_t                     dst_cfg = pa_config_t::type_id::create("dst_cfg");
            a2c_beat_count_rule#(pa_item_t) out_rule = a2c_beat_count_rule#(pa_item_t)::type_id::create("out_rule");
            pa_vif_t                        vif;
            super.build_phase(phase);
            demoter = lb_rt_demoter::type_id::create("demoter");
            uvm_report_cb::add(null, demoter);
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa", vif)) `uvm_fatal("LB_CFG", "no virtual push_ack_if 'pa'")
            src_cfg.vif = vif;
            dst_cfg.vif = vif;
            src_cfg.clk_vif = clk_vif;
            dst_cfg.clk_vif = clk_vif;
            src_cfg.role = A2C_SRC;
            dst_cfg.role = A2C_DST;
            src_cfg.port_name = "pa";
            dst_cfg.port_name = "pa";
            dst_cfg.ack_delay_min = 25;
            dst_cfg.ack_delay_max = 25;
            uvm_config_db#(pa_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(pa_config_t)::set(this, "dst", "cfg", dst_cfg);
            src      = pa_agent_t::type_id::create("src", this);
            dst      = pa_agent_t::type_id::create("dst", this);
            out_seen = lb_arrivals#(pa_item_t)::type_id::create("out_seen", this);
            rt       = a2c_rt_checker#(pa_item_t, pa_item_t)::type_id::create("rt", this);
            out_rule.beats_per_unit = 40;
            rt.out_rule   = out_rule;
            rt.gap_cycles = 20;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(out_seen.analysis_export);
            rt.connect_out(dst.mon);
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_list_seq#(pa_item_t) seq = lb_list_seq#(pa_item_t)::type_id::create("seq");
            phase.raise_objection(this);
            for (int unsigned i = 0; i < 40; i++) begin
                pa_item_t it = pa_item_t::type_id::create("it");
                if (!it.randomize()) `uvm_fatal("LB_RAND", "push_ack item randomize failed")
                it.gap = (i == 10) ? 30 : 0;
                seq.items.push_back(it);
            end
            clk_vif.wait_reset_release();
            seq.start(src.sqr);
            repeat (10) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            longint unsigned samples, valid, ready, transfers;
            a2c_flow_counts  fc;
            super.check_phase(phase);
            void'($cast(fc, dst.mon));
            fc.flow_counts(samples, valid, ready, transfers);
            if (transfers != 40) `uvm_error("LB_RT", $sformatf("%0d transfers counted, expected 40", transfers))
            if (valid < transfers + 40 * 25) `uvm_error("LB_RT", $sformatf("%0d push clocks for %0d transfers, expected 25 waits each", valid, transfers))
            if (samples - ready != valid - transfers) begin
                `uvm_error("LB_RT", $sformatf("%0d clocks counted not ready, expected the %0d with push waiting for ack", samples - ready, valid - transfers))
            end
            if (demoter.first_at("A2C_RT_GAP") != out_seen.at[9] + 5ns + 20 * 10ns) begin
                `uvm_error("LB_RT", $sformatf("the gap came at %0t, expected %0t", demoter.first_at("A2C_RT_GAP"), out_seen.at[9] + 5ns + 20 * 10ns))
            end
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (demoter.count("A2C_RT_GAP") != 1 || demoter.errors() != 1) `uvm_error("LB_RT", $sformatf("expected one A2C_RT_GAP: %p", demoter.msgs))
            super.report_phase(phase);
        endfunction
    endclass : rt_pa_gap_test

    // A generated env with a checker, so the base test's knobs reach it.
    class lb_gen_rt_env extends lb_gen_env;
        rv_agent_t rv_agent;
        lb_rv_rt_t rt;

        `uvm_component_utils(lb_gen_rt_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t cfg = rv_config_t::type_id::create("rv_cfg");
            super.build_phase(phase);
            if (!uvm_config_db#(rv_vif_t)::get(null, "uvm_test_top", "rv_out", cfg.vif)) `uvm_fatal("LB_CFG", "no interface rv_out")
            cfg.clk_vif   = clk_vif;
            cfg.role      = A2C_DST;
            cfg.port_name = "rv_out";
            cfg.is_active = UVM_PASSIVE;
            uvm_config_db#(rv_config_t)::set(this, "rv_agent", "cfg", cfg);
            rv_agent = rv_agent_t::type_id::create("rv_agent", this);
            rt       = lb_rv_rt_t::type_id::create("rt", this);
            rt.in_rule  = lb_rv_eof_rule::type_id::create("in_rule");
            rt.out_rule = lb_rv_eof_rule::type_id::create("out_rule");
        endfunction

        // One idle port as both input and output: the test reads only the
        // knobs, and the lag rule needs an input.
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            rt.connect_in(rv_agent.mon);
            rt.connect_out(rv_agent.mon);
        endfunction
    endclass : lb_gen_rt_env

    // The generated base test hands its real-time knobs to the env's
    // checker: rt_gap_cycles and rt_latency_cycles from the constructor,
    // rt_lag_cycles and rt_on_model from plusargs over the constructor's.
    // set_limits() then changes the gap and refusal bounds and leaves the
    // plusarg's lag bound.
    // LB_PLUSARGS gen_base_rt_knobs_test +a2c_rt_lag_cycles=7 +a2c_rt_on_model=1
    class gen_base_rt_knobs_test extends lb_gen_base;
        int unsigned bounds[3];

        `uvm_component_utils(gen_base_rt_knobs_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            rt_gap_cycles        = 9;
            rt_latency_cycles    = 11;
            rt_lag_cycles        = 3;
            no_stimulus_expected = 1;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            lb_gen_env::type_id::set_type_override(lb_gen_rt_env::get_type());
            super.build_phase(phase);
        endfunction

        virtual task run_body();
            lb_gen_rt_env e;
            void'($cast(e, env));
            bounds[0] = e.rt.gap_cycles;
            bounds[1] = e.rt.lag_cycles;
            bounds[2] = e.rt.refusal_cycles;
            e.rt.set_limits(5, 5, 5);
        endtask

        virtual function void check_phase(uvm_phase phase);
            lb_gen_rt_env e;
            super.check_phase(phase);
            void'($cast(e, env));
            if (bounds[0] != 9 || bounds[1] != 7 || bounds[2] != 0) begin
                `uvm_error("LB_RT", $sformatf("before set_limits() gap %0d, lag %0d, refusal %0d; expected 9, 7, 0",
                                              bounds[0], bounds[1], bounds[2]))
            end
            if (e.rt.gap_cycles != 5 || e.rt.lag_cycles != 7 || e.rt.refusal_cycles != 5) begin
                `uvm_error("LB_RT", $sformatf("set_limits(5, 5, 5) left gap %0d, lag %0d, refusal %0d; expected 5, the plusarg's 7, 5",
                                              e.rt.gap_cycles, e.rt.lag_cycles, e.rt.refusal_cycles))
            end
            if (e.rt.latency_cycles != 11 || !e.rt.on_model) begin
                `uvm_error("LB_RT", $sformatf("latency %0d and on_model %0d, expected 11 and 1", e.rt.latency_cycles, e.rt.on_model))
            end
        endfunction

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            `uvm_info("LB_STATS", $sformatf("bounds before set_limits() %0d, %0d, %0d", bounds[0], bounds[1], bounds[2]), UVM_NONE)
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
        endfunction
    endclass : gen_base_rt_knobs_test
