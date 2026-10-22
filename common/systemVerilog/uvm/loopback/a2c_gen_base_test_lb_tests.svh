// A loopback run of the base test that templates/systemVerilog/uvmTest.py
// generates, so its handling of the drain knobs is simulated, not only
// read. The span between the RENDERED markers is render_tests() of that
// template for lb_gen_env, a stand-in for the generated env with no ports
// and one clock; unittest/test_uvm_test_pkg.py fails when the span and the
// template differ. Included in a2c_uvm_loopback_pkg after
// a2c_replay_drain_lb_tests.svh, whose fake lanes the env's replay log
// uses.

    // A component where a generated env puts an AXI agent's driver, so a
    // test can read the knobs that driver would.
    class lb_gen_scope extends uvm_component;
        `uvm_component_utils(lb_gen_scope)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass : lb_gen_scope

    // What the base test reads of a generated env, one replay log, and the
    // driver path of an AXI agent.
    class lb_gen_env extends uvm_env;
        virtual a2c_clk_if clk_vif;
        bit                dual_dut = 1;
        lb_bit_log_t       replay;
        lb_gen_scope       axi_drv;

        `uvm_component_utils(lb_gen_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            lb_fake_lanes lanes = new();
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(null, "uvm_test_top", "clk", clk_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk'")
            replay = lb_bit_log_t::type_id::create("replay", this);
            replay.driver  = lanes;
            replay.clk_vif = clk_vif;
            axi_drv = lb_gen_scope::type_id::create("drv", lb_gen_scope::type_id::create("rd_agent", this));
        endfunction

        function void model_stable_point();
        endfunction
    endclass : lb_gen_env

    // RENDERED BEGIN
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
    // UVM_INFO. An AXI master in Mode B declares a lane dead when it
    // trails the other by lane_skew_cycles clocks, and the other lane
    // dead too when, left alone, it makes no progress for
    // lone_lane_cycles clocks. Left at -1 each keeps the master's own
    // 200000, +a2c_lane_skew_cycles and +a2c_lone_lane_cycles override
    // them, and 0 turns a rule off.
    class lb_gen_base extends uvm_test;
        lb_gen_env env;
        int unsigned output_deadline_cycles = 200000;
        int unsigned quiet_cycles = 1000;
        int unsigned clock_stop_cycles = 1000;
        int          drain_quiet_cycles = -1;
        int          drain_deadline_cycles = -1;
        int          drain_catchup_cycles = -1;
        bit          drain_cut_expected;
        int          lane_skew_cycles = -1;
        int          lone_lane_cycles = -1;

        `uvm_component_utils(lb_gen_base)

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
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_clock_stop_cycles", clock_stop_cycles);
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_quiet_cycles", drain_quiet_cycles);
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_deadline_cycles", drain_deadline_cycles);
            if (drain_catchup_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_catchup_cycles", drain_catchup_cycles);
            end
            uvm_config_db#(bit)::set(this, "env*", "a2c_drain_cut_expected", drain_cut_expected);
            if (lane_skew_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_lane_skew_cycles", lane_skew_cycles);
            end
            if (lone_lane_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_lone_lane_cycles", lone_lane_cycles);
            end
            env = lb_gen_env::type_id::create("env", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            env.clk_vif.wait_reset_release();
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
            if (env.dual_dut) begin
                env.model_stable_point();
            end
        endtask
    endclass : lb_gen_base
    // RENDERED END

    // A test that sets the drain's window, deadline and catch-up, the lane
    // skew bound and the lone lane bound in its constructor: the replay log
    // must get the drain's, not the values the base test derives, and an AXI
    // master driver below the env each bound. A bound expected unset leaves
    // the driver its own default.
    class gen_base_drain_ctor_test extends lb_gen_base;
        int unsigned want[3] = '{37, 4100, 99};
        bit          skew_set = 1;
        int unsigned want_skew = 3000;
        bit          lone_set = 1;
        int unsigned want_lone = 4000;

        `uvm_component_utils(gen_base_drain_ctor_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            drain_quiet_cycles    = 37;
            drain_deadline_cycles = 4100;
            drain_catchup_cycles  = 99;
            lane_skew_cycles      = 3000;
            lone_lane_cycles      = 4000;
        endfunction

        protected function void check_bound(string knob, bit got_set, int unsigned got, bit set, int unsigned want);
            if (got_set == set && (!set || got == want)) return;
            `uvm_error("LB_GEN", $sformatf("%s reads %s %s, expected %s", env.axi_drv.get_full_name(), knob,
                                           got_set ? $sformatf("of %0d", got) : "of none", set ? $sformatf("of %0d", want) : "of none"))
        endfunction

        virtual function void end_of_elaboration_phase(uvm_phase phase);
            int unsigned got[3] = '{env.replay.drain_quiet_cycles, env.replay.drain_deadline_cycles, env.replay.catchup_cycles()};
            int unsigned skew = 0;
            int unsigned lone = 0;
            bit          got_skew = a2c_get_config_int(env.axi_drv, "a2c_lane_skew_cycles", skew);
            bit          got_lone = a2c_get_config_int(env.axi_drv, "a2c_lone_lane_cycles", lone);
            super.end_of_elaboration_phase(phase);
            `uvm_info("LB_STATS", $sformatf("the replay log's window, deadline and catch-up: %p; lane skew bound set %0d, %0d; lone lane bound set %0d, %0d",
                                            got, got_skew, skew, got_lone, lone), UVM_NONE)
            if (got != want) `uvm_error("LB_GEN", $sformatf("the replay log got %p, expected %p", got, want))
            check_bound("a2c_lane_skew_cycles", got_skew, skew, skew_set, want_skew);
            check_bound("a2c_lone_lane_cycles", got_lone, lone, lone_set, want_lone);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
        endfunction
    endclass : gen_base_drain_ctor_test

    // A test that sets only the quiet window and the output deadline in its
    // constructor: the drain's window and deadline must follow them, the
    // catch-up the log's deadline, and the two lane bounds none of them.
    class gen_base_drain_default_test extends gen_base_drain_ctor_test;
        `uvm_component_utils(gen_base_drain_default_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            drain_quiet_cycles     = -1;
            drain_deadline_cycles  = -1;
            drain_catchup_cycles   = -1;
            quiet_cycles           = 45;
            output_deadline_cycles = 5000;
            lane_skew_cycles       = -1;
            lone_lane_cycles       = -1;
            want                   = '{45, 5000, 5000};
            skew_set               = 0;
            lone_set               = 0;
        endfunction
    endclass : gen_base_drain_default_test

    // A lane skew bound of 0, which turns the bound off, reaches the driver,
    // and the lone lane bound keeps its own value.
    class gen_base_skew_off_test extends gen_base_drain_ctor_test;
        `uvm_component_utils(gen_base_skew_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            lane_skew_cycles = 0;
            want_skew        = 0;
        endfunction
    endclass : gen_base_skew_off_test

    // A lone lane bound of 0, which turns the rule off, reaches the driver,
    // and the lane skew bound keeps its own value.
    class gen_base_lone_off_test extends gen_base_drain_ctor_test;
        `uvm_component_utils(gen_base_lone_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            lone_lane_cycles = 0;
            want_lone        = 0;
        endfunction
    endclass : gen_base_lone_off_test

    // Only the lane skew bound set: the lone lane bound must not follow it,
    // so the driver keeps its own.
    class gen_base_lone_unset_test extends gen_base_drain_ctor_test;
        `uvm_component_utils(gen_base_lone_unset_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            lone_lane_cycles = -1;
            lone_set         = 0;
        endfunction
    endclass : gen_base_lone_unset_test

    // lb_gen_env with a hand-written default deadline for its replay log,
    // set as int.
    class lb_gen_int_env extends lb_gen_env;
        `uvm_component_utils(lb_gen_int_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_config_db#(int)::set(this, "replay", "a2c_drain_deadline_cycles", 7777);
            super.build_phase(phase);
        endfunction
    endclass : lb_gen_int_env

    // The drain knobs set as different types. The test sets the window for
    // env* as int and then for the replay log alone as int unsigned, and
    // the env sets its own deadline as int under the base test's int
    // unsigned one. Each read must follow the config_db's precedence as if
    // all were one type: the log's own later window, 61, and the test's
    // deadline, 4100, over the env's.
    class gen_base_drain_types_test extends gen_base_drain_ctor_test;
        `uvm_component_utils(gen_base_drain_types_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            lb_gen_env::type_id::set_type_override(lb_gen_int_env::get_type());
            want = '{61, 4100, 99};
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            uvm_config_db#(int)::set(this, "env*", "a2c_drain_quiet_cycles", 50);
            uvm_config_db#(int unsigned)::set(this, "env.replay", "a2c_drain_quiet_cycles", 61);
        endfunction
    endclass : gen_base_drain_types_test

    // A knob set as a type the config_db read does not take: the replay
    // log's window as longint unsigned, its cut flag as string and the AXI
    // driver's lone lane bound as longint unsigned, each after the base
    // test's set. Each entry must be skipped as if never set, so the log
    // takes the base test's window, 37, and flag, 0, and the driver its
    // bound, 4000, with one A2C_CFG warning each naming the value taken and
    // the type to set.
    class gen_base_drain_wrong_type_test extends gen_base_drain_ctor_test;
        lb_id_counter cfgs;

        `uvm_component_utils(gen_base_drain_wrong_type_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            cfgs = lb_id_counter::type_id::create("cfgs");
            cfgs.id = "A2C_CFG";
            uvm_report_cb::add(null, cfgs);
            super.build_phase(phase);
            uvm_config_db#(longint unsigned)::set(this, "env.replay", "a2c_drain_quiet_cycles", 61);
            uvm_config_db#(string)::set(this, "env.replay", "a2c_drain_cut_expected", "1");
            uvm_config_db#(longint unsigned)::set(this, "env.rd_agent.drv", "a2c_lone_lane_cycles", 61);
        endfunction

        virtual function void end_of_elaboration_phase(uvm_phase phase);
            string want[3] = '{"uvm_test_top.env.replay: the config_db entry that sets a2c_drain_quiet_cycles is not of type int unsigned, int or uvm_config_int, so it is ignored and the knob takes 37 from the next entry of an accepted type. Set it as int unsigned",
                               "uvm_test_top.env.replay: the config_db entry that sets a2c_drain_cut_expected is not of type bit, int unsigned, int or uvm_config_int, so it is ignored and the knob takes 0 from the next entry of an accepted type. Set it as bit",
                               "uvm_test_top.env.rd_agent.drv: the config_db entry that sets a2c_lone_lane_cycles is not of type int unsigned, int or uvm_config_int, so it is ignored and the knob takes 4000 from the next entry of an accepted type. Set it as int unsigned"};
            super.end_of_elaboration_phase(phase);
            `uvm_info("LB_STATS", $sformatf("drain_cut_expected %0d; %0d A2C_CFG: %p", env.replay.drain_cut_expected, cfgs.warnings,
                                            cfgs.messages), UVM_NONE)
            if (env.replay.drain_cut_expected) `uvm_error("LB_GEN", "the log took the string entry for drain_cut_expected")
            if (cfgs.warnings != 3) `uvm_error("LB_GEN", $sformatf("expected three A2C_CFG warnings, got %0d", cfgs.warnings))
            foreach (want[i]) begin
                int unsigned n = 0;
                foreach (cfgs.messages[j]) n += a2c_contains(cfgs.messages[j], want[i]);
                if (n != 1) `uvm_error("LB_GEN", $sformatf("%0d A2C_CFG hold '%s', expected one: %p", n, want[i], cfgs.messages))
            end
        endfunction
    endclass : gen_base_drain_wrong_type_test
