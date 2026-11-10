// Loopback tests of the joint stall rule in Mode A, on the lb_rt_pipe
// stand-in DUT between rv_in and rv_out, and between axis_in and axis_out
// where a second port is needed, and on the AXI master and slave pairs.
// Included in a2c_uvm_loopback_pkg after a2c_rt_checker_lb_tests.svh,
// whose lb_rt_rv_base they extend; its checker has no rule on here. Clock
// periods: clk 10ns, rising 5ns after each falling edge, where the monitors
// sample; clk3 20ns.

    // The last sentence of a Mode A A2C_JOINT_STALL, in a test with a run
    // timeout, which the stall ends the run through, and in one without.
    localparam string LB_JS_MODE_A_END = "No port made progress, so the cause may lie in the DUT, the model or the stimulus, such as a deadlock between ports or an event that nothing produces. With one DUT no lane dies, and the run ends here.";
    localparam string LB_JS_MODE_A_WAIT = "No port made progress, so the cause may lie in the DUT, the model or the stimulus, such as a deadlock between ports or an event that nothing produces. With one DUT no lane dies, and with no run timeout to end the run the masters go on waiting.";

    // What every test here shares: rv_in's master has the joint stall
    // bound joint, and with budget above 0 the run has an a2c_run_timeout
    // on clk whose derived budget is budget clocks. configure_js() sets the
    // test's pipe and sequence. The base class's report_phase passes only
    // on exactly want[id] errors of A2C_JOINT_STALL, A2C_RUN_TIMEOUT and
    // the checker's ids.
    class lb_js_rv_base extends lb_rt_rv_base;
        int unsigned    joint = 200;
        int unsigned    budget;
        a2c_run_timeout run_timeout;
        realtime        released_at;

        `uvm_component_utils(lb_js_rv_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_js();
        endfunction

        // The pipe takes 24 beats, emits 20 and stops for good.
        protected function void stop_pipe(lb_rt_pipe_e id);
            lb_rt_pipe_cfg[id].stall_after = 20;
            lb_rt_pipe_cfg[id].stall_len   = 1000000;
            lb_rt_pipe_cfg[id].depth       = 4;
        endfunction

        virtual function void configure();
            demoter.also.push_back("A2C_JOINT_STALL");
            demoter.also.push_back("A2C_RUN_TIMEOUT");
            seq.beats = 64;
            configure_js();
            uvm_config_db#(int unsigned)::set(this, "src.drv", "a2c_joint_stall_cycles", joint);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (budget == 0) return;
            run_timeout = a2c_run_timeout::type_id::create("run_timeout", this);
            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_floor_cycles", budget);
            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_factor", 0);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (run_timeout == null) return;
            run_timeout.clk_vif = clk_vif;
            run_timeout.clock   = "clk";
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    clk_vif.wait_reset_release();
                    released_at = $realtime;
                end
            join_none
            super.run_phase(phase);
        endtask

        // When the last handshake on rv_in or rv_out was sampled.
        protected function realtime last_handshake();
            realtime t = 0;
            if (in_seen.at.size() != 0) t = in_seen.at[$];
            if (out_seen.at.size() != 0 && out_seen.at[$] > t) t = out_seen.at[$];
            return t;
        endfunction

        // The longest run of clocks between two handshakes on rv_in or
        // rv_out, the last one included.
        protected function int unsigned longest_gap();
            realtime t[$];
            realtime most = 0;
            foreach (in_seen.at[i]) t.push_back(in_seen.at[i]);
            foreach (out_seen.at[i]) t.push_back(out_seen.at[i]);
            t.sort();
            for (int i = 1; i < t.size(); i++) if (t[i] - t[i - 1] > most) most = t[i] - t[i - 1];
            return int'(most / 10ns);
        endfunction

        protected function void expect_timeout_at(realtime want);
            realtime got = demoter.first_at("A2C_RUN_TIMEOUT");
            if (got != want) `uvm_error("LB_JS", $sformatf("A2C_RUN_TIMEOUT came at %0t, expected %0t", got, want))
        endfunction

        // From check_phase: the stall ended the run in its own time step,
        // through the run timeout, whose own error never came, and its
        // message says the run ends there.
        protected function void expect_ended_at_stall();
            realtime stall = demoter.first_at("A2C_JOINT_STALL");
            if ($realtime != stall) `uvm_error("LB_JS", $sformatf("check_phase ran at %0t, not at the stall at %0t", $realtime, stall))
            if (demoter.count("A2C_JOINT_STALL", UVM_ERROR, LB_JS_MODE_A_END) != 1) `uvm_error("LB_JS", $sformatf("the A2C_JOINT_STALL does not end '%s': %p", LB_JS_MODE_A_END, demoter.msgs))
            if (a2c_run_ended_by != "the joint stall rule" || a2c_run_ended_id != "A2C_JOINT_STALL" || a2c_run_ended_at != stall) begin
                `uvm_error("LB_JS", $sformatf("the run's end is recorded as %s (%s) at %0t", a2c_run_ended_by, a2c_run_ended_id, a2c_run_ended_at))
            end
        endfunction

        // Whether src's master waits now and its watchdog counts no rule.
        protected function void expect_waiting_uncounted();
            int unsigned left;
            string       rule = src.drv.wd.counting(left);
            if (!src.drv.wd.waiting_now()) `uvm_error("LB_JS", "rv_in's master does not wait at the end of the run")
            if (rule != "") `uvm_error("LB_JS", $sformatf("rv_in's watchdog counts the %s with %0d clocks left", rule, left))
        endfunction
    endclass : lb_js_rv_base

    // The pipe stops taking input once it holds 4 beats: one A2C_JOINT_STALL
    // joint + 1 clocks after the last handshake, naming rv_in's master and
    // its item. The test has no run timeout, so the run goes on: the master
    // goes on waiting, and in the 2 bounds after the stall raises no second
    // one.
    class js_rv_stop_test extends lb_js_rv_base;
        `uvm_component_utils(js_rv_stop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_js();
            stop_pipe(LB_RT_RV);
            max_clocks = 3 * joint + 200;
            want["A2C_JOINT_STALL"] = 1;
        endfunction

        virtual function void check();
            string head = $sformatf("rv_in: no port has made a handshake on any lane for %0d of this port's clocks (joint_stall_cycles, +a2c_joint_stall_cycles), while lanes waited on these ports: rv_in (uvm_test_top.src.drv), waiting for the transfer of ",
                                    joint);
            expect_at("A2C_JOINT_STALL", last_handshake() + (joint + 1) * 10ns);
            if (demoter.count("A2C_JOINT_STALL", UVM_ERROR, head) != 1) `uvm_error("LB_JS", $sformatf("no A2C_JOINT_STALL reads '%s': %p", head, demoter.msgs))
            if (demoter.count("A2C_JOINT_STALL", UVM_ERROR, LB_JS_MODE_A_WAIT) != 1) `uvm_error("LB_JS", $sformatf("the A2C_JOINT_STALL does not end '%s': %p", LB_JS_MODE_A_WAIT, demoter.msgs))
            if (clocks < max_clocks) `uvm_error("LB_JS", $sformatf("the run ended after %0d clocks, before the 2 bounds after the stall", clocks))
            expect_waiting_uncounted();
        endfunction
    endclass : js_rv_stop_test

    // The pipe is slow, 1 beat in 4 clocks, and stalls once for as long as
    // the bound allows: the longest run between handshakes is joint clocks,
    // one short of a stall, and nothing fires. Handshakes on either side
    // of the pipe's output stall are stall_len - 1 clocks apart, so
    // joint + 1 gives the gap of joint.
    class js_rv_slow_test extends lb_js_rv_base;
        `uvm_component_utils(js_rv_slow_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_js();
            lb_rt_pipe_cfg[LB_RT_RV].emit_n      = 1;
            lb_rt_pipe_cfg[LB_RT_RV].emit_m      = 4;
            lb_rt_pipe_cfg[LB_RT_RV].depth       = 4;
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 20;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = joint + 1;
        endfunction

        virtual function void check();
            if (out_seen.items.size() != 64) `uvm_error("LB_JS", $sformatf("%0d beats out, expected 64", out_seen.items.size()))
            if (longest_gap() != joint) `uvm_error("LB_JS", $sformatf("the longest run between handshakes is %0d clocks, expected the bound's %0d", longest_gap(), joint))
        endfunction
    endclass : js_rv_slow_test

    // The rv pipe stalls for 3 bounds while the axis pipe streams beside
    // it: rv_in's master waits that long, but a port moves, so nothing
    // fires.
    class js_rv_moving_test extends lb_js_rv_base;
        axis_agent_t              axsrc;
        axis_agent_t              axdst;
        lb_arrivals#(axis_item_t) ax_seen;

        `uvm_component_utils(js_rv_moving_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_js();
            axis_config_t ax_in  = axis_config_t::type_id::create("ax_in");
            axis_config_t ax_out = axis_config_t::type_id::create("ax_out");
            lb_rt_pipe_cfg[LB_RT_RV].stall_after = 20;
            lb_rt_pipe_cfg[LB_RT_RV].stall_len   = 3 * joint;
            lb_rt_pipe_cfg[LB_RT_RV].depth       = 4;
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis_in", ax_in.vif)) `uvm_fatal("LB_CFG", "no interface axis_in")
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis_out", ax_out.vif)) `uvm_fatal("LB_CFG", "no interface axis_out")
            ax_in.clk_vif    = clk_vif;
            ax_in.role       = A2C_SRC;
            ax_in.port_name  = "axis_in";
            ax_out.clk_vif   = clk_vif;
            ax_out.role      = A2C_DST;
            ax_out.port_name = "axis_out";
            uvm_config_db#(axis_config_t)::set(this, "axsrc", "cfg", ax_in);
            uvm_config_db#(axis_config_t)::set(this, "axdst", "cfg", ax_out);
            axsrc   = axis_agent_t::type_id::create("axsrc", this);
            axdst   = axis_agent_t::type_id::create("axdst", this);
            ax_seen = lb_arrivals#(axis_item_t)::type_id::create("ax_seen", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            axdst.mon.ap.connect(ax_seen.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_list_seq#(axis_item_t) ax_seq = lb_list_seq#(axis_item_t)::type_id::create("ax_seq");
            for (int unsigned i = 0; i < 2000; i++) begin
                axis_item_t it = axis_item_t::type_id::create("it");
                if (!it.randomize()) `uvm_fatal("LB_RAND", "axi4_stream item randomize failed")
                it.gap = 0;
                ax_seq.items.push_back(it);
            end
            fork
                begin
                    clk_vif.wait_reset_release();
                    ax_seq.start(axsrc.sqr);
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            realtime from = 0;
            realtime to = 0;
            int unsigned moved = 0;
            if (out_seen.items.size() != 64) `uvm_error("LB_JS", $sformatf("%0d beats out, expected 64", out_seen.items.size()))
            if (out_seen.at.size() > 20) begin
                from = out_seen.at[19];
                to   = out_seen.at[20];
            end
            foreach (ax_seen.at[i]) moved += ax_seen.at[i] > from && ax_seen.at[i] < to;
            if (to - from < 3 * joint * 10ns || moved < 3 * joint / 2) begin
                `uvm_error("LB_JS", $sformatf("rv_out paused from %0t to %0t with %0d axis beats meanwhile: not a long wait beside a moving port", from, to, moved))
            end
        endfunction
    endclass : js_rv_moving_test

    // rv_in's pipe and axis_in's both stop. rv_in's master, with the lower
    // bound, raises the one A2C_JOINT_STALL and names both ports, and the
    // stall ends the run there, before the budget of 600: no deferral and
    // no A2C_RUN_TIMEOUT.
    class js_rv_two_ports_test extends js_rv_moving_test;
        `uvm_component_utils(js_rv_two_ports_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            budget = 600;
        endfunction

        virtual function void configure_js();
            super.configure_js();
            stop_pipe(LB_RT_RV);
            stop_pipe(LB_RT_AXIS);
            uvm_config_db#(int unsigned)::set(this, "axsrc.drv", "a2c_joint_stall_cycles", 1000);
            max_clocks = 1000000;
            want["A2C_JOINT_STALL"] = 1;
        endfunction

        virtual function void check();
            if (demoter.count("A2C_JOINT_STALL", UVM_ERROR, "rv_in (uvm_test_top.src.drv), waiting for the transfer of ") != 1
                || demoter.count("A2C_JOINT_STALL", UVM_ERROR, "axis_in (uvm_test_top.axsrc.drv), waiting for the transfer of ") != 1) begin
                `uvm_error("LB_JS", $sformatf("the stall does not name both waiting ports: %p", demoter.msgs))
            end
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_INFO, "defers to them") != 0) `uvm_error("LB_JS", $sformatf("the timeout deferred after the stall: %p", demoter.msgs))
            expect_ended_at_stall();
        endfunction
    endclass : js_rv_two_ports_test

    // All 64 beats go through, and then nothing moves and rv_in's master
    // holds no item until the run timeout at 1200 clocks, over three
    // bounds after the last beat: no stall, and nothing for the timeout to
    // defer to.
    class js_rv_idle_test extends lb_js_rv_base;
        `uvm_component_utils(js_rv_idle_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            budget = 1200;
        endfunction

        virtual function void configure_js();
            lb_rt_pipe_cfg[LB_RT_RV].depth = 1;
            drain = 1000000;
            want["A2C_RUN_TIMEOUT"] = 1;
        endfunction

        virtual function void check();
            if (out_seen.items.size() != 64) `uvm_error("LB_JS", $sformatf("%0d beats out, expected 64", out_seen.items.size()))
            if (released_at + budget * 10ns - last_handshake() < 3 * joint * 10ns) begin
                `uvm_error("LB_JS", $sformatf("the last handshake at %0t leaves under 3 bounds of idle before the timeout", last_handshake()))
            end
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_INFO, "defers to them") != 0) `uvm_error("LB_JS", $sformatf("the timeout deferred on an idle run: %p", demoter.msgs))
            expect_timeout_at(released_at + budget * 10ns);
        endfunction
    endclass : js_rv_idle_test

    // js_rv_stop_test with the bound at 0: nothing fires, and the master
    // waits to the end with no rule counting.
    class js_rv_off_test extends lb_js_rv_base;
        `uvm_component_utils(js_rv_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_js();
            stop_pipe(LB_RT_RV);
            joint      = 0;
            max_clocks = 1000;
        endfunction

        virtual function void check();
            if (last_handshake() > released_at + 200 * 10ns) `uvm_error("LB_JS", $sformatf("the last handshake came at %0t, too late for a long wait", last_handshake()))
            expect_waiting_uncounted();
        endfunction
    endclass : js_rv_off_test

    // The pipe stops, with a bound of 400 that runs past the budget of 300:
    // the run timeout defers to the joint stall rule, which reports first
    // and ends the run, so the timeout never expires.
    class js_rv_defer_test extends lb_js_rv_base;
        `uvm_component_utils(js_rv_defer_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            budget = 300;
            joint  = 400;
        endfunction

        virtual function void configure_js();
            stop_pipe(LB_RT_RV);
            max_clocks = 1000000;
            want["A2C_JOINT_STALL"] = 1;
        endfunction

        virtual function void check();
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_INFO, "the joint stall rule (joint_stall_cycles) of rv_in (uvm_test_top.src.drv)") != 1) begin
                `uvm_error("LB_JS", $sformatf("the deferral does not name the joint stall rule: %p", demoter.msgs))
            end
            expect_at("A2C_JOINT_STALL", last_handshake() + (joint + 1) * 10ns);
            expect_ended_at_stall();
        endfunction
    endclass : js_rv_defer_test

    // rv_in's master and the pipe's input on clk3, which stops at clock 150
    // of clk while the joint stall counts toward 400 clocks of clk3, with a
    // clock stop of 20: at the budget of 300 the run timeout leaves the
    // rule out, names it, and expires without a deferral. The rule never
    // fires.
    class js_rv_stopped_test extends lb_js_rv_base;
        virtual a2c_clk_if clk3_vif;

        `uvm_component_utils(js_rv_stopped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            budget = 300;
            joint  = 400;
        endfunction

        virtual function void configure_js();
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            stop_pipe(LB_RT_RV);
            lb_rt_rv_in_clk3 = 1;
            src_cfg.clk_vif  = clk3_vif;
            uvm_config_db#(int unsigned)::set(this, "src.drv", "a2c_clock_stop_cycles", 20);
            max_clocks = 1000000;
            want["A2C_RUN_TIMEOUT"] = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    clk_vif.wait_reset_release();
                    repeat (150) clk_vif.sample_edge();
                    lb_clk3_run = 0;
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual function void check();
            string left = "Left out, clock stopped: the joint stall rule (joint_stall_cycles) of rv_in (uvm_test_top.src.drv)";
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_ERROR, left) != 1) `uvm_error("LB_JS", $sformatf("the timeout does not leave out the stopped rule: %p", demoter.msgs))
            if (demoter.count("A2C_RUN_TIMEOUT", UVM_INFO, "defers to them") != 0) `uvm_error("LB_JS", $sformatf("the timeout deferred to a stopped rule: %p", demoter.msgs))
            if (in_seen.items.size() != 24) `uvm_error("LB_JS", $sformatf("%0d beats in, expected the 24 the pipe takes", in_seen.items.size()))
            expect_timeout_at(released_at + budget * 10ns);
        endfunction
    endclass : js_rv_stopped_test

    // An AXI read master whose slave takes the AR and never returns R: the
    // burst is outstanding with nothing on the bus, so the master still
    // holds it, and one A2C_JOINT_STALL comes joint + 1 clocks after the AR
    // transfer, naming the R beats the master waits for. The test has no
    // run timeout, so the master goes on waiting, and at the end both
    // monitors report the open burst as A2C_PROTO.
    class js_axi_read_test extends axr_pair_test;
        int unsigned  joint = 200;
        lb_rt_demoter demoter;
        realtime      ar_at = -1;

        `uvm_component_utils(js_axi_read_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axr_config_t master_cfg, axr_config_t slave_cfg);
            slave_cfg.resp_delay_min = 1000000;
            slave_cfg.resp_delay_max = 1000000;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            demoter = lb_rt_demoter::type_id::create("demoter");
            demoter.also.push_back("A2C_JOINT_STALL");
            demoter.also.push_back("A2C_PROTO");
            uvm_report_cb::add(null, demoter);
            uvm_config_db#(int unsigned)::set(this, "master.drv", "a2c_joint_stall_cycles", joint);
        endfunction

        virtual task run_phase(uvm_phase phase);
            axr_seq seq = axr_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n            = 1;
            seq.mem          = slave_cfg.mem;
            seq.error_ranges = slave_cfg.error_ranges;
            clk_vif.wait_reset_release();
            fork
                seq.start(master.sqr);
                forever begin
                    clk_vif.sample_edge();
                    if (vif.arvalid === 1'b1 && vif.arready === 1'b1) ar_at = $realtime;
                end
            join_none
            repeat (3 * joint) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            string head = $sformatf("axr: no port has made a handshake on any lane for %0d of this port's clocks (joint_stall_cycles, +a2c_joint_stall_cycles), while lanes waited on these ports: axr (uvm_test_top.master.drv), waiting for the R beats of ",
                                    joint);
            super.check_phase(phase);
            if (demoter.count("A2C_JOINT_STALL", UVM_ERROR, head) != 1 || demoter.count("A2C_JOINT_STALL", UVM_ERROR, LB_JS_MODE_A_WAIT) != 1
                || demoter.count("A2C_PROTO", UVM_ERROR, "the run ended with 1 bursts still waiting for their last beat") != 2 || demoter.errors() != 3) begin
                `uvm_error("LB_JS", $sformatf("expected one A2C_JOINT_STALL reading '%s', and the master's and slave's monitors each reporting the open burst at the end: %p", head, demoter.msgs))
            end
            if (ar_at < 0 || demoter.first_at("A2C_JOINT_STALL") != ar_at + (joint + 1) * 10ns) begin
                `uvm_error("LB_JS", $sformatf("the A2C_JOINT_STALL came at %0t, the AR transfer at %0t", demoter.first_at("A2C_JOINT_STALL"), ar_at))
            end
        endfunction
    endclass : js_axi_read_test

    // js_axi_read_test for an AXI write master whose slave takes the AW and
    // every W beat and never returns B: the stall comes joint + 1 clocks
    // after the last W beat, naming the B the master waits for.
    class js_axi_write_test extends axw_pair_test;
        int unsigned  joint = 200;
        lb_rt_demoter demoter;
        realtime      last_at = -1;

        `uvm_component_utils(js_axi_write_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axw_config_t master_cfg, axw_config_t slave_cfg);
            slave_cfg.resp_delay_min = 1000000;
            slave_cfg.resp_delay_max = 1000000;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            demoter = lb_rt_demoter::type_id::create("demoter");
            demoter.also.push_back("A2C_JOINT_STALL");
            demoter.also.push_back("A2C_PROTO");
            uvm_report_cb::add(null, demoter);
            uvm_config_db#(int unsigned)::set(this, "master.drv", "a2c_joint_stall_cycles", joint);
        endfunction

        virtual task run_phase(uvm_phase phase);
            axw_seq seq = axw_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n     = 1;
            seq.model = new();
            clk_vif.wait_reset_release();
            fork
                seq.start(master.sqr);
                forever begin
                    clk_vif.sample_edge();
                    if ((vif.awvalid === 1'b1 && vif.awready === 1'b1) || (vif.wvalid === 1'b1 && vif.wready === 1'b1)) last_at = $realtime;
                end
            join_none
            repeat (3 * joint + 300) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            string head = $sformatf("axw: no port has made a handshake on any lane for %0d of this port's clocks (joint_stall_cycles, +a2c_joint_stall_cycles), while lanes waited on these ports: axw (uvm_test_top.master.drv), waiting for the B of ",
                                    joint);
            super.check_phase(phase);
            if (demoter.count("A2C_JOINT_STALL", UVM_ERROR, head) != 1 || demoter.count("A2C_JOINT_STALL", UVM_ERROR, LB_JS_MODE_A_WAIT) != 1
                || demoter.count("A2C_PROTO", UVM_ERROR, "1 bursts waiting for B") != 2 || demoter.errors() != 3) begin
                `uvm_error("LB_JS", $sformatf("expected one A2C_JOINT_STALL reading '%s', and the master's and slave's monitors each reporting the open burst at the end: %p", head, demoter.msgs))
            end
            if (last_at < 0 || demoter.first_at("A2C_JOINT_STALL") != last_at + (joint + 1) * 10ns) begin
                `uvm_error("LB_JS", $sformatf("the A2C_JOINT_STALL came at %0t, the last W beat at %0t", demoter.first_at("A2C_JOINT_STALL"), last_at))
            end
        endfunction
    endclass : js_axi_write_test
