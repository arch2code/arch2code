// Randomised tests of a2c_rt_checker against lb_rt_trial's reference
// pipeline, a model with no pins that writes its two ports' flow counts and
// unit ends as monitors would, on clk_rt. Each test runs many trials at
// once, each with its own random configuration, pipeline, further
// starvation source and checker, and an oracle judges each trial:
//   - a conforming pipeline raises no real-time error with every rule on at
//     the tightest bound the pipeline meets: the gap at 1 to 3, the window
//     at the pipeline's latency, the lag one above the pipeline's own, the
//     refusal at 1;
//   - a stall injected into an open output unit is reported as A2C_RT_GAP
//     no later than the bound specs/SIMULATOR_INTEGRATION.md states, worked
//     out from the trial's own trace.
// Included in a2c_uvm_loopback_pkg after a2c_rt_checker_lb_tests.svh, whose
// lb_rt_demoter it uses.

    class lb_rt_beat extends uvm_sequence_item;
        bit last;

        `uvm_object_utils(lb_rt_beat)

        function new(string name = "lb_rt_beat");
            super.new(name);
        endfunction
    endclass : lb_rt_beat

    class lb_rt_last_rule extends a2c_unit_rule #(lb_rt_beat);
        `uvm_object_utils(lb_rt_last_rule)

        function new(string name = "lb_rt_last_rule");
            super.new(name);
        endfunction

        virtual function bit is_unit_end(lb_rt_beat t);
            return t.last;
        endfunction
    endclass : lb_rt_last_rule

    typedef a2c_rt_checker #(lb_rt_beat, lb_rt_beat) lb_rt_ref_checker_t;

    // One port of the reference pipeline: the counts and items a monitor
    // reports, written at the sample point of each clock.
    class lb_rt_ref_port extends uvm_component implements a2c_flow_counts;
        uvm_analysis_port #(lb_rt_beat) ap;
        a2c_clk_vif_t                   clk_vif;
        protected longint unsigned      n[4];

        `uvm_component_utils(lb_rt_ref_port)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        function void sample(bit valid, bit ready, bit last);
            lb_rt_beat b;
            n[0]++;
            n[1] += valid;
            n[2] += ready;
            n[3] += valid && ready;
            if (!(valid && ready)) return;
            b      = lb_rt_beat::type_id::create("b");
            b.last = last;
            ap.write(b);
        endfunction

        virtual function void flow_counts(output longint unsigned samples, output longint unsigned valid,
                                          output longint unsigned ready, output longint unsigned transfers);
            samples   = n[0];
            valid     = n[1];
            ready     = n[2];
            transfers = n[3];
        endfunction

        virtual function a2c_clk_vif_t flow_clock();
            return clk_vif;
        endfunction

        virtual function string flow_port();
            return get_full_name();
        endfunction
    endclass : lb_rt_ref_port

    // A responder the pipeline waits on, as a pop_ack monitor reports it.
    class lb_rt_ref_source extends uvm_component implements a2c_starvation_source;
        longint unsigned samples;
        longint unsigned withheld;

        `uvm_component_utils(lb_rt_ref_source)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void starvation_counts(output longint unsigned samples, output longint unsigned withheld);
            samples  = this.samples;
            withheld = this.withheld;
        endfunction

        virtual function string starvation_port();
            return get_full_name();
        endfunction
    endclass : lb_rt_ref_source

    // A trial's pipeline and checker bounds.
    //   - lat: a beat accepted on clock t is processed from t + 1, one beat
    //     a clock, and offered from lat - 1 clocks after it is processed, so
    //     from t + lat at the earliest; lat is 1 or more;
    //   - depth: the beats the pipeline holds, at least lat + 3, so it never
    //     refuses input while its output keeps up; reg_ready takes ready
    //     from the occupancy after the last clock, else from this clock's
    //     with this clock's output beat gone;
    //   - sf: an input unit is processed only once all of it has arrived;
    //   - in_per_out, out_per_in: the unit ratio, one beat out per beat in;
    //     a split (out_per_in above 1) is store and forward, or its output
    //     units would end before their anchor;
    //   - gap_pct, max_gap, v_blank: the source's pacing, a gap of 1 to
    //     max_gap clocks before gap_pct percent of beats and up to v_blank
    //     before each unit;
    //   - ready_pct, ready_burst: the sink is ready on ready_pct percent of
    //     clocks, and each clock it is not holds ready low up to
    //     ready_burst - 1 more;
    //   - src_pct, src_burst: the further source starts withholding on
    //     src_pct percent of clocks, for 1 to src_burst clocks, and the
    //     pipeline processes nothing while it does; src_stream connects it
    //     as a stream the testbench drives, withholding on the clocks it
    //     offers no beat, else as a responder that counts its own;
    //   - stall_beat: 0, or the output beat after which the pipeline offers
    //     nothing for stall_len clocks, a beat that is not its unit's last.
    class lb_rt_ref_cfg;
        int unsigned lat;
        int unsigned depth;
        bit          reg_ready;
        bit          sf;
        int unsigned in_per_out = 1;
        int unsigned out_per_in = 1;
        int unsigned in_beats;
        int unsigned units;
        int unsigned gap_pct;
        int unsigned max_gap;
        int unsigned v_blank;
        int unsigned ready_pct;
        int unsigned ready_burst;
        int unsigned src_pct;
        int unsigned src_burst;
        bit          src_stream;
        int unsigned stall_beat;
        int unsigned stall_len = 800;
        int unsigned gap;
        int unsigned window;
        int unsigned lag;

        function void randomize_cfg(bit allow_stall);
            int unsigned r = $urandom_range(9, 0);
            lat       = $urandom_range(12, 1);
            reg_ready = $urandom_range(1, 0);
            sf        = $urandom_range(3, 0) == 0;
            if (r < 2) in_per_out = $urandom_range(3, 2);
            else if (r < 4) out_per_in = $urandom_range(4, 2);
            if (out_per_in > 1) begin
                sf       = 1;
                in_beats = out_per_in * $urandom_range(12, 2);
            end else begin
                in_beats = $urandom_range(40, 4);
            end
            // Store and forward of input units shorter than the output unit
            // idles an open output unit while input flows.
            if (in_per_out > 1) sf = 0;
            units       = in_per_out * $urandom_range(8 / in_per_out, 2);
            depth       = lat + 3 + $urandom_range(6, 0) + (sf ? 2 * in_beats : 0);
            gap_pct     = $urandom_range(1, 0) ? $urandom_range(80, 0) : 0;
            max_gap     = $urandom_range(6, 1);
            v_blank     = $urandom_range(40, 0);
            ready_pct   = $urandom_range(1, 0) ? 100 : $urandom_range(95, 40);
            ready_burst = (ready_pct != 100 && $urandom_range(1, 0)) ? $urandom_range(20, 1) : 0;
            src_pct     = $urandom_range(1, 0) ? $urandom_range(15, 2) : 0;
            src_burst   = $urandom_range(8, 1);
            src_stream  = $urandom_range(1, 0);
            gap         = $urandom_range(3, 1);
            window      = lat;
            lag         = lat + (sf ? in_beats - 1 : 0) + 1;
            stall_beat  = 0;
            if (allow_stall && $urandom_range(2, 0) == 0) begin
                int unsigned out_n = (out_per_in > 1) ? in_beats / out_per_in : in_beats * in_per_out;
                do stall_beat = $urandom_range(units * in_beats - 1, 1);
                while (stall_beat % out_n == 0);
            end
        endfunction

        function string sprint();
            return $sformatf("lat %0d depth %0d reg_ready %0d sf %0d in_per_out %0d out_per_in %0d in_beats %0d units %0d gap_pct %0d max_gap %0d v_blank %0d ready_pct %0d ready_burst %0d src_pct %0d src_burst %0d src_stream %0d stall_beat %0d; bounds gap %0d window %0d lag %0d",
                             lat, depth, reg_ready, sf, in_per_out, out_per_in, in_beats, units, gap_pct, max_gap, v_blank, ready_pct,
                             ready_burst, src_pct, src_burst, src_stream, stall_beat, gap, window, lag);
        endfunction
    endclass : lb_rt_ref_cfg

    // One trial: the reference pipeline, stepped at each sample point of
    // clk_rt, its ports, its further source and the checker on them, and
    // the per-clock trace the oracle reads.
    class lb_rt_trial extends uvm_component;
        lb_rt_ref_cfg       cfg;
        a2c_clk_vif_t       clk_vif;
        lb_rt_ref_port      in_p;
        lb_rt_ref_port      out_p;
        lb_rt_ref_source    src;
        lb_rt_ref_port      src_p;
        lb_rt_ref_checker_t rt;
        bit                 done;
        // What the oracle reads of each clock: its sample time; whether the
        // output idled with its sink ready, or offered a beat the sink
        // refused; whether the further source withheld; whether the input
        // withheld, transferred, or was refused, and the input unit it was
        // on; the free clocks so far; the output units ended before it.
        typedef struct {
            realtime         at;
            bit              idle;
            bit              stall;
            bit              sec;
            bit              in_w;
            bit              in_x;
            bit              refused;
            int unsigned     unit;
            longint unsigned free;
            int unsigned     out_ended;
        } rec_t;
        rec_t               trace[$];
        longint unsigned    stall_from;
        // Totals over the trial, for the test's statistics.
        int unsigned        n_idle;
        int unsigned        n_refused;
        int unsigned        n_stall;
        int unsigned        n_sec;
        // Output units ended before the last reset.
        int unsigned        ended_before;

        typedef struct {
            int unsigned     unit;
            bit              out_last;
            longint unsigned at;
            longint unsigned proc;
        } beat_t;
        protected beat_t           q[$];
        protected int unsigned     nproc;
        protected longint unsigned done_at[int unsigned];
        protected int unsigned     src_unit;
        protected int unsigned     src_beat;
        protected int unsigned     src_wait;
        protected bit              rdy_q = 1;
        protected int unsigned     hold_left;
        protected int unsigned     sec_left;
        protected int unsigned     stall_left;
        protected int unsigned     out_count;
        protected int unsigned     out_ended;
        protected longint unsigned free;

        `uvm_component_utils(lb_rt_trial)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            lb_rt_last_rule in_rule  = lb_rt_last_rule::type_id::create("in_rule");
            lb_rt_last_rule out_rule = lb_rt_last_rule::type_id::create("out_rule");
            super.build_phase(phase);
            in_p  = lb_rt_ref_port::type_id::create("in_p", this);
            out_p = lb_rt_ref_port::type_id::create("out_p", this);
            src   = lb_rt_ref_source::type_id::create("src", this);
            src_p = lb_rt_ref_port::type_id::create("src_p", this);
            src_p.clk_vif = clk_vif;
            rt    = lb_rt_ref_checker_t::type_id::create("rt", this);
            in_p.clk_vif  = clk_vif;
            out_p.clk_vif = clk_vif;
            rt.in_rule          = in_rule;
            rt.out_rule         = out_rule;
            rt.in_units_per_out = cfg.in_per_out;
            rt.out_units_per_in = cfg.out_per_in;
            rt.gap_cycles       = cfg.gap;
            rt.latency_cycles   = cfg.window;
            rt.lag_cycles       = cfg.lag;
            rt.refusal_cycles   = 1;
            rt.max_reported     = 1000;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            rt.connect_in(in_p);
            rt.connect_out(out_p);
            if (cfg.src_pct != 0) begin
                if (cfg.src_stream) rt.connect_source(src_p);
                else rt.connect_source(src);
            end
        endfunction

        function int unsigned anchor(int unsigned k);
            if (cfg.in_per_out > 1) return k * cfg.in_per_out + cfg.in_per_out - 1;
            return k / cfg.out_per_in;
        endfunction

        function int unsigned out_units();
            return cfg.units * cfg.out_per_in / cfg.in_per_out;
        endfunction

        protected function bit out_last_of(int unsigned u, int unsigned b);
            if (cfg.out_per_in > 1) return (b + 1) % (cfg.in_beats / cfg.out_per_in) == 0;
            return b == cfg.in_beats - 1 && u % cfg.in_per_out == cfg.in_per_out - 1;
        endfunction

        protected function int unsigned pace(int unsigned pct, int unsigned most);
            return ($urandom_range(99, 0) < pct) ? $urandom_range(most, 1) : 0;
        endfunction

        // A reset empties the pipeline, and the source starts its units
        // again from the first.
        function void flush();
            ended_before += out_ended;
            q.delete();
            done_at.delete();
            nproc      = 0;
            src_unit   = 0;
            src_beat   = 0;
            src_wait   = 0;
            rdy_q      = 1;
            hold_left  = 0;
            sec_left   = 0;
            stall_left = 0;
            out_count  = 0;
            out_ended  = 0;
        endfunction

        // The first sample after a reset release is the one the monitors
        // take first, on the falling edge after the rising edge that samples
        // the release.
        virtual task run_phase(uvm_phase phase);
            forever begin
                clk_vif.wait_reset_release();
                forever begin
                    clk_vif.sample_edge();
                    if (clk_vif.rst_n !== 1'b1) break;
                    step();
                end
                flush();
            end
        endtask

        protected function void step();
            rec_t        r;
            bit          ready;
            bit          sec;
            bit          stalling = stall_left != 0;
            bit          src_valid;
            bit          in_rdy;
            bit          in_xfer;
            bit          out_valid;
            bit          out_xfer;
            bit          out_last;
            bit          last_in;
            longint unsigned now = trace.size();
            if (hold_left != 0) begin
                ready = 0;
                hold_left--;
            end else begin
                ready = $urandom_range(99, 0) < cfg.ready_pct;
                if (!ready && cfg.ready_burst != 0) hold_left = $urandom_range(cfg.ready_burst - 1, 0);
            end
            if (sec_left != 0) begin
                sec = 1;
                sec_left--;
            end else begin
                sec = cfg.src_pct != 0 && $urandom_range(99, 0) < cfg.src_pct;
                if (sec) sec_left = $urandom_range(cfg.src_burst - 1, 0);
            end
            src_valid = src_unit < cfg.units && src_wait == 0;
            if (!sec && nproc < q.size() && q[nproc].at < now
                    && (!cfg.sf || (done_at.exists(q[nproc].unit) && done_at[q[nproc].unit] < now))) begin
                q[nproc].proc = now;
                nproc++;
            end
            out_valid = !stalling && nproc != 0 && q[0].proc + cfg.lat - 1 <= now;
            out_xfer  = out_valid && ready;
            out_last  = out_valid && q[0].out_last;
            in_rdy    = cfg.reg_ready ? rdy_q : (q.size() - out_xfer < cfg.depth);
            in_xfer   = src_valid && in_rdy;
            last_in   = src_beat == cfg.in_beats - 1;
            if (!(out_valid && !ready) && !sec) free++;
            r = '{at: $realtime, idle: ready && !out_valid, stall: out_valid && !ready, sec: sec, in_w: !src_valid,
                  in_x: in_xfer, refused: src_valid && !in_rdy, unit: src_unit, free: free, out_ended: out_ended};
            trace.push_back(r);
            n_idle    += r.idle && out_ended < out_units() && out_count != 0;
            n_refused += r.refused;
            n_stall   += r.stall;
            n_sec     += sec;
            in_p.sample(src_valid, in_rdy, last_in);
            out_p.sample(out_valid, ready, out_last);
            src.samples++;
            src.withheld += sec;
            src_p.sample(!sec, 1'b1, 1'b0);
            if (stalling) stall_left--;
            if (out_xfer) begin
                void'(q.pop_front());
                nproc--;
                out_count++;
                if (out_last) out_ended++;
                if (out_count == cfg.stall_beat) begin
                    stall_left = cfg.stall_len;
                    stall_from = now + 1;
                end
            end
            if (in_xfer) begin
                q.push_back('{unit: src_unit, out_last: out_last_of(src_unit, src_beat), at: now, proc: 0});
                if (last_in) done_at[src_unit] = now;
                if (++src_beat == cfg.in_beats) begin
                    src_beat = 0;
                    src_unit++;
                    src_wait = $urandom_range(cfg.v_blank, 0);
                end else begin
                    src_wait = pace(cfg.gap_pct, cfg.max_gap);
                end
            end else if (!src_valid && src_wait != 0) begin
                src_wait--;
            end
            rdy_q = q.size() < cfg.depth;
            done  = out_count == cfg.units * cfg.in_beats && stall_left == 0;
        endfunction

        // The trace from clock from to clock to, for a failure's report.
        function void dump(longint unsigned from, longint unsigned to);
            for (longint unsigned c = from; c < trace.size() && c <= to; c++) begin
                `uvm_info("LB_RT_TRACE", $sformatf("%s clock %0d at %0t: idle %0d stall %0d sec %0d in_w %0d in_x %0d refused %0d unit %0d free %0d out_ended %0d",
                                                   get_name(), c, trace[c].at, trace[c].idle, trace[c].stall, trace[c].sec, trace[c].in_w, trace[c].in_x,
                                                   trace[c].refused, trace[c].unit, trace[c].free, trace[c].out_ended), UVM_NONE)
            end
        endfunction

        // The clock whose sample time is at, the falling edge before the
        // rising edge at which a report came.
        function longint unsigned clock_at(realtime at);
            for (longint unsigned c = trace.size(); c > 0; c--) if (trace[c - 1].at < at) return c - 1;
            return 0;
        endfunction

        // The demoted real-time errors of this trial's checker: their ids and
        // times.
        protected function void errors_of(lb_rt_demoter d, ref string ids[$], ref realtime ats[$]);
            string p = {out_p.get_full_name(), ":"};
            foreach (d.ids[i]) begin
                if (d.sevs[i] != UVM_ERROR || d.msgs[i].len() < p.len() || d.msgs[i].substr(0, p.len() - 1) != p) continue;
                ids.push_back(d.ids[i]);
                ats.push_back(d.at[i]);
            end
        endfunction

        // The last clock by which the checker must report the injected
        // stall: the first clock from stall_from on by which the clocks it
        // must charge reach the gap bound. An idle clock is charged when the
        // pipeline has held a beat of the open unit for the window's idle
        // clocks since the beat or the further source's last withholding;
        // the other idle clocks are charged less the credits that can pair
        // with them, at most those alive at stall_from and those earned
        // since. -1 when the stall ends first.
        function longint bound_clock();
            longint unsigned s = stall_from;
            int unsigned     a = anchor(trace[s].out_ended);
            longint unsigned alive = 0;
            longint unsigned earned = 0;
            longint unsigned idles = 0;
            longint unsigned by_work = 0;
            longint unsigned work_idle = 0;
            longint unsigned work_at;
            bit              work_held = 0;
            for (longint w = longint'(s) - 1; w >= 0 && trace[w].free + cfg.window >= trace[s].free; w--) begin
                alive += (trace[w].in_w && trace[w].unit <= a) + trace[w].sec;
            end
            for (longint unsigned c = s - 1; c < trace.size() && c < s + cfg.stall_len; c++) begin
                bit work = 0;
                if (trace[c].sec) begin
                    work_at   = c;
                    work_idle = 0;
                end
                if (trace[c].in_x && trace[c].unit <= a && !work_held) begin
                    work_held = 1;
                    work_at   = c;
                    work_idle = 0;
                end
                if (c < s) continue;
                earned += (trace[c].in_w && trace[c].unit <= a) + trace[c].sec;
                if (!trace[c].idle) continue;
                if (work_held && c > work_at) begin
                    work_idle++;
                    work = work_idle >= cfg.window;
                end
                if (work) by_work++;
                else idles++;
                if (by_work + ((idles > alive + earned) ? idles - alive - earned : 0) >= cfg.gap) return c;
            end
            return -1;
        endfunction

        // The corollary bound of a stall with the sink always ready, no
        // further source and no hold before it: the stall's first d + W + G
        // clocks, where d is the clocks after it began on which the input
        // withheld a unit the open output unit needs before it first offered
        // one.
        function longint unsigned simple_bound();
            int unsigned     a = anchor(trace[stall_from].out_ended);
            longint unsigned d = 0;
            for (longint unsigned c = stall_from; c < trace.size(); c++) begin
                if (trace[c].unit > a || !trace[c].in_w) break;
                d++;
            end
            return stall_from + d + cfg.window + cfg.gap - 1;
        endfunction

        // Set by judge() for a stall whose bound lies beyond its end, which
        // only a further source withholding through it can cause.
        bit                 unbounded;

        // Judges the trial: "" or what went wrong. detect_delay is the
        // clocks from the stall's first to its report, and slack the clocks
        // the report came before its bound.
        function string judge(lb_rt_demoter d, output longint detect_delay, output longint slack, output bit simple_checked);
            string   ids[$];
            realtime ats[$];
            realtime half = clk_vif.period / 2;
            realtime gap_at = -1;
            longint  b;
            detect_delay   = -1;
            slack          = -1;
            simple_checked = 0;
            errors_of(d, ids, ats);
            if (!done) return $sformatf("the pipeline did not finish: %0d of %0d beats out", out_count, cfg.units * cfg.in_beats);
            if (cfg.stall_beat == 0) begin
                if (ids.size() != 0) return $sformatf("%0d real-time errors on a conforming pipeline, the first %s at %0t", ids.size(), ids[0], ats[0]);
                if (rt.units_checked() != ended_before + out_units()) return $sformatf("%0d output units checked, expected %0d", rt.units_checked(), ended_before + out_units());
                return "";
            end
            foreach (ids[i]) begin
                if (ids[i] == "A2C_RT_GAP" && gap_at < 0) gap_at = ats[i];
                if (!(ids[i] inside {"A2C_RT_GAP", "A2C_RT_DEADLINE", "A2C_RT_REFUSAL"})) return $sformatf("%s at %0t on a stalled pipeline", ids[i], ats[i]);
                if (ats[i] < trace[stall_from].at) return $sformatf("%s at %0t before the stall began at %0t", ids[i], ats[i], trace[stall_from].at + half);
            end
            b = bound_clock();
            if (b < 0) begin
                unbounded = 1;
                if (cfg.src_pct == 0) return $sformatf("the stall from %0t has no bound, yet no further source withheld", trace[stall_from].at + half);
                return "";
            end
            if (gap_at < 0) return $sformatf("the stall from %0t was not reported; its bound was %0t", trace[stall_from].at + half, trace[b].at + half);
            if (gap_at > trace[b].at + half) return $sformatf("the stall from %0t was reported at %0t, after its bound of %0t", trace[stall_from].at + half, gap_at, trace[b].at + half);
            detect_delay = longint'((gap_at - trace[stall_from].at - half) / clk_vif.period);
            slack        = longint'((trace[b].at + half - gap_at) / clk_vif.period);
            if (cfg.ready_pct == 100 && cfg.src_pct == 0) begin
                longint unsigned sb = simple_bound();
                simple_checked = 1;
                if (sb >= trace.size() || gap_at > trace[sb].at + half) return $sformatf("the stall from %0t was reported at %0t, after the d + W + G bound of clock %0d", trace[stall_from].at + half, gap_at, sb);
            end
            return "";
        endfunction
    endclass : lb_rt_trial

    // The trials on clk_rt, run until each pipeline has delivered every beat.
    // report_phase passes on every trial's verdict and prints the totals:
    // trials, stalls detected, the worst detection delay and the least slack
    // against the bound, and the clocks of each kind the conforming trials
    // exercised.
    class lb_rt_ref_base extends lb_base_test;
        int unsigned       n_trials = 96;
        int unsigned       max_clocks = 60000;
        bit                allow_stall = 1;
        lb_rt_trial        trials[$];
        lb_rt_demoter      demoter;
        a2c_clk_vif_t      rt_clk;
        int unsigned       clocks;
        // The failing trials whose trace around the failure is printed.
        int unsigned       dump_failed = 3;
        bit                stimulus_done;

        `uvm_component_utils(lb_rt_ref_base)

        // The clock of a trial's first real-time error, or of its stall.
        function longint unsigned dump_from(lb_rt_trial t);
            foreach (demoter.ids[i]) begin
                if (demoter.sevs[i] == UVM_ERROR && a2c_contains(demoter.msgs[i], {t.out_p.get_full_name(), ":"})) return t.clock_at(demoter.at[i]);
            end
            return t.stall_from;
        endfunction

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk_rt", rt_clk)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk_rt'")
            demoter = lb_rt_demoter::type_id::create("demoter");
            uvm_report_cb::add(null, demoter);
            for (int unsigned i = 0; i < n_trials; i++) begin
                lb_rt_trial t = lb_rt_trial::type_id::create($sformatf("t%0d", i), this);
                t.cfg = new();
                t.cfg.randomize_cfg(allow_stall);
                t.clk_vif = rt_clk;
                trials.push_back(t);
            end
        endfunction

        function bit all_done();
            foreach (trials[i]) if (!trials[i].done) return 0;
            return 1;
        endfunction

        virtual task stimulus();
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            rt_clk.wait_reset_release();
            fork
                begin
                    stimulus();
                    stimulus_done = 1;
                end
            join_none
            while (!(all_done() && stimulus_done) && clocks < max_clocks) begin
                rt_clk.sample_edge();
                clocks++;
            end
            repeat (20) rt_clk.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            int unsigned conforming = 0;
            int unsigned stalls = 0;
            int unsigned detected = 0;
            int unsigned simple = 0;
            int unsigned unbounded = 0;
            int unsigned failed = 0;
            longint      worst_delay = -1;
            longint      least_slack = -1;
            longint unsigned idle = 0;
            longint unsigned refused = 0;
            longint unsigned stall = 0;
            longint unsigned sec = 0;
            foreach (trials[i]) begin
                longint delay;
                longint slack;
                bit     simple_checked;
                string  why = trials[i].judge(demoter, delay, slack, simple_checked);
                if (why != "") begin
                    failed++;
                    `uvm_error("LB_RT", $sformatf("%s: %s; %s", trials[i].get_name(), why, trials[i].cfg.sprint()))
                    if (failed <= dump_failed) trials[i].dump(dump_from(trials[i]) > 60 ? dump_from(trials[i]) - 60 : 0, dump_from(trials[i]) + 5);
                end
                if (trials[i].cfg.stall_beat == 0) begin
                    conforming++;
                    idle    += trials[i].n_idle;
                    refused += trials[i].n_refused;
                    stall   += trials[i].n_stall;
                    sec     += trials[i].n_sec;
                end else begin
                    stalls++;
                end
                if (delay >= 0) begin
                    detected++;
                    if (delay > worst_delay) worst_delay = delay;
                    if (least_slack < 0 || slack < least_slack) least_slack = slack;
                end
                simple    += simple_checked;
                unbounded += trials[i].unbounded;
            end
            if (conforming == 0 || (allow_stall && detected == 0)) `uvm_error("LB_RT", $sformatf("%0d conforming trials and %0d detected stalls: the oracle checked nothing", conforming, detected))
            `uvm_info("LB_STATS", $sformatf("%0d trials in %0d clocks, %0d failed: %0d conforming, with %0d open-unit idle, %0d refused, %0d sink-stall and %0d further-source clocks; %0d stalls, %0d detected within their bound, %0d of them also within d + W + G, %0d with a further source withholding past their end; worst detection %0d clocks after the stall began, least slack %0d clocks",
                                            trials.size(), clocks, failed, conforming, idle, refused, stall, sec, stalls, detected, simple,
                                            unbounded, worst_delay, least_slack), UVM_NONE)
            super.report_phase(phase);
        endfunction
    endclass : lb_rt_ref_base

    // Conforming and stalled pipelines of random configuration.
    class rt_ref_random_test extends lb_rt_ref_base;
        `uvm_component_utils(rt_ref_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass : rt_ref_random_test

    // Conforming pipelines through three resets of clk_rt's domain at random
    // clocks, each in the middle of the trials' units: every checker
    // abandons its open units and pairs units afresh from the release, so
    // no unit, deadline or credit of before a reset reaches past it.
    class rt_ref_reset_test extends lb_rt_ref_base;
        `uvm_component_utils(rt_ref_reset_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            allow_stall = 0;
            n_trials    = 48;
        endfunction

        virtual task stimulus();
            repeat (3) begin
                repeat ($urandom_range(400, 100)) rt_clk.drive_edge();
                lb_rt_rst_n = 1'b0;
                repeat ($urandom_range(5, 1)) rt_clk.drive_edge();
                lb_rt_rst_n = 1'b1;
            end
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            foreach (trials[i]) begin
                if (trials[i].rt.resets_seen() != 3) `uvm_error("LB_RT", $sformatf("%s saw %0d resets, expected 3", trials[i].get_name(), trials[i].rt.resets_seen()))
            end
        endfunction
    endclass : rt_ref_reset_test
