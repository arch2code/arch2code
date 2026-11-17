// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain
// GENERATED_CODE_BEGIN --template=uvmTest --section=header

`ifndef UVMREUSECHAIN_UVM_TEST_PKG_SV
`define UVMREUSECHAIN_UVM_TEST_PKG_SV

`ifndef A2C_UVM_PKG
`define A2C_UVM_PKG A2C_UVM_PKG_is_not_defined__define_it_as_the_variant_uvm_package
`endif

package uvmReuseChain_uvm_test_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;
    import rdy_vld_uvm_pkg::*;
    import apb_uvm_pkg::*;
    import push_ack_uvm_pkg::*;
    // Generated Import package statement(s)
    import uvmReuse_package::*;
    import uvmReuseLeaf_package::*;
    import `A2C_UVM_PKG::*;

// GENERATED_CODE_END
    import a2c_video_pkg::*;
    `include "uvm/a2c_video_macros.svh"

    // Sequences and scoreboard classes go here; the env below instantiates
    // the scoreboards.
    class uvmReuseChain_tb_env extends uvmReuseChain_env;
        `uvm_component_utils(uvmReuseChain_tb_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass : uvmReuseChain_tb_env

// GENERATED_CODE_BEGIN --template=uvmTest --section=tests

    // Waits for reset, runs run_body(), then waits for every output's
    // expected transactions. A test sets its own default deadline, quiet
    // window and clock stop in its constructor; +a2c_output_deadline_cycles,
    // +a2c_quiet_cycles and +a2c_clock_stop_cycles override them. A clock
    // with no edge for clock_stop_cycles of its periods has stopped. In
    // Mode B the drain at the end of the run phase has its own window,
    // deadline and catch-up after a cut, which a test may set in its
    // constructor too, and +a2c_drain_quiet_cycles,
    // +a2c_drain_deadline_cycles and +a2c_drain_catchup_cycles override.
    // Left at -1, the window and deadline take quiet_cycles and
    // output_deadline_cycles, and the catch-up takes each replay log's
    // deadline. +a2c_drain_cut_expected=1 reports the drain's cuts as
    // UVM_INFO. A master in Mode B declares a lane dead when it trails
    // the other by lane_skew_cycles clocks, and the other lane dead too
    // when, left alone, it makes no progress for lone_lane_cycles
    // clocks. In either mode a master that holds an item while no port
    // makes a handshake for joint_stall_cycles clocks raises one
    // A2C_JOINT_STALL. In Mode B the masters then declare every live
    // lane dead, and in Mode A the run ends there, as at the run
    // timeout. Left at -1 each keeps the master's own
    // 200000, +a2c_lane_skew_cycles, +a2c_lone_lane_cycles and
    // +a2c_joint_stall_cycles override them, and 0 turns a rule off. A
    // Mode B master that holds its next item back for the model lane,
    // with the DUT lane ready for it, for model_throttle_cycles clocks in a
    // row raises A2C_MODEL_THROTTLE; left at -1 it keeps the master's
    // own bound, +a2c_model_throttle_cycles overrides it, and 0 turns the
    // rule off. A run that sends nothing on an input and expects no output
    // transaction warns at check_phase, unless no_stimulus_expected
    // (+a2c_no_stimulus_expected=1) is set. A run phase still running at
    // its run timeout, counted in clocks of clk, ends with one
    // A2C_RUN_TIMEOUT error naming the ports that wait and the objections
    // raised, and check_phase still runs. Left at -1, the timeout is
    // run_timeout_floor_cycles plus run_timeout_factor times the work the
    // test has declared, each knob left at -1 taking a2c_run_timeout's
    // default, and a progress rule counting at that point may report
    // first; run_timeout_cycles above 0 fixes it and 0 turns it off, as
    // does run_timeout.fix(), from any phase.
    // +a2c_run_timeout_cycles, +a2c_run_timeout_floor_cycles and
    // +a2c_run_timeout_factor override them. rt_gap_cycles,
    // rt_latency_cycles, rt_lag_cycles, rt_refusal_cycles and
    // rt_on_model set the real-time rules of every a2c_rt_checker the
    // env holds; left at -1 each keeps the checker's own, and
    // +a2c_rt_gap_cycles, +a2c_rt_latency_cycles, +a2c_rt_lag_cycles,
    // +a2c_rt_refusal_cycles and +a2c_rt_on_model override them. With
    // expect_from_model (+a2c_expect_from_model=1) set, an output needs no
    // expect_count(): in Mode B the model lane's count is the DUT lane's
    // expectation, and wait_for_outputs() returns once the outputs have
    // been quiet for quiet_cycles. reset_dut() pulses the resets mid-run.
    class uvmReuseChain_base_test extends uvm_test implements a2c_run_work;
        uvmReuseChain_tb_env env;
        int unsigned output_deadline_cycles = 200000;
        int unsigned quiet_cycles = 1000;
        int unsigned clock_stop_cycles = 1000;
        int          drain_quiet_cycles = -1;
        int          drain_deadline_cycles = -1;
        int          drain_catchup_cycles = -1;
        bit          drain_cut_expected;
        int          lane_skew_cycles = -1;
        int          lone_lane_cycles = -1;
        int          joint_stall_cycles = -1;
        int          model_throttle_cycles = -1;
        bit          no_stimulus_expected;
        bit          expect_from_model;
        int          run_timeout_cycles = -1;
        int          run_timeout_floor_cycles = -1;
        int          run_timeout_factor = -1;
        int          rt_gap_cycles = -1;
        int          rt_latency_cycles = -1;
        int          rt_lag_cycles = -1;
        int          rt_refusal_cycles = -1;
        int          rt_on_model = -1;
        a2c_run_timeout run_timeout;

        `uvm_component_utils(uvmReuseChain_base_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            void'($value$plusargs("a2c_output_deadline_cycles=%d", output_deadline_cycles));
            void'($value$plusargs("a2c_quiet_cycles=%d", quiet_cycles));
            void'($value$plusargs("a2c_clock_stop_cycles=%d", clock_stop_cycles));
            if (drain_quiet_cycles < 0) drain_quiet_cycles = quiet_cycles;
            if (drain_deadline_cycles < 0) drain_deadline_cycles = output_deadline_cycles;
            void'($value$plusargs("a2c_drain_quiet_cycles=%d", drain_quiet_cycles));
            void'($value$plusargs("a2c_drain_deadline_cycles=%d", drain_deadline_cycles));
            void'($value$plusargs("a2c_drain_catchup_cycles=%d", drain_catchup_cycles));
            void'($value$plusargs("a2c_drain_cut_expected=%d", drain_cut_expected));
            void'($value$plusargs("a2c_lane_skew_cycles=%d", lane_skew_cycles));
            void'($value$plusargs("a2c_lone_lane_cycles=%d", lone_lane_cycles));
            void'($value$plusargs("a2c_joint_stall_cycles=%d", joint_stall_cycles));
            void'($value$plusargs("a2c_model_throttle_cycles=%d", model_throttle_cycles));
            void'($value$plusargs("a2c_no_stimulus_expected=%d", no_stimulus_expected));
            void'($value$plusargs("a2c_expect_from_model=%d", expect_from_model));
            void'($value$plusargs("a2c_run_timeout_cycles=%d", run_timeout_cycles));
            void'($value$plusargs("a2c_run_timeout_floor_cycles=%d", run_timeout_floor_cycles));
            void'($value$plusargs("a2c_run_timeout_factor=%d", run_timeout_factor));
            void'($value$plusargs("a2c_rt_gap_cycles=%d", rt_gap_cycles));
            void'($value$plusargs("a2c_rt_latency_cycles=%d", rt_latency_cycles));
            void'($value$plusargs("a2c_rt_lag_cycles=%d", rt_lag_cycles));
            void'($value$plusargs("a2c_rt_refusal_cycles=%d", rt_refusal_cycles));
            void'($value$plusargs("a2c_rt_on_model=%d", rt_on_model));
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_clock_stop_cycles", clock_stop_cycles);
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_quiet_cycles", drain_quiet_cycles);
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_deadline_cycles", drain_deadline_cycles);
            if (drain_catchup_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_catchup_cycles", drain_catchup_cycles);
            end
            uvm_config_db#(bit)::set(this, "env*", "a2c_drain_cut_expected", drain_cut_expected);
            uvm_config_db#(bit)::set(this, "env*", "a2c_expect_from_model", expect_from_model);
            if (lane_skew_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_lane_skew_cycles", lane_skew_cycles);
            end
            if (lone_lane_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_lone_lane_cycles", lone_lane_cycles);
            end
            if (joint_stall_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_joint_stall_cycles", joint_stall_cycles);
            end
            if (model_throttle_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_model_throttle_cycles", model_throttle_cycles);
            end
            if (run_timeout_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_cycles", run_timeout_cycles);
            end
            if (run_timeout_floor_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_floor_cycles", run_timeout_floor_cycles);
            end
            if (run_timeout_factor >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_factor", run_timeout_factor);
            end
            if (rt_gap_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_rt_gap_cycles", rt_gap_cycles);
            end
            if (rt_latency_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_rt_latency_cycles", rt_latency_cycles);
            end
            if (rt_lag_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_rt_lag_cycles", rt_lag_cycles);
            end
            if (rt_refusal_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_rt_refusal_cycles", rt_refusal_cycles);
            end
            if (rt_on_model >= 0) begin
                uvm_config_db#(bit)::set(this, "env*", "a2c_rt_on_model", rt_on_model != 0);
            end
            env = uvmReuseChain_tb_env::type_id::create("env", this);
            run_timeout = a2c_run_timeout::type_id::create("run_timeout", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            run_timeout.clk_vif = env.clk_vif;
            run_timeout.clock   = "clk";
            run_timeout.work    = this;
        endfunction

        virtual function void start_of_simulation_phase(uvm_phase phase);
            super.start_of_simulation_phase(phase);
            a2c_rerun::start();
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            env.clk_vif.wait_reset_release();
            env.clkAux_vif.wait_reset_release();
            run_body();
            wait_for_outputs();
            phase.drop_objection(this);
        endtask

        virtual task run_body();
        endtask

        // Each output waits on its own clock. A test may call this between
        // frames too. In Mode B its return is a stable point for the model
        // comparators.
        task wait_for_outputs();
            fork
                env.out_counter.wait_for_count(env.clk_vif, output_deadline_cycles, quiet_cycles);
            join
            if (env.dual_dut) begin
                env.model_stable_point();
            end
        endtask

        // Pulses every reset of the block and returns once each clock samples
        // its reset released. The RTL and the agents abandon what is in
        // flight, and the counters and comparators start again from the
        // release. The model has no mid-run reset, so a run that holds it
        // gets an A2C_RESET error instead.
        task reset_dut();
            bit model;
            void'(uvm_config_db#(bit)::get(this, "env", "a2c_model_dut", model));
            if (model || env.dual_dut) begin
                `uvm_error("A2C_RESET", "reset_dut(): the run holds the SystemC model, which cannot be reset mid-run; reset only with --uvmDut rtl")
                return;
            end
            fork
                env.clk_vif.request_reset();
                env.clkAux_vif.request_reset();
            join
        endtask

        // Warns about a run that sent nothing on any input and declared no
        // transaction on any output, as the scaffolded smoke test does until
        // its run_body() sends stimulus. A Mode B comparator or a check of the
        // test's own may still have run, so the warning claims no more.
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (no_stimulus_expected || stimulus_sent() != 0) return;
            if (env.out_counter.declared() != 0) return;
            `uvm_warning("A2C_NO_STIMULUS", $sformatf("%s sent no transaction on any input and declared no transaction on any output. Send stimulus in run_body(), through the input agents' sequencers or a status input's cfg.value, and declare each output's transactions with expect_count() on its counter, or set no_stimulus_expected (+a2c_no_stimulus_expected=1) in a test meant to send nothing",
                                                      get_type_name()))
        endfunction

        // The items the input ports' agents have sent, through their
        // sequencers or, for a status input, their drivers.
        virtual function int unsigned stimulus_sent();
            int unsigned n = 0;
            n += a2c_items_sent#(in_item_t)::of(env.in_agent);
            n += a2c_items_sent#(apbReg_item_t)::of(env.apbReg_agent);
            return n;
        endfunction

        // The transactions the output counters expect.
        virtual function int unsigned outputs_declared();
            int unsigned n = 0;
            n += env.out_counter.declared();
            return n;
        endfunction
    endclass : uvmReuseChain_base_test

// GENERATED_CODE_END

    // uLeafA is the leaf's w8 variant in both tops, so its register block is
    // that package's class and the package's configuration sequence programs
    // it. uLeafB's block is this package's own class, written directly. out
    // takes the chain of both leaves' contracts; with an RTL DUT the internal
    // connection mid takes uLeafA's alone, so a defect fails first at the
    // leaf that makes it.
    class uvmReuseChain_video_test extends a2c_video_test #(uvmReuseChain_base_test);
        uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_video_contract leaf_a, leaf_b;
        a2c_video_contract_chain out_chain, mid_chain;
        bit internal;

        `uvm_component_utils(uvmReuseChain_video_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void video_ports();
            a2c_video_output #(mid_item_t) mid;
            bit model_dut;
            void'(uvm_config_db#(bit)::get(this, "env", "a2c_model_dut", model_dut));
            internal  = !model_dut;
            leaf_a    = uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_video_contract::type_id::create("leaf_a");
            leaf_b    = uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_video_contract::type_id::create("leaf_b");
            out_chain = a2c_video_contract_chain::type_id::create("out_chain");
            out_chain.add_stage(leaf_a);
            out_chain.add_stage(leaf_b);
            mid_chain = a2c_video_contract_chain::type_id::create("mid_chain");
            mid_chain.add_stage(leaf_a);
            add_video_input(a2c_video_input#(in_item_t)::make("in", uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_video_adapter#(in_item_t)::type_id::create("in_adapter")));
            if (internal) begin
                mid = a2c_video_output#(mid_item_t)::make("mid", uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_video_adapter#(mid_item_t)::type_id::create("mid_adapter"),
                                                          mid_chain);
                mid.dut_lane_only = 1;
                add_video_output(mid);
            end
            add_video_output(a2c_video_output#(out_item_t)::make("out", uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_video_adapter#(out_item_t)::type_id::create("out_adapter"),
                                                                 out_chain));
        endfunction

        virtual function void video_connect();
            leaf_a.offset = env.regmodel.uLeafA.offset;
            leaf_b.offset = env.regmodel.uLeafB.offset;
            connect_video_input(env.in_agent);
            if (internal) connect_video_output("mid", env.mid_agent);
            connect_video_output("out", env.out_agent, env.out_counter);
        endfunction

        virtual task configure_dut(a2c_video_cfg cfg);
            uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_config_seq seq = uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_config_seq::type_id::create("config_seq");
            uvm_status_e status;
            seq.offset = $urandom_range((1 << env.regmodel.uLeafA.offset.get_n_bits()) - 1);
            seq.model  = env.regmodel.uLeafA;
            seq.start(null);
            env.regmodel.uLeafB.offset.write(status, $urandom_range((1 << env.regmodel.uLeafB.offset.get_n_bits()) - 1));
            env.regmodel.uLeafB.offset.mirror(status, UVM_CHECK);
        endtask
    endclass : uvmReuseChain_video_test

    `a2c_video_corner_tests(uvmReuseChain_video_test)

    class uvmReuseChain_smoke_test extends uvmReuseChain_video_test;
        `uvm_component_utils(uvmReuseChain_smoke_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass : uvmReuseChain_smoke_test

    // Counts the transfers on ticks and when the last one was seen.
    class uvmReuseChain_tick_counter extends uvm_subscriber #(ticks_item_t);
        int unsigned seen;
        realtime     last_at;

        `uvm_component_utils(uvmReuseChain_tick_counter)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void write(ticks_item_t t);
            seen++;
            last_at = $realtime;
        endfunction
    endclass : uvmReuseChain_tick_counter

    // Records when the first A2C_JOINT_STALL was reported, at any severity.
    class uvmReuseChain_stall_clock extends uvm_report_catcher;
        realtime at;
        bit      seen;

        `uvm_object_utils(uvmReuseChain_stall_clock)

        function new(string name = "uvmReuseChain_stall_clock");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_id() == "A2C_JOINT_STALL" && !seen) begin
                seen = 1;
                at   = $realtime;
            end
            return THROW;
        endfunction
    endclass : uvmReuseChain_stall_clock

    // RTL DUT only. out is never ready, so the boundary deadlocks while uTick
    // and uTock go on handshaking on ticks, which the env watches. The test
    // passes only if the joint stall rule still fires, which it would not if
    // the internal monitor's transfers counted as progress, and ticks moved
    // within stall_tick_window of it. The stall ends the run phase with
    // nothing delivered, so out's counter and the mid and out checkers each
    // report it once too.
    class uvmReuseChain_stall_test extends uvmReuseChain_video_test;
        a2c_expected_error         stall, missing;
        // The video checkers report at check_phase after an
        // a2c_expected_error would have counted, so report_phase counts these.
        a2c_error_demoter          frames;
        uvmReuseChain_tick_counter ticks;
        uvmReuseChain_stall_clock  stall_clock;
        realtime                   stall_tick_window = 20ns;

        `uvm_component_utils(uvmReuseChain_stall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            joint_stall_cycles = 300;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            stall    = a2c_expected_error::type_id::create("stall", this);
            stall.id = "A2C_JOINT_STALL";
            missing  = a2c_expected_error::type_id::create("missing", this);
            missing.id = "A2C_TXN_COUNT";
            frames   = a2c_error_demoter::type_id::create("frames");
            frames.demote_id   = "A2C_VIDEO";
            frames.demote_text = "expected frames never came out";
            uvm_report_cb::add(null, frames);
            ticks    = uvmReuseChain_tick_counter::type_id::create("ticks", this);
            stall_clock = uvmReuseChain_stall_clock::type_id::create("stall_clock");
            uvm_report_cb::add(null, stall_clock);
            uvm_config_db#(bit)::set(this, "env*", "a2c_rt_off", 1'b1);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (env.ticks_agent == null) begin
                `uvm_fatal("A2C_CFG", "uvmReuseChain_stall_test needs the RTL DUT, whose ticks connection the env watches")
            end
            env.ticks_agent.mon.ap.connect(ticks.analysis_export);
        endfunction

        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            env.out_agent.cfg.ready_pct = 0;
        endfunction

        virtual function void report_phase(uvm_phase phase);
            super.report_phase(phase);
            if (frames.demoted != 2) begin
                `uvm_error("A2C_STALL_TEST", $sformatf("expected the mid and out checkers each to report missing frames once; caught %0d",
                                                       frames.demoted))
            end
            // A missing stall is the expected error's to report.
            if (!stall_clock.seen) return;
            if (ticks.seen == 0 || stall_clock.at - ticks.last_at > stall_tick_window) begin
                `uvm_error("A2C_STALL_TEST", $sformatf("ticks saw %0d transfers, the last at %0t, but the joint stall came at %0t: the internal connection did not run through the stall",
                                                       ticks.seen, ticks.last_at, stall_clock.at))
            end
        endfunction
    endclass : uvmReuseChain_stall_test


// GENERATED_CODE_BEGIN --template=uvmTest --section=footer

    // The smoke test with more transactions expected on the first output than
    // the DUT delivers (+a2c_fail_missing_count, default 1). It passes only if
    // the counter reported exactly one A2C_TXN_COUNT, one per lane in Mode B,
    // each lane ends missing exactly missing_count transactions, and nothing
    // else raised a UVM_ERROR or UVM_FATAL, so a counter that stops reporting
    // or reports the wrong shortfall fails it. The missing transaction never
    // closes its unit, so the real-time rules are off.
    // It also fails when the smoke test sent no stimulus, since the shortfall
    // alone would then pass with a dead data path.
    class uvmReuseChain_fail_test extends uvmReuseChain_smoke_test;
        a2c_error_demoter demoter;
        int unsigned missing_count = 1;

        `uvm_component_utils(uvmReuseChain_fail_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            void'($value$plusargs("a2c_fail_missing_count=%d", missing_count));
            demoter = a2c_error_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_TXN_COUNT";
            uvm_report_cb::add(null, demoter);
            // Wins over the rt_* knobs, plusargs and set_limits().
            uvm_config_db#(bit)::set(this, "env*", "a2c_rt_off", 1'b1);
        endfunction

        virtual task run_body();
            super.run_body();
            env.out_counter.expect_count(missing_count);
        endtask

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned others = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);
            int unsigned want = 1;
            string       expected = "one A2C_TXN_COUNT error";
            string       shortfall = "";
            super.report_phase(phase);
            if (env.dual_dut) begin
                want     = 2;
                expected = "one A2C_TXN_COUNT error per lane";
            end
            for (int lane = 0; lane < want; lane++) begin
                int unsigned pending = env.out_counter.lane_pending(a2c_lane_e'(lane));
                if (pending != missing_count) begin
                    shortfall = {shortfall, $sformatf("; the %s lane misses %0d, expected %0d", a2c_lane_name(a2c_lane_e'(lane)),
                                                      pending, missing_count)};
                end
            end
            if (stimulus_sent() == 0) begin
                `uvm_error("A2C_FAIL_TEST", "uvmReuseChain_smoke_test sent no stimulus, so the missing transactions would also be missing with a dead data path; send stimulus in its run_body()")
            end else if (demoter.demoted != want || others != 0 || shortfall != "") begin
                `uvm_error("A2C_FAIL_TEST", $sformatf("expected exactly %s and no other error; caught %0d A2C_TXN_COUNT, %0d other UVM_ERROR/UVM_FATAL%s",
                                                      expected, demoter.demoted, others, shortfall))
            end else begin
                `uvm_info("A2C_FAIL_TEST", "the transaction counter reported the missing transactions as intended", UVM_LOW)
            end
        endfunction
    endclass : uvmReuseChain_fail_test

    // The smoke test with a mismatch injected at pair +a2c_model_mismatch_at
    // (default 1) of the first counted output's model comparator. It runs
    // only in Mode B. Only the injected A2C_MODEL_CMP is demoted, so any
    // other mismatch stays an error. It passes only if that one report
    // arrived, the comparator compared at least mismatch_at pairs, and
    // nothing else raised a UVM_ERROR or UVM_FATAL.
    class uvmReuseChain_model_mismatch_test extends uvmReuseChain_smoke_test;
        a2c_error_demoter demoter;
        int unsigned mismatch_at = 1;

        `uvm_component_utils(uvmReuseChain_model_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            void'($value$plusargs("a2c_model_mismatch_at=%d", mismatch_at));
            demoter = a2c_error_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_MODEL_CMP";
            demoter.demote_text = "(injected mismatch)";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (!env.dual_dut) begin
                `uvm_fatal("A2C_CFG", "uvmReuseChain_model_mismatch_test compares the model DUT against the RTL and runs only on the both DUT")
            end
            env.out_agent.model_cmp.inject_mismatch(mismatch_at);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned others = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);
            int unsigned pairs = env.out_agent.model_cmp.get_pairs();
            super.report_phase(phase);
            if (demoter.demoted != 1 || others != 0 || pairs < mismatch_at) begin
                `uvm_error("A2C_MISMATCH_TEST", $sformatf("expected exactly one injected A2C_MODEL_CMP at pair %0d and no other error; caught %0d injected, %0d other UVM_ERROR/UVM_FATAL, %0d pairs compared",
                                                          mismatch_at, demoter.demoted, others, pairs))
            end else begin
                `uvm_info("A2C_MISMATCH_TEST", "the model comparator reported the injected mismatch as intended", UVM_LOW)
            end
        endfunction
    endclass : uvmReuseChain_model_mismatch_test

endpackage : uvmReuseChain_uvm_test_pkg

`endif // UVMREUSECHAIN_UVM_TEST_PKG_SV

// GENERATED_CODE_END
