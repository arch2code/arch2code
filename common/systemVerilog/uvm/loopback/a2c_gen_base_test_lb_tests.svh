// A loopback run of the base test that templates/systemVerilog/uvmTest.py
// generates, so its handling of the drain knobs and of the run timeout is
// simulated, not only read. The span between the RENDERED markers is
// render_tests() of that template for lb_gen_env, a stand-in for the
// generated env with two clocks, clk and clk2, an input port, lb_in, a
// status input, lb_st, and one counted output, lb_out;
// unittest/test_uvm_test_pkg.py fails when the span and the template
// differ. Included in a2c_uvm_loopback_pkg after
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

    // The items of the stand-in ports.
    class lb_gen_item extends uvm_sequence_item;
        `uvm_object_utils(lb_gen_item)

        function new(string name = "lb_gen_item");
            super.new(name);
        endfunction
    endclass : lb_gen_item

    typedef lb_gen_item lb_in_item_t;
    typedef st_item_t   lb_st_item_t;

    // Takes each item at once.
    class lb_gen_sink extends uvm_driver #(lb_gen_item);
        `uvm_component_utils(lb_gen_sink)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            forever begin
                seq_item_port.get_next_item(req);
                seq_item_port.item_done();
            end
        endtask
    endclass : lb_gen_sink

    // An input port's active agent, as far as the base test reads it.
    class lb_gen_in_agent extends uvm_agent;
        uvm_sequencer #(lb_gen_item) sqr;
        lb_gen_sink                  drv;

        `uvm_component_utils(lb_gen_in_agent)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            sqr = uvm_sequencer#(lb_gen_item)::type_id::create("sqr", this);
            drv = lb_gen_sink::type_id::create("drv", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            drv.seq_item_port.connect(sqr.seq_item_export);
        endfunction
    endclass : lb_gen_in_agent

    // Sends n items.
    class lb_gen_seq extends uvm_sequence #(lb_gen_item);
        int unsigned n;

        `uvm_object_utils(lb_gen_seq)

        function new(string name = "lb_gen_seq");
            super.new(name);
        endfunction

        virtual task body();
            repeat (n) begin
                req = lb_gen_item::type_id::create("req");
                start_item(req);
                finish_item(req);
            end
        endtask
    endclass : lb_gen_seq

    // What the base test reads of a generated env: one replay log, the
    // driver path of an AXI agent, an input port's agent, a status input's
    // agent on the st pin set and an output's counter.
    class lb_gen_env extends uvm_env;
        virtual a2c_clk_if                 clk_vif;
        virtual a2c_clk_if                 clk2_vif;
        bit                                dual_dut = 1;
        lb_bit_log_t                       replay;
        lb_gen_scope                       axi_drv;
        lb_gen_in_agent                    lb_in_agent;
        st_agent_t                         lb_st_agent;
        a2c_txn_counter #(lb_gen_item)     lb_out_counter;

        `uvm_component_utils(lb_gen_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            lb_fake_lanes lanes = new();
            st_config_t   st_cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(null, "uvm_test_top", "clk", clk_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk'")
            if (!uvm_config_db#(virtual a2c_clk_if)::get(null, "uvm_test_top", "clk2", clk2_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk2'")
            replay = lb_bit_log_t::type_id::create("replay", this);
            replay.driver  = lanes;
            replay.clk_vif = clk_vif;
            axi_drv = lb_gen_scope::type_id::create("drv", lb_gen_scope::type_id::create("rd_agent", this));
            lb_in_agent    = lb_gen_in_agent::type_id::create("lb_in_agent", this);
            st_cfg         = st_config_t::type_id::create("st_cfg");
            if (!uvm_config_db#(st_vif_t)::get(null, "uvm_test_top", "st", st_cfg.vif)) `uvm_fatal("LB_CFG", "no virtual status_if 'st'")
            st_cfg.clk_vif   = clk_vif;
            st_cfg.port_name = "lb_st";
            uvm_config_db#(st_config_t)::set(this, "lb_st_agent", "cfg", st_cfg);
            lb_st_agent    = st_agent_t::type_id::create("lb_st_agent", this);
            lb_out_counter = a2c_txn_counter#(lb_gen_item)::type_id::create("lb_out_counter", this);
            lb_out_counter.port_name = "lb_out";
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
    // UVM_INFO. A master in Mode B declares a lane dead when it trails
    // the other by lane_skew_cycles clocks, the other lane dead too
    // when, left alone, it makes no progress for lone_lane_cycles
    // clocks, and the masters declare every live lane dead when no
    // port makes a handshake for joint_stall_cycles clocks while a
    // lane waits. Left at -1 each keeps the master's own
    // 200000, +a2c_lane_skew_cycles, +a2c_lone_lane_cycles and
    // +a2c_joint_stall_cycles override them, and 0 turns a rule off. A
    // run that sends nothing on an input and expects no output
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
    // +a2c_rt_refusal_cycles and +a2c_rt_on_model override them.
    class lb_gen_base extends uvm_test implements a2c_run_work;
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
        int          joint_stall_cycles = -1;
        bit          no_stimulus_expected;
        int          run_timeout_cycles = -1;
        int          run_timeout_floor_cycles = -1;
        int          run_timeout_factor = -1;
        int          rt_gap_cycles = -1;
        int          rt_latency_cycles = -1;
        int          rt_lag_cycles = -1;
        int          rt_refusal_cycles = -1;
        int          rt_on_model = -1;
        a2c_run_timeout run_timeout;

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
            void'($value$plusargs("a2c_joint_stall_cycles=%d", joint_stall_cycles));
            void'($value$plusargs("a2c_no_stimulus_expected=%d", no_stimulus_expected));
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
            if (lane_skew_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_lane_skew_cycles", lane_skew_cycles);
            end
            if (lone_lane_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_lone_lane_cycles", lone_lane_cycles);
            end
            if (joint_stall_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_joint_stall_cycles", joint_stall_cycles);
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
            env = lb_gen_env::type_id::create("env", this);
            run_timeout = a2c_run_timeout::type_id::create("run_timeout", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            run_timeout.clk_vif = env.clk_vif;
            run_timeout.clock   = "clk";
            run_timeout.work    = this;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            env.clk_vif.wait_reset_release();
            env.clk2_vif.wait_reset_release();
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
                env.lb_out_counter.wait_for_count(env.clk_vif, output_deadline_cycles, quiet_cycles);
            join
            if (env.dual_dut) begin
                env.model_stable_point();
            end
        endtask

        // Warns about a run that sent nothing on any input and declared no
        // transaction on any output, as the scaffolded smoke test does until
        // its run_body() sends stimulus. A Mode B comparator or a check of the
        // test's own may still have run, so the warning claims no more.
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (no_stimulus_expected || stimulus_sent() != 0) return;
            if (env.lb_out_counter.declared() != 0) return;
            `uvm_warning("A2C_NO_STIMULUS", $sformatf("%s sent no transaction on any input and declared no transaction on any output. Send stimulus in run_body(), through the input agents' sequencers or a status input's cfg.value, and declare each output's transactions with expect_count() on its counter, or set no_stimulus_expected (+a2c_no_stimulus_expected=1) in a test meant to send nothing",
                                                      get_type_name()))
        endfunction

        // The items the input ports' agents have sent, through their
        // sequencers or, for a status input, their drivers.
        virtual function int unsigned stimulus_sent();
            int unsigned n = 0;
            n += a2c_items_sent#(lb_in_item_t)::of(env.lb_in_agent);
            n += a2c_items_sent#(lb_st_item_t)::of(env.lb_st_agent);
            return n;
        endfunction

        // The transactions the output counters expect.
        virtual function int unsigned outputs_declared();
            int unsigned n = 0;
            n += env.lb_out_counter.declared();
            return n;
        endfunction
    endclass : lb_gen_base
    // RENDERED END

    // A test that sets the drain's window, deadline and catch-up, the lane
    // skew bound, the lone lane bound and the joint stall bound in its
    // constructor: the replay log must get the drain's, not the values the
    // base test derives, and an AXI master driver below the env each bound.
    // A bound expected unset leaves the driver its own default. It sends
    // nothing on purpose.
    class gen_base_drain_ctor_test extends lb_gen_base;
        int unsigned want[3] = '{37, 4100, 99};
        bit          skew_set = 1;
        int unsigned want_skew = 3000;
        bit          lone_set = 1;
        int unsigned want_lone = 4000;
        bit          joint_set = 1;
        int unsigned want_joint = 5000;

        `uvm_component_utils(gen_base_drain_ctor_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            drain_quiet_cycles    = 37;
            drain_deadline_cycles = 4100;
            drain_catchup_cycles  = 99;
            lane_skew_cycles      = 3000;
            lone_lane_cycles      = 4000;
            joint_stall_cycles    = 5000;
            no_stimulus_expected  = 1;
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
            int unsigned joint = 0;
            bit          got_skew = a2c_get_config_int(env.axi_drv, "a2c_lane_skew_cycles", skew);
            bit          got_lone = a2c_get_config_int(env.axi_drv, "a2c_lone_lane_cycles", lone);
            bit          got_joint = a2c_get_config_int(env.axi_drv, "a2c_joint_stall_cycles", joint);
            super.end_of_elaboration_phase(phase);
            `uvm_info("LB_STATS", $sformatf("the replay log's window, deadline and catch-up: %p; lane skew bound set %0d, %0d; lone lane bound set %0d, %0d; joint stall bound set %0d, %0d",
                                            got, got_skew, skew, got_lone, lone, got_joint, joint), UVM_NONE)
            if (got != want) `uvm_error("LB_GEN", $sformatf("the replay log got %p, expected %p", got, want))
            check_bound("a2c_lane_skew_cycles", got_skew, skew, skew_set, want_skew);
            check_bound("a2c_lone_lane_cycles", got_lone, lone, lone_set, want_lone);
            check_bound("a2c_joint_stall_cycles", got_joint, joint, joint_set, want_joint);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
        endfunction
    endclass : gen_base_drain_ctor_test

    // A test that sets only the quiet window and the output deadline in its
    // constructor: the drain's window and deadline must follow them, the
    // catch-up the log's deadline, and the three lane bounds none of them.
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
            joint_stall_cycles     = -1;
            want                   = '{45, 5000, 5000};
            skew_set               = 0;
            lone_set               = 0;
            joint_set              = 0;
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

    // A joint stall bound of 0, which turns the rule off, reaches the
    // driver, and the other bounds keep their own values.
    class gen_base_joint_off_test extends gen_base_drain_ctor_test;
        `uvm_component_utils(gen_base_joint_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            joint_stall_cycles = 0;
            want_joint         = 0;
        endfunction
    endclass : gen_base_joint_off_test

    // The joint stall bound left at -1 sets nothing, so the driver keeps its
    // own, whatever the other bounds.
    class gen_base_joint_unset_test extends gen_base_drain_ctor_test;
        `uvm_component_utils(gen_base_joint_unset_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            joint_stall_cycles = -1;
            joint_set          = 0;
        endfunction
    endclass : gen_base_joint_unset_test

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

    // The base test's check that a run did something. It sends n_sent
    // items on lb_in, sets the status input lb_st if set_status is set, and
    // declares n_declared transactions on lb_out, which it then delivers
    // itself, so the counter is satisfied; it expects want_warnings
    // A2C_NO_STIMULUS, which must name the test and the way out.
    class gen_base_no_stimulus_test extends lb_gen_base;
        lb_id_counter ids;
        int unsigned  n_sent;
        bit           set_status;
        int unsigned  n_declared;
        int unsigned  want_warnings = 1;

        `uvm_component_utils(gen_base_no_stimulus_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            quiet_cycles = 20;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            ids = lb_id_counter::type_id::create("ids");
            ids.id = "A2C_NO_STIMULUS";
            uvm_report_cb::add(null, ids);
            super.build_phase(phase);
        endfunction

        virtual task run_body();
            lb_gen_seq seq = lb_gen_seq::type_id::create("seq");
            seq.n = n_sent;
            seq.start(env.lb_in_agent.sqr);
            if (set_status) env.lb_st_agent.cfg.value = '{tag: 4'h1, value: 20'h5};
            env.lb_out_counter.expect_count(n_declared);
            repeat (n_declared) env.lb_out_counter.analysis_export.write(lb_gen_item::type_id::create("out"));
        endtask

        virtual function void report_phase(uvm_phase phase);
            string            want = {get_type_name(), " sent no transaction on any input and declared no transaction on any output. ",
                                      "Send stimulus in run_body(), through the input agents' sequencers or a status input's cfg.value, and declare each output's transactions ",
                                      "with expect_count() on its counter, or set no_stimulus_expected (+a2c_no_stimulus_expected=1) in a test meant to send nothing"};
            uvm_report_server srv = uvm_report_server::get_server();
            `uvm_info("LB_STATS", $sformatf("%0d A2C_NO_STIMULUS: %p", ids.warnings, ids.messages), UVM_NONE)
            if (ids.warnings != want_warnings) `uvm_error("LB_GEN", $sformatf("expected %0d A2C_NO_STIMULUS, got %0d", want_warnings, ids.warnings))
            foreach (ids.messages[i]) begin
                if (ids.messages[i] != want) `uvm_error("LB_GEN", $sformatf("A2C_NO_STIMULUS reads '%s', expected '%s'", ids.messages[i], want))
            end
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
        endfunction
    endclass : gen_base_no_stimulus_test

    // As gen_base_no_stimulus_test with no_stimulus_expected set: no
    // warning.
    class gen_base_no_stimulus_off_test extends gen_base_no_stimulus_test;
        `uvm_component_utils(gen_base_no_stimulus_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            no_stimulus_expected = 1;
            want_warnings        = 0;
        endfunction
    endclass : gen_base_no_stimulus_off_test

    // One item sent on the input port is stimulus: no warning.
    class gen_base_stimulus_sent_test extends gen_base_no_stimulus_test;
        `uvm_component_utils(gen_base_stimulus_sent_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_sent        = 1;
            want_warnings = 0;
        endfunction
    endclass : gen_base_stimulus_sent_test

    // A value set on the status input, which has no sequencer, is stimulus:
    // no warning.
    class gen_base_status_stimulus_test extends gen_base_no_stimulus_test;
        `uvm_component_utils(gen_base_status_stimulus_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            set_status    = 1;
            want_warnings = 0;
        endfunction
    endclass : gen_base_status_stimulus_test

    // One transaction declared on the output, with none sent, checks the
    // DUT's output: no warning.
    class gen_base_output_declared_test extends gen_base_no_stimulus_test;
        `uvm_component_utils(gen_base_output_declared_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_declared    = 1;
            want_warnings = 0;
        endfunction
    endclass : gen_base_output_declared_test

    // a2c_items_sent::of() given no agent, an agent whose sequencer sends
    // another item type, or a component with neither a sequencer nor a
    // counting driver: one A2C_CFG error each, and a count of 0.
    class a2c_items_sent_cfg_test extends lb_mode_b_base;
        `uvm_component_utils(a2c_items_sent_cfg_test)

        lb_gen_in_agent in_agent;
        lb_gen_scope    scope;

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_CFG";
            want_errors = 3;
            want_text.push_back("a2c_items_sent::of() was given no agent");
            want_text.push_back("uvm_test_top.in_agent: the sequencer sqr does not send the item type the base test counts");
            want_text.push_back("uvm_test_top.scope has no sequencer sqr and no driver drv that counts its items (a2c_items_driven)");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            in_agent = lb_gen_in_agent::type_id::create("in_agent", this);
            scope    = lb_gen_scope::type_id::create("scope", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            int unsigned n[3];
            phase.raise_objection(this);
            n[0] = a2c_items_sent#(lb_gen_item)::of(null);
            n[1] = a2c_items_sent#(st_item_t)::of(in_agent);
            n[2] = a2c_items_sent#(lb_gen_item)::of(scope);
            if (n[0] != 0 || n[1] != 0 || n[2] != 0) `uvm_error("LB_GEN", $sformatf("the counts are %p, expected 0 each", n))
            phase.drop_objection(this);
        endtask
    endclass : a2c_items_sent_cfg_test

    // Also records the time of each message of `severity`; only errors are
    // demoted.
    class lb_timed_demoter extends lb_recording_demoter;
        realtime     at[$];
        uvm_severity severity = UVM_ERROR;

        `uvm_object_utils(lb_timed_demoter)

        function new(string name = "lb_timed_demoter");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_severity() == severity && get_id() == demote_id) at.push_back($realtime);
            return super.catch();
        endfunction
    endclass : lb_timed_demoter

    // With hold set, holds the run phase's objection from its start; with
    // hold_main set, main_phase's.
    class lb_gen_holder extends uvm_component;
        bit      hold;
        bit      hold_main;
        bit      hold_reset;
        bit      hold_shutdown;
        bit      hold_custom;
        bit      hold_late;
        // With main_for above 0, main_phase objects for that long and then
        // sets main_done.
        realtime main_for;
        bit      main_done;

        `uvm_component_utils(lb_gen_holder)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            if (hold) phase.raise_objection(this);
        endtask

        virtual task reset_phase(uvm_phase phase);
            if (hold_reset) phase.raise_objection(this);
        endtask

        virtual task shutdown_phase(uvm_phase phase);
            if (hold_shutdown) phase.raise_objection(this);
        endtask

        // lb_custom_phase.
        virtual task custom_phase(uvm_phase phase);
            if (hold_custom) phase.raise_objection(this);
        endtask

        // lb_late_phase.
        virtual task late_phase(uvm_phase phase);
            if (hold_late) phase.raise_objection(this);
        endtask

        virtual task main_phase(uvm_phase phase);
            if (hold_main) phase.raise_objection(this);
            if (main_for > 0) begin
                phase.raise_objection(this);
                #(main_for);
                main_done = 1;
                phase.drop_objection(this);
            end
        endtask
    endclass : lb_gen_holder

    // A user-defined task phase, which lb_gen_holder implements.
    class lb_custom_phase extends uvm_task_phase;
        local static lb_custom_phase m_inst;

        function new(string name = "custom");
            super.new(name);
        endfunction

        static function lb_custom_phase get();
            if (m_inst == null) m_inst = new();
            return m_inst;
        endfunction

        virtual task exec_task(uvm_component comp, uvm_phase phase);
            lb_gen_holder h;
            if ($cast(h, comp)) h.custom_phase(phase);
        endtask
    endclass : lb_custom_phase

    // A user-defined task phase of the common domain, which lb_gen_holder
    // implements.
    class lb_late_phase extends uvm_task_phase;
        local static lb_late_phase m_inst;

        function new(string name = "late");
            super.new(name);
        endfunction

        static function lb_late_phase get();
            if (m_inst == null) m_inst = new();
            return m_inst;
        endfunction

        virtual task exec_task(uvm_component comp, uvm_phase phase);
            lb_gen_holder h;
            if ($cast(h, comp)) h.late_phase(phase);
        endtask
    endclass : lb_late_phase

    // A user-defined function phase that does nothing.
    class lb_func_phase extends uvm_topdown_phase;
        local static lb_func_phase m_inst;

        function new(string name = "func");
            super.new(name);
        endfunction

        static function lb_func_phase get();
            if (m_inst == null) m_inst = new();
            return m_inst;
        endfunction

        virtual function void exec_func(uvm_component comp, uvm_phase phase);
        endfunction
    endclass : lb_func_phase

    // Records the messages of one ID at UVM_INFO, leaving out the errors a
    // demoter turned into infos.
    class lb_info_recorder extends uvm_report_catcher;
        string id;
        string messages[$];

        `uvm_object_utils(lb_info_recorder)

        function new(string name = "lb_info_recorder");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_id() == id && get_severity() == UVM_INFO && !a2c_contains(get_message(), "demoted to info")) messages.push_back(get_message());
            return THROW;
        endfunction
    endclass : lb_info_recorder

    // lb_gen_env with a rdy_vld master, rv_agent, on the rv pin set, and on
    // rv_model too in Mode B (lb_mode_b), that nothing ever makes ready, and
    // holder.
    class lb_gen_hang_env extends lb_gen_env;
        rv_agent_t    rv_agent;
        lb_gen_holder holder;

        `uvm_component_utils(lb_gen_hang_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t cfg;
            bit         mode_b;
            super.build_phase(phase);
            void'(uvm_config_db#(bit)::get(this, "", "lb_mode_b", mode_b));
            dual_dut = mode_b;
            cfg = rv_config_t::type_id::create("rv_cfg");
            if (!uvm_config_db#(rv_vif_t)::get(null, "uvm_test_top", "rv", cfg.vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            if (mode_b && !uvm_config_db#(rv_vif_t)::get(null, "uvm_test_top", "rv_model", cfg.model_vif)) begin
                `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv_model'")
            end
            cfg.clk_vif   = clk_vif;
            cfg.role      = A2C_SRC;
            cfg.port_name = "rv";
            uvm_config_db#(rv_config_t)::set(this, "rv_agent", "cfg", cfg);
            rv_agent = rv_agent_t::type_id::create("rv_agent", this);
            holder   = lb_gen_holder::type_id::create("holder", this);
        endfunction
    endclass : lb_gen_hang_env

    // The run timeout. A test of the base test on lb_gen_hang_env whose
    // run_body() declares n_declared transactions on lb_out, and with
    // n_extra above 0 receives that many more than it declared, in Mode B
    // records n_recorded responses in the replay log, which the model lane
    // never replays, sends n_sent items on lb_in, gap clocks apart, which
    // its sink takes at once, and then sends n_items on rv, which never
    // transfer; with hold set, holder holds the run phase and the base test
    // waits for nothing, and with hold_main, holder holds main_phase.
    // Checks:
    //   - one A2C_RUN_TIMEOUT at want_cycles rising edges of clk after its
    //     reset release, saying the clocks, the clock, how the budget was
    //     set (want_how), the ports that wait (want_ports, then
    //     want_ports_end), the objectors (want_objectors) and the knob to
    //     raise (want_raise); with want_cycles 0, none, and one
    //     A2C_RUN_TIMEOUT info giving the clocks the run phase took;
    //   - that extract_phase and check_phase each run once, check_phase in
    //     the time step of the timeout, and that the lb_out counter's
    //     A2C_TXN_COUNT and the replay log's A2C_REPLAY still report what is
    //     missing, n_declared and n_recorded, naming the timeout, and with
    //     n_extra the A2C_TXN_COUNT of the extra transactions, which does
    //     not name it;
    //   - with want_joint, one A2C_JOINT_STALL before the timeout.
    // This test fixes the budget at 500 clocks.
    class gen_base_run_timeout_mode_a_test extends lb_gen_base;
        bit                  mode_b;
        bit                  hold;
        bit                  hold_main;
        int unsigned         n_sent;
        int unsigned         gap;
        int unsigned         n_items = 1;
        int unsigned         n_declared = 3;
        int unsigned         n_extra;
        int unsigned         n_recorded;
        int unsigned         want_cycles = 500;
        string               want_how = "The budget is fixed by run_timeout_cycles (+a2c_run_timeout_cycles)";
        string               want_ports = "rv (uvm_test_top.env.rv_agent.drv), waiting for the transfer of ";
        string               want_ports_end = "";
        string               want_objectors = "uvm_test_top";
        string               want_raise = "Raise run_timeout_cycles, or the value the test passes to fix(), if the test is legitimately longer.";
        // The task phases ended as they began that held an objection, as
        // the info names them, from the phase's name on.
        string               want_late[$];
        // The A2C_MODEL_CMP end-of-test reports, each of which names the
        // timeout.
        string               want_cmp[$];
        bit                  want_joint;
        lb_timed_demoter     timeouts;
        lb_recording_demoter counts;
        lb_recording_demoter replays;
        lb_recording_demoter joints;
        lb_recording_demoter cmps;
        lb_info_recorder     infos;
        // a2c_run_timeout_clause() and death_context() in the timeout's time
        // step, after it, when the run phase may still raise a report.
        string               clause_in_step = "unset";
        string               death_in_step = "unset";
        realtime             released_at;
        realtime             checked_at = -1;
        // How long after the timeout check_phase runs.
        realtime             check_after;
        int unsigned         extracts;
        int unsigned         checks;

        `uvm_component_utils(gen_base_run_timeout_mode_a_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            lb_gen_env::type_id::set_type_override(lb_gen_hang_env::get_type());
            run_timeout_cycles = 500;
        endfunction

        // A derived budget of floor + factor x the work, which the test
        // expects to be want_work, want_sent of it sent on the inputs. The
        // output deadline, the one progress bound in Mode A, is kept below
        // the floor, with a quiet window below it.
        protected function void derive(int unsigned floor, int unsigned factor, int unsigned want_work, int unsigned want_sent);
            quiet_cycles             = 5;
            output_deadline_cycles   = 10;
            run_timeout_cycles       = -1;
            run_timeout_floor_cycles = floor;
            run_timeout_factor       = factor;
            want_cycles              = floor + factor * want_work;
            want_how                 = $sformatf("The budget is run_timeout_floor_cycles %0d + run_timeout_factor %0d x %0d, the work the test has declared (input items sent %0d, output transactions expected %0d)",
                                                 floor, factor, want_work, want_sent, want_work - want_sent);
            want_raise               = "Raise run_timeout_factor or run_timeout_floor_cycles, or fix the budget with run_timeout_cycles or fix(), if the test is legitimately longer.";
        endfunction

        protected function lb_recording_demoter demote(string id, lb_recording_demoter d = null);
            if (d == null) d = lb_recording_demoter::type_id::create({"demote_", id});
            d.demote_id = id;
            uvm_report_cb::add(null, d);
            return d;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            timeouts = lb_timed_demoter::type_id::create("demote_A2C_RUN_TIMEOUT");
            void'(demote("A2C_RUN_TIMEOUT", timeouts));
            counts   = demote("A2C_TXN_COUNT");
            replays  = demote("A2C_REPLAY");
            joints   = demote("A2C_JOINT_STALL");
            cmps     = demote("A2C_MODEL_CMP");
            infos    = lb_info_recorder::type_id::create("infos");
            infos.id = "A2C_RUN_TIMEOUT";
            uvm_report_cb::add(null, infos);
            uvm_config_db#(bit)::set(this, "env", "lb_mode_b", mode_b);
            super.build_phase(phase);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            lb_gen_hang_env e;
            super.connect_phase(phase);
            void'($cast(e, env));
            e.holder.hold      = hold;
            e.holder.hold_main = hold_main;
        endfunction

        // Not under the run phase, which ends in that time step.
        virtual function void start_of_simulation_phase(uvm_phase phase);
            super.start_of_simulation_phase(phase);
            fork
                begin
                    wait (a2c_run_timed_out_at >= 0);
                    clause_in_step = a2c_run_timeout_clause();
                    death_in_step  = a2c_replay_drain::death_context($realtime);
                end
            join_none
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    env.clk_vif.wait_reset_release();
                    released_at = $realtime;
                end
            join_none
            super.run_phase(phase);
        endtask

        virtual task run_body();
            lb_gen_hang_env e;
            lb_list_seq#(rv_item_t) seq = new("seq");
            void'($cast(e, env));
            env.lb_out_counter.expect_count(n_declared);
            if (n_extra != 0) repeat (n_declared + n_extra) env.lb_out_counter.analysis_export.write(lb_gen_item::type_id::create("out"));
            repeat (n_recorded) env.replay.record(1'b1, 0);
            repeat (n_sent) begin
                lb_gen_seq in_seq = lb_gen_seq::type_id::create("in_seq");
                in_seq.n = 1;
                in_seq.start(env.lb_in_agent.sqr);
                repeat (gap) @(posedge env.clk_vif.clk);
            end
            repeat (n_items) begin
                rv_item_t it = rv_item_t::type_id::create("it");
                it.data = '{tag: 4'h3, value: 20'h5};
                seq.items.push_back(it);
            end
            seq.start(e.rv_agent.sqr);
            if (n_items != 0) wait (0);
        endtask

        virtual function void extract_phase(uvm_phase phase);
            extracts++;
            super.extract_phase(phase);
        endfunction

        virtual function void check_phase(uvm_phase phase);
            checks++;
            checked_at = $realtime;
            super.check_phase(phase);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            realtime          want_at = released_at + want_cycles * 10ns;
            int unsigned      w = stimulus_sent() + outputs_declared();
            string            rate = (w == 0) ? "no work declared" : $sformatf("%0.1f clocks per unit of the work declared, W %0d", real'(want_cycles) / w, w);
            string            head = $sformatf("%s: the run phase has not ended after %0d clocks of clk, its run timeout: %s. %s. Ports waiting now: %s",
                                               get_type_name(), want_cycles, rate, want_how, want_ports);
            string            tail = {want_ports_end, ". Objections still raised by: ", want_objectors, ". ", want_raise};
            string            cut = $sformatf("; the run timeout ended the run phase at %0t (A2C_RUN_TIMEOUT), which may account for this", want_at);
            `uvm_info("LB_STATS", $sformatf("released at %0t, A2C_RUN_TIMEOUT at %p, check_phase at %0t, %0d extract and %0d check; %0d A2C_TXN_COUNT, %0d A2C_REPLAY, %0d A2C_JOINT_STALL: %p; infos %p",
                                            released_at, timeouts.at, checked_at, extracts, checks, counts.demoted, replays.demoted, joints.demoted,
                                            timeouts.messages, infos.messages), UVM_NONE)
            if (want_cycles == 0) begin
                // The run phase can end on a rising edge, before or after the
                // count takes it.
                longint n   = longint'((checked_at - released_at) / 10ns);
                string  ran = $sformatf("the run phase ended after %0d clocks of clk, with no run timeout", n);
                string  ran_before = $sformatf("the run phase ended after %0d clocks of clk, with no run timeout", n - 1);
                if (timeouts.demoted != 0) `uvm_error("LB_GEN", $sformatf("expected no A2C_RUN_TIMEOUT, got %p", timeouts.messages))
                if (infos.messages.size() != 1 || !(a2c_contains(infos.messages[0], ran) || a2c_contains(infos.messages[0], ran_before))) begin
                    `uvm_error("LB_GEN", $sformatf("expected one A2C_RUN_TIMEOUT info containing '%s', got %p", ran, infos.messages))
                end
            end else if (timeouts.demoted != 1) begin
                `uvm_error("LB_GEN", $sformatf("expected one A2C_RUN_TIMEOUT, got %0d: %p", timeouts.demoted, timeouts.messages))
            end else begin
                if (timeouts.at[0] != want_at) `uvm_error("LB_GEN", $sformatf("A2C_RUN_TIMEOUT at %0t, expected %0t", timeouts.at[0], want_at))
                if (checked_at != want_at + check_after) begin
                    `uvm_error("LB_GEN", $sformatf("check_phase ran at %0t, expected %0t after the timeout, %0t", checked_at, check_after, want_at + check_after))
                end
                if (!a2c_contains(timeouts.messages[0], head) || !a2c_contains(timeouts.messages[0], tail)) begin
                    `uvm_error("LB_GEN", $sformatf("A2C_RUN_TIMEOUT reads '%s', expected '%s...%s'", timeouts.messages[0], head, tail))
                end
                if (infos.messages.size() != want_late.size()) begin
                    `uvm_error("LB_GEN", $sformatf("expected %0d A2C_RUN_TIMEOUT infos after the timeout, got %p", want_late.size(), infos.messages))
                end else begin
                    foreach (want_late[i]) begin
                        string late = $sformatf("the run timeout, which expired at %0t, ended the %s", want_at, want_late[i]);
                        if (infos.messages[i] != late) `uvm_error("LB_GEN", $sformatf("A2C_RUN_TIMEOUT info reads '%s', expected '%s'", infos.messages[i], late))
                    end
                end
                if (clause_in_step != "" || a2c_contains(death_in_step, "A2C_RUN_TIMEOUT")) begin
                    `uvm_error("LB_GEN", $sformatf("a report in the timeout's own time step would cite it: clause '%s', death context '%s'", clause_in_step, death_in_step))
                end
                if (cmps.count(cut) != want_cmp.size()) `uvm_error("LB_GEN", $sformatf("A2C_MODEL_CMP does not name the timeout ('%s'): %p", cut, cmps.messages))
                if (n_declared != 0 && counts.count(cut) != (n_extra == 0)) begin
                    `uvm_error("LB_GEN", $sformatf("A2C_TXN_COUNT names the timeout ('%s') %0d times, expected %0d: %p", cut, counts.count(cut), n_extra == 0, counts.messages))
                end
                if (n_recorded != 0 && replays.count(cut) != 1) `uvm_error("LB_GEN", $sformatf("A2C_REPLAY does not name the timeout ('%s'): %p", cut, replays.messages))
            end
            if (extracts != 1 || checks != 1) `uvm_error("LB_GEN", $sformatf("extract_phase ran %0d times and check_phase %0d, expected once each", extracts, checks))
            if (counts.demoted != (n_declared != 0)) `uvm_error("LB_GEN", $sformatf("expected %0d A2C_TXN_COUNT, got %p", n_declared != 0, counts.messages))
            if (n_declared != 0 && n_extra == 0 && counts.count($sformatf("end of test with %0d of %0d expected transactions outstanding", n_declared, n_declared)) != 1) begin
                `uvm_error("LB_GEN", $sformatf("A2C_TXN_COUNT does not report the %0d missing transactions: %p", n_declared, counts.messages))
            end
            if (n_extra != 0 && counts.count($sformatf("end of test: received %0d transactions, expected %0d (%0d extra)", n_declared + n_extra, n_declared, n_extra)) != 1) begin
                `uvm_error("LB_GEN", $sformatf("A2C_TXN_COUNT does not report the %0d extra transactions: %p", n_extra, counts.messages))
            end
            if (replays.demoted != (n_recorded != 0)) `uvm_error("LB_GEN", $sformatf("expected %0d A2C_REPLAY, got %p", n_recorded != 0, replays.messages))
            if (n_recorded != 0 && replays.count($sformatf("end of test with %0d responses the DUT lane recorded and the model lane never replayed", n_recorded)) != 1) begin
                `uvm_error("LB_GEN", $sformatf("A2C_REPLAY does not report the %0d unreplayed responses: %p", n_recorded, replays.messages))
            end
            if (joints.demoted != want_joint) `uvm_error("LB_GEN", $sformatf("expected %0d A2C_JOINT_STALL, got %p", want_joint, joints.messages))
            if (cmps.demoted != want_cmp.size()) `uvm_error("LB_GEN", $sformatf("expected %0d A2C_MODEL_CMP, got %p", want_cmp.size(), cmps.messages))
            foreach (want_cmp[i]) if (cmps.count(want_cmp[i]) != 1) `uvm_error("LB_GEN", $sformatf("no A2C_MODEL_CMP reads '%s': %p", want_cmp[i], cmps.messages))
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
        endfunction
    endclass : gen_base_run_timeout_mode_a_test

    // Mode B: both lanes wait, and the joint stall bound, at its default,
    // is far off.
    class gen_base_run_timeout_mode_b_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b     = 1;
            n_recorded = 2;
            want_ports = "rv (uvm_test_top.env.rv_agent.drv), both lanes waiting for the transfer of ";
        endfunction
    endclass : gen_base_run_timeout_mode_b_test

    // Mode B: the joint stall declares both lanes of rv dead, its item
    // completes, and run_body() then waits for nothing that comes. rv's
    // lanes waited on its last clock but are dead, so no port is named.
    class gen_base_run_timeout_dead_port_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_dead_port_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b             = 1;
            joint_stall_cycles = 100;
            want_joint         = 1;
            want_ports         = "none";
        endfunction
    endclass : gen_base_run_timeout_dead_port_test

    // The base test returns from wait_for_outputs(), and holder's objection
    // keeps the run phase going: the timeout counts on, names holder alone
    // and no port.
    class gen_base_run_timeout_objection_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_objection_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold                 = 1;
            n_items              = 0;
            n_declared           = 0;
            quiet_cycles         = 20;
            no_stimulus_expected = 1;
            want_ports           = "none";
            want_objectors       = "uvm_test_top.env.holder";
        endfunction
    endclass : gen_base_run_timeout_objection_test

    // +a2c_run_timeout_cycles=300 overrides the 500 the constructor sets.
    // LB_PLUSARGS gen_base_run_timeout_plusarg_test +a2c_run_timeout_cycles=300
    class gen_base_run_timeout_plusarg_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_plusarg_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_cycles = 300;
        endfunction
    endclass : gen_base_run_timeout_plusarg_test

    // run_timeout_cycles 0 turns the timeout off: holder releases the run
    // phase 2000 clocks after the reset release, with no A2C_RUN_TIMEOUT.
    class gen_base_run_timeout_off_test extends gen_base_run_timeout_objection_test;
        `uvm_component_utils(gen_base_run_timeout_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold               = 0;
            run_timeout_cycles = 0;
            want_cycles        = 0;
        endfunction

        virtual task run_body();
            repeat (2000) @(posedge env.clk_vif.clk);
        endtask
    endclass : gen_base_run_timeout_off_test

    // The derived budget: 2 items sent on lb_in and 3 transactions declared
    // on lb_out make the work 5, so the timeout comes at 200 + 10 x 5.
    class gen_base_run_timeout_derived_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_derived_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_sent = 2;
            derive(200, 10, 5, 2);
        endfunction
    endclass : gen_base_run_timeout_derived_test

    // The plusargs override the floor and factor the constructor sets: the
    // timeout comes at 100 + 20 x 5.
    // LB_PLUSARGS gen_base_run_timeout_derived_plusarg_test +a2c_run_timeout_floor_cycles=100 +a2c_run_timeout_factor=20
    class gen_base_run_timeout_derived_plusarg_test extends gen_base_run_timeout_derived_test;
        `uvm_component_utils(gen_base_run_timeout_derived_plusarg_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            derive(200, 10, 5, 2);
            want_cycles = 100 + 20 * 5;
            want_how    = "The budget is run_timeout_floor_cycles 100 + run_timeout_factor 20 x 5, the work the test has declared (input items sent 2, output transactions expected 3)";
        endfunction
    endclass : gen_base_run_timeout_derived_plusarg_test

    // The budget grows with the stimulus: 30 items on lb_in, 10 clocks
    // apart, then rv blocks. The floor's 200 clocks see 20 items, so the
    // budget becomes 400; by then all 30 are sent, so it becomes 500, where
    // the timeout comes.
    class gen_base_run_timeout_grow_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_grow_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_sent     = 30;
            gap        = 10;
            n_declared = 0;
            derive(200, 10, 30, 30);
        endfunction
    endclass : gen_base_run_timeout_grow_test

    // A test that fixes the budget from run_body() overrides the derived
    // one, here lowering it from 1000 + 10 x 5 to 300.
    class gen_base_run_timeout_fix_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_fix_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_sent = 2;
            derive(1000, 10, 5, 2);
            want_cycles = 300;
            want_how    = "The budget is fixed by run_timeout.fix() in the test";
            want_raise  = "Raise run_timeout_cycles, or the value the test passes to fix(), if the test is legitimately longer.";
        endfunction

        virtual task run_body();
            run_timeout.fix(300);
            super.run_body();
        endtask
    endclass : gen_base_run_timeout_fix_test

    // fix() from run_body() overrides run_timeout_cycles, 500, which
    // mode_a's constructor sets.
    class gen_base_run_timeout_fix_knob_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_fix_knob_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_cycles = 300;
            want_how    = "The budget is fixed by run_timeout.fix() in the test";
        endfunction

        virtual task run_body();
            run_timeout.fix(300);
            super.run_body();
        endtask
    endclass : gen_base_run_timeout_fix_knob_test

    // +a2c_run_timeout_cycles wins over fix().
    // LB_PLUSARGS gen_base_run_timeout_fix_plusarg_test +a2c_run_timeout_cycles=400
    class gen_base_run_timeout_fix_plusarg_test extends gen_base_run_timeout_fix_test;
        `uvm_component_utils(gen_base_run_timeout_fix_plusarg_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_cycles = 400;
            want_how    = "The budget is fixed by run_timeout_cycles (+a2c_run_timeout_cycles)";
        endfunction
    endclass : gen_base_run_timeout_fix_plusarg_test

    // fix() from build_phase, after super.build_phase() has read the knobs,
    // still fixes the budget.
    class gen_base_run_timeout_fix_build_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_fix_build_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_sent = 2;
            derive(1000, 10, 5, 2);
            want_cycles = 300;
            want_how    = "The budget is fixed by run_timeout.fix() in the test";
            want_raise  = "Raise run_timeout_cycles, or the value the test passes to fix(), if the test is legitimately longer.";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            run_timeout.fix(300);
        endfunction
    endclass : gen_base_run_timeout_fix_build_test

    // holder holds main_phase as well as run_body() waiting: the timeout
    // names main_phase's objector, ends main_phase too, and extract_phase
    // and check_phase run once each.
    class gen_base_run_timeout_main_phase_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_main_phase_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold_main      = 1;
            want_objectors = "uvm_test_top; main phase: uvm_test_top.env.holder";
        endfunction
    endclass : gen_base_run_timeout_main_phase_test

    // A runtime phase of another domain: holder2 holds the main_phase of
    // lb_domain as well, and both main phases end at the timeout.
    class gen_base_run_timeout_domain_test extends gen_base_run_timeout_mode_a_test;
        lb_gen_holder holder2;

        `uvm_component_utils(gen_base_run_timeout_domain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold_main      = 1;
            want_objectors = "uvm_test_top; main phase of domain lb_domain: uvm_test_top.holder2; main phase: uvm_test_top.env.holder";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_domain domain = new("lb_domain");
            super.build_phase(phase);
            holder2           = lb_gen_holder::type_id::create("holder2", this);
            holder2.hold_main = 1;
            holder2.set_domain(domain);
        endfunction
    endclass : gen_base_run_timeout_domain_test

    // The timeout comes in reset_phase, which holder holds: reset_phase
    // ends, and main_phase, which begins after it, ends as it begins
    // although holder objects in it for 1 us, so check_phase runs at the
    // timeout.
    class gen_base_run_timeout_reset_phase_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_reset_phase_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_objectors = "uvm_test_top; reset phase: uvm_test_top.env.holder";
            want_late      = '{"main phase as it began. Objections raised by: uvm_test_top.env.holder"};
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            lb_gen_hang_env e;
            super.connect_phase(phase);
            void'($cast(e, env));
            e.holder.hold_reset = 1;
            e.holder.main_for   = 1us;
        endfunction

        virtual function void report_phase(uvm_phase phase);
            lb_gen_hang_env e;
            void'($cast(e, env));
            if (e.holder.main_done) `uvm_error("LB_GEN", "main_phase, which began after the timeout, ran in full")
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_reset_phase_test

    // holder holds main_phase, which the timeout ends, and then
    // shutdown_phase for ever, which ends as it begins.
    class gen_base_run_timeout_shutdown_phase_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_shutdown_phase_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold_main      = 1;
            want_objectors = "uvm_test_top; main phase: uvm_test_top.env.holder";
            want_late      = '{"shutdown phase as it began. Objections raised by: uvm_test_top.env.holder"};
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            lb_gen_hang_env e;
            super.connect_phase(phase);
            void'($cast(e, env));
            e.holder.hold_shutdown = 1;
        endfunction
    endclass : gen_base_run_timeout_shutdown_phase_test

    // A user-defined task phase, lb_custom_phase, between main_phase and
    // post_main_phase of UVM's schedule: holder holds it at the timeout,
    // which names and ends it. A user-defined function phase,
    // lb_func_phase, follows it, which the timeout leaves to run: UVM
    // reports each phase it ends as a PH_JUMP info, which names custom and
    // not func.
    class gen_base_run_timeout_custom_phase_test extends gen_base_run_timeout_mode_a_test;
        lb_info_recorder jumps;

        `uvm_component_utils(gen_base_run_timeout_custom_phase_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            uvm_domain::get_uvm_schedule().add(lb_custom_phase::get(), .after_phase(uvm_main_phase::get()), .before_phase(uvm_post_main_phase::get()));
            uvm_domain::get_uvm_schedule().add(lb_func_phase::get(), .after_phase(lb_custom_phase::get()), .before_phase(uvm_post_main_phase::get()));
            want_objectors = "uvm_test_top; custom phase: uvm_test_top.env.holder";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_root::get().set_report_id_verbosity("PH_JUMP", UVM_MEDIUM);
            jumps    = lb_info_recorder::type_id::create("jumps");
            jumps.id = "PH_JUMP";
            uvm_report_cb::add(null, jumps);
            super.build_phase(phase);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            lb_gen_hang_env e;
            super.connect_phase(phase);
            void'($cast(e, env));
            e.holder.hold_custom = 1;
        endfunction

        virtual function void report_phase(uvm_phase phase);
            int unsigned custom = 0;
            int unsigned func = 0;
            foreach (jumps.messages[i]) begin
                custom += a2c_contains(jumps.messages[i], "phase custom (");
                func   += a2c_contains(jumps.messages[i], "phase func (");
            end
            if (custom != 1 || func != 0) begin
                `uvm_error("LB_GEN", $sformatf("expected a PH_JUMP for custom and none for func, got %0d and %0d: %p", custom, func, jumps.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_custom_phase_test

    // A user-defined task phase of the common schedule, lb_late_phase,
    // after the run phase, which holder holds: the timeout ends it as it
    // begins, as it would a runtime phase.
    class gen_base_run_timeout_common_phase_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_common_phase_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            uvm_domain::get_common_domain().add(lb_late_phase::get(), .after_phase(uvm_run_phase::get()), .before_phase(uvm_extract_phase::get()));
            want_late = '{"late phase of domain common as it began. Objections raised by: uvm_test_top.env.holder"};
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            lb_gen_hang_env e;
            super.connect_phase(phase);
            void'($cast(e, env));
            e.holder.hold_late = 1;
        endfunction
    endclass : gen_base_run_timeout_common_phase_test

    // Mode B: the timeout comes while the drain waits for the model lane to
    // replay the 2 responses the DUT lane recorded. The drain's objection
    // is named, the drain ends with the run phase and drops nothing after,
    // and A2C_REPLAY names the timeout.
    class gen_base_run_timeout_drain_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b               = 1;
            n_recorded           = 2;
            n_items              = 0;
            n_declared           = 0;
            quiet_cycles         = 20;
            no_stimulus_expected = 1;
            want_ports           = "none";
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            want_objectors = env.replay.get_full_name();
        endfunction
    endclass : gen_base_run_timeout_drain_test

    // An A2C_RUN_TIMEOUT info, with its time.
    class lb_timed_info_recorder extends lb_info_recorder;
        realtime at[$];

        `uvm_object_utils(lb_timed_info_recorder)

        function new(string name = "lb_timed_info_recorder");
            super.new(name);
        endfunction

        virtual function action_e catch();
            int unsigned n = messages.size();
            action_e     a = super.catch();
            if (messages.size() != n) at.push_back($realtime);
            return a;
        endfunction
    endclass : lb_timed_info_recorder

    // The run timeout's one deferral to the progress rules counting at its
    // budget, on lb_gen_hang_env with a derived budget of 100 + 10 x W and
    // a clock stop of 20, which every rule's deferral covers, so a rule on
    // clk reports 21 clocks and the margin before the timeout; the default
    // rule_slack allows that and 3 more. run_body() is each test's own.
    // Checks:
    //   - want_defers deferral infos, 1 or 0, the one at the budget of
    //     want_budget clocks, naming want_rule;
    //   - with rule_id set, that the rule's first error, or warning with
    //     rule_severity UVM_WARNING, came after the budget, and with
    //     want_timeout, before the timeout, by at most the margin and
    //     rule_slack clocks, and want_rule_errors errors of them;
    //   - one A2C_RUN_TIMEOUT error with want_timeout, and none without;
    //   - that extract_phase and check_phase run once each.
    class lb_gen_defer_base extends lb_gen_base;
        bit                    mode_b;
        bit                    hold;
        string                 rule_id;
        int unsigned           want_rule_errors = 1;
        string                 want_rule;
        bit                    want_timeout = 1;
        int unsigned           want_budget = 100;
        int unsigned           want_defers = 1;
        int unsigned           rule_slack = 24;
        uvm_severity           rule_severity = UVM_ERROR;
        lb_timed_demoter       timeouts;
        lb_timed_demoter       rules;
        lb_timed_info_recorder infos;
        lb_recording_demoter   others[$];
        realtime               released_at;
        int unsigned           extracts;
        int unsigned           checks;

        `uvm_component_utils(lb_gen_defer_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            lb_gen_env::type_id::set_type_override(lb_gen_hang_env::get_type());
            quiet_cycles             = 5;
            clock_stop_cycles        = 20;
            run_timeout_floor_cycles = 100;
            run_timeout_factor       = 10;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            string ids[$] = '{"A2C_TXN_COUNT", "A2C_JOINT_STALL", "A2C_REPLAY"};
            if (rule_id != "" && !(rule_id inside {ids})) ids.push_back(rule_id);
            timeouts = lb_timed_demoter::type_id::create("demote_A2C_RUN_TIMEOUT");
            timeouts.demote_id = "A2C_RUN_TIMEOUT";
            uvm_report_cb::add(null, timeouts);
            foreach (ids[i]) begin
                if (ids[i] == rule_id) begin
                    rules = lb_timed_demoter::type_id::create({"demote_", rule_id});
                    rules.demote_id = rule_id;
                    rules.severity  = rule_severity;
                    uvm_report_cb::add(null, rules);
                end else begin
                    lb_recording_demoter d = lb_recording_demoter::type_id::create({"demote_", ids[i]});
                    d.demote_id = ids[i];
                    uvm_report_cb::add(null, d);
                    others.push_back(d);
                end
            end
            infos    = lb_timed_info_recorder::type_id::create("infos");
            infos.id = "A2C_RUN_TIMEOUT";
            uvm_report_cb::add(null, infos);
            uvm_config_db#(bit)::set(this, "env", "lb_mode_b", mode_b);
            super.build_phase(phase);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            lb_gen_hang_env e;
            super.connect_phase(phase);
            void'($cast(e, env));
            e.holder.hold = hold;
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    env.clk_vif.wait_reset_release();
                    released_at = $realtime;
                end
            join_none
            super.run_phase(phase);
        endtask

        // Sends one item on rv, which never transfers, and waits for ever.
        protected task hang_rv();
            lb_gen_hang_env e;
            lb_list_seq#(rv_item_t) seq = new("seq");
            rv_item_t it = rv_item_t::type_id::create("it");
            void'($cast(e, env));
            it.data = '{tag: 4'h3, value: 20'h5};
            seq.items.push_back(it);
            seq.start(e.rv_agent.sqr);
            wait (0);
        endtask

        virtual function void extract_phase(uvm_phase phase);
            extracts++;
            super.extract_phase(phase);
        endfunction

        virtual function void check_phase(uvm_phase phase);
            checks++;
            super.check_phase(phase);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned      defers = 0;
            realtime          defer_at = -1;
            `uvm_info("LB_STATS", $sformatf("released at %0t; A2C_RUN_TIMEOUT at %p: %p; %s at %p; infos %p at %p", released_at, timeouts.at,
                                            timeouts.messages, rule_id, (rules == null) ? "{}" : $sformatf("%p", rules.at), infos.messages, infos.at), UVM_NONE)
            foreach (infos.messages[i]) begin
                if (!a2c_contains(infos.messages[i], "The run timeout defers to them, once")) continue;
                defers++;
                defer_at = infos.at[i];
                if (!a2c_contains(infos.messages[i], want_rule)) `uvm_error("LB_GEN", $sformatf("the deferral does not name '%s': %s", want_rule, infos.messages[i]))
            end
            if (defers != want_defers) `uvm_error("LB_GEN", $sformatf("expected %0d deferral info, got %0d: %p", want_defers, defers, infos.messages))
            if (defer_at >= 0 && defer_at != released_at + 10ns * want_budget) begin
                `uvm_error("LB_GEN", $sformatf("the deferral came at %0t, not at the budget of %0d clocks", defer_at, want_budget))
            end
            if (timeouts.demoted != want_timeout) `uvm_error("LB_GEN", $sformatf("expected %0d A2C_RUN_TIMEOUT, got %p", want_timeout, timeouts.messages))
            if (rules != null) begin
                if (rules.demoted != want_rule_errors) `uvm_error("LB_GEN", $sformatf("expected %0d %s, got %p", want_rule_errors, rule_id, rules.messages))
                if (rules.at.size() != 0 && rules.at[0] <= defer_at) `uvm_error("LB_GEN", $sformatf("%s came at %0t, before the budget", rule_id, rules.at[0]))
                if (want_timeout && rules.at.size() != 0 && timeouts.at.size() != 0
                    && !(rules.at[0] < timeouts.at[0] && timeouts.at[0] - rules.at[0] <= 10ns * (A2C_RUN_TIMEOUT_DEFER_MARGIN + rule_slack))) begin
                    `uvm_error("LB_GEN", $sformatf("%s at %0t is not just before the timeout at %0t", rule_id, rules.at[0], timeouts.at[0]))
                end
            end
            if (extracts != 1 || checks != 1) `uvm_error("LB_GEN", $sformatf("extract_phase ran %0d times and check_phase %0d, expected once each", extracts, checks))
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
        endfunction
    endclass : lb_gen_defer_base

    // Scenario (a) for the output deadline: run_body() configures for 50
    // clocks, then waits for 3 transactions that never come, with a
    // deadline of 300, past the budget of 130. The deadline reports first,
    // and holder then keeps the run phase until the deferral ends, which
    // also covers a clock stop of 20, so the report may come that much and
    // a clock earlier.
    class gen_base_run_timeout_defer_output_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_output_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold                   = 1;
            clock_stop_cycles      = 20;
            rule_slack             = 24;
            output_deadline_cycles = 300;
            want_budget            = 130;
            rule_id                = "A2C_TXN_COUNT";
            want_rule              = "the output deadline of lb_out (uvm_test_top.env.lb_out_counter)";
        endfunction

        virtual task run_body();
            repeat (50) @(posedge env.clk_vif.clk);
            env.lb_out_counter.expect_count(3);
            wait_for_outputs();
        endtask
    endclass : gen_base_run_timeout_defer_output_test

    // As defer_output with the wait on clk3, of twice clk's period, and a
    // clock stop of 100: run_body() stops clk3 just before the budget of
    // 130, when the deadline has 6 clocks of clk3 left, so the counter
    // reports the stop 100.5 clocks of clk3 after clk3's last falling
    // edge, past the deadline, and the deferral must cover that. The
    // deferral counts 6 + 100 + 1 clocks of clk3 from the budget, and the
    // report comes 14.5 clocks of clk before that: the deadline's 6
    // unused clocks of clk3 are 12, the stop's half clock of clk3 against
    // the deferral's whole one is 1, and the last falling edge came 1.5
    // before the budget.
    class gen_base_run_timeout_defer_stopped_test extends lb_gen_defer_base;
        virtual a2c_clk_if clk3_vif;

        `uvm_component_utils(gen_base_run_timeout_defer_stopped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            hold              = 1;
            clock_stop_cycles = 100;
            want_budget       = 130;
            rule_slack        = 15;
            rule_id           = "A2C_TXN_COUNT";
            want_rule         = "the output deadline of lb_out (uvm_test_top.env.lb_out_counter)";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
        endfunction

        virtual task run_body();
            repeat (50) @(posedge env.clk_vif.clk);
            env.lb_out_counter.expect_count(3);
            fork
                begin
                    repeat (78) @(posedge env.clk_vif.clk);
                    lb_clk3_run = 0;
                end
            join_none
            env.lb_out_counter.wait_for_count(clk3_vif, 45, quiet_cycles);
        endtask

        virtual function void report_phase(uvm_phase phase);
            if (rules.count("the clock stopped") != 1) `uvm_error("LB_GEN", $sformatf("expected one report of the stopped clock: %p", rules.messages))
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_stopped_test

    // Scenario (a) for a lane rule: in Mode B rv's lanes both wait, and the
    // joint stall bound of 300, set on rv's master through the config_db,
    // runs past the budget of 100. The joint stall reports first.
    class gen_base_run_timeout_defer_joint_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_joint_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b               = 1;
            no_stimulus_expected = 1;
            rule_id              = "A2C_JOINT_STALL";
            want_rule            = "the joint stall rule (joint_stall_cycles) of rv (uvm_test_top.env.rv_agent.drv)";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            uvm_config_db#(int unsigned)::set(this, "env.rv_agent.drv", "a2c_joint_stall_cycles", joint_bound());
        endfunction

        protected virtual function int unsigned joint_bound();
            return 300;
        endfunction

        virtual task run_body();
            hang_rv();
        endtask
    endclass : gen_base_run_timeout_defer_joint_test

    // As defer_joint with rv on clk2, of three times clk's period: the
    // joint stall bound of 100 clocks of clk2 is 300 clocks of clk, which
    // the deferral counts, and so are the 21 clocks of clk2 it covers for a
    // clock stop, 63 of clk.
    class gen_base_run_timeout_defer_clk2_test extends gen_base_run_timeout_defer_joint_test;
        `uvm_component_utils(gen_base_run_timeout_defer_clk2_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            rule_slack = 66;
        endfunction

        protected virtual function int unsigned joint_bound();
            return 100;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            lb_gen_hang_env e;
            super.connect_phase(phase);
            void'($cast(e, env));
            e.rv_agent.cfg.clk_vif = env.clk2_vif;
        endfunction
    endclass : gen_base_run_timeout_defer_clk2_test

    // Scenario (a) for the lane skew rule on rdy_vld, a master that counts
    // its lanes' steps: in Mode B the model lane takes rv's one item and
    // the DUT lane never does, so the DUT lane trails until the skew
    // bound of 300, set on rv's master through the config_db, declares it
    // dead, past the budget of 100.
    class gen_base_run_timeout_defer_skew_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_skew_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b               = 1;
            no_stimulus_expected = 1;
            rule_id              = "A2C_SKEW";
            want_rule            = "the lane skew rule (lane_skew_cycles) of rv (uvm_test_top.env.rv_agent.drv)";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            uvm_config_db#(int unsigned)::set(this, "env.rv_agent.drv", "a2c_lane_skew_cycles", 300);
        endfunction

        virtual task run_body();
            lb_gen_hang_env e;
            void'($cast(e, env));
            e.rv_agent.cfg.model_vif.rdy <= 1'b1;
            hang_rv();
        endtask
    endclass : gen_base_run_timeout_defer_skew_test

    // Scenario (a) for the lone lane rule on rdy_vld: in Mode B the model
    // lane takes rv's first item and the DUT lane, 20 clocks behind, is
    // declared dead by the skew bound before the budget of 100. The model
    // lane, alone, never takes the second item, so the lone lane bound of
    // 300 runs past the budget. The first A2C_SKEW, the DUT lane's death,
    // is left out of the timing checks.
    class gen_base_run_timeout_defer_lone_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_lone_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b               = 1;
            no_stimulus_expected = 1;
            rule_id              = "A2C_SKEW";
            want_rule_errors     = 2;
            want_rule            = "the lone lane rule (lone_lane_cycles) of rv (uvm_test_top.env.rv_agent.drv)";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            uvm_config_db#(int unsigned)::set(this, "env.rv_agent.drv", "a2c_lane_skew_cycles", 20);
            uvm_config_db#(int unsigned)::set(this, "env.rv_agent.drv", "a2c_lone_lane_cycles", 300);
        endfunction

        virtual task run_body();
            lb_gen_hang_env e;
            rv_vif_t        m;
            lb_list_seq#(rv_item_t) seq = new("seq");
            void'($cast(e, env));
            m = e.rv_agent.cfg.model_vif;
            for (int i = 0; i < 2; i++) begin
                rv_item_t it = rv_item_t::type_id::create("it");
                it.data = '{tag: 4'h3, value: 20'(i)};
                seq.items.push_back(it);
            end
            m.rdy <= 1'b1;
            fork
                begin
                    do @(posedge env.clk_vif.clk); while (!(m.vld === 1'b1 && m.rdy === 1'b1));
                    m.rdy <= 1'b0;
                end
            join_none
            seq.start(e.rv_agent.sqr);
            wait (0);
        endtask

        virtual function void report_phase(uvm_phase phase);
            if (rules.messages.size() != 2 || !a2c_contains(rules.messages[0], "has not completed") || !a2c_contains(rules.messages[1], "alone since")) begin
                `uvm_error("LB_GEN", $sformatf("expected the DUT lane's skew death, then the model lane's lone stall: %p", rules.messages))
            end
            if (rules.at.size() != 0) rules.at.delete(0);
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_lone_test

    // A lane rule whose clock pauses short of a stop still reports first:
    // as defer_joint with rv on clk3, of twice clk's period, and a joint
    // stall bound of 100 clocks of clk3, run_body() stops clk3 at clock 90
    // of clk and starts it again 30 clocks later, 15 of clk3's periods,
    // short of the 20.5 that make a stop. clk3 stays stopped for 10 of its
    // periods past the budget of 100, so the joint stall, counting then,
    // reports that much later than its clocks left at the budget give. The
    // deferral's 21 clocks of clk3 for a clock stop cover that, and the
    // report comes 11 clocks of clk3 and the margin before the timeout.
    class gen_base_run_timeout_defer_dog_paused_test extends gen_base_run_timeout_defer_joint_test;
        virtual a2c_clk_if clk3_vif;
        int unsigned       bound = 100;
        int unsigned       pause_at = 90;
        // 0 leaves clk3 stopped.
        int unsigned       pause_for = 30;
        // Above 0, rv runs on clk9 instead, which stops for good on the
        // rising edge this long before the budget, and the pause knobs are
        // unused.
        realtime           stop_gap;

        `uvm_component_utils(gen_base_run_timeout_defer_dog_paused_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected virtual function int unsigned joint_bound();
            return bound;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", (stop_gap > 0) ? "clk9" : "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3' or 'clk9'")
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            lb_gen_hang_env e;
            super.connect_phase(phase);
            void'($cast(e, env));
            e.rv_agent.cfg.clk_vif = clk3_vif;
        endfunction

        virtual task run_body();
            if (stop_gap > 0) fork
                begin
                    realtime stop_at;
                    wait (released_at > 0);
                    stop_at = released_at + 10ns * want_budget - stop_gap;
                    do @(posedge clk3_vif.clk); while ($realtime < stop_at);
                    lb_clk9_run = 0;
                    if ($realtime != stop_at) `uvm_fatal("LB_GEN", $sformatf("clk9 rose at %0t, not at %0t", $realtime, stop_at))
                end
            join_none
            else fork
                begin
                    repeat (pause_at) @(posedge env.clk_vif.clk);
                    lb_clk3_run = 0;
                    if (pause_for != 0) begin
                        repeat (pause_for) @(posedge env.clk_vif.clk);
                        lb_clk3_run = 1;
                    end
                end
            join_none
            hang_rv();
        endtask
    endclass : gen_base_run_timeout_defer_dog_paused_test

    // A lane rule whose clock has stopped is left out: as defer_dog_paused
    // with a clock stop of 10 and a joint stall bound of 300 clocks of
    // clk3, clk3 stops at clock 60 for good, so at the budget of 100 it
    // has not risen for 20 of its periods, and the joint stall, which
    // cannot count on, gets no deferral. The timeout comes at the budget
    // and names the joint stall as left out.
    class gen_base_run_timeout_defer_dog_stopped_test extends gen_base_run_timeout_defer_dog_paused_test;
        `uvm_component_utils(gen_base_run_timeout_defer_dog_stopped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            clock_stop_cycles = 10;
            bound             = 300;
            pause_at          = 60;
            pause_for         = 0;
            want_defers       = 0;
            want_rule_errors  = 0;
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (timeouts.at.size() != 1 || timeouts.at[0] != released_at + 10ns * 100) begin
                `uvm_error("LB_GEN", $sformatf("expected the timeout at the budget of 100 clocks, at %0t: %p", released_at + 10ns * 100, timeouts.at))
            end
            if (timeouts.messages.size() != 0 && !a2c_contains(timeouts.messages[0], "Left out, clock stopped: the joint stall rule (joint_stall_cycles) of rv")) begin
                `uvm_error("LB_GEN", $sformatf("the timeout does not name the joint stall as left out: %s", timeouts.messages[0]))
            end
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_dog_stopped_test

    // The stop boundary, from the side that reads as stopped: as
    // defer_dog_stopped on clk9, whose last rising edge comes 10.5 of its
    // periods, the stop limit exactly, before the budget.
    class gen_base_run_timeout_defer_dog_stop_edge_test extends gen_base_run_timeout_defer_dog_stopped_test;
        `uvm_component_utils(gen_base_run_timeout_defer_dog_stop_edge_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            stop_gap = 210ns;
        endfunction
    endclass : gen_base_run_timeout_defer_dog_stop_edge_test

    // The stop boundary, from the side that does not: clk9's last rising
    // edge comes 10 of its periods before a budget of 101, half a period
    // short of a stop, so the joint stall is counted and the run timeout
    // defers to it. clk9 never returns, so the timeout comes at the end of
    // the deferral and leaves no rule out.
    class gen_base_run_timeout_defer_dog_stop_short_test extends gen_base_run_timeout_defer_dog_paused_test;
        `uvm_component_utils(gen_base_run_timeout_defer_dog_stop_short_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            clock_stop_cycles        = 10;
            bound                    = 300;
            stop_gap                 = 200ns;
            run_timeout_floor_cycles = 101;
            want_budget              = 101;
            want_rule_errors         = 0;
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (timeouts.messages.size() != 0 && a2c_contains(timeouts.messages[0], "Left out")) begin
                `uvm_error("LB_GEN", $sformatf("the timeout leaves a rule out: %s", timeouts.messages[0]))
            end
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_dog_stop_short_test

    // Scenario (a) for the drain: in Mode B the model lane never replays
    // the 2 responses the DUT lane recorded, so the drain runs to its
    // deadline of 300, past the budget of 100, and gives up. The run phase
    // then ends with no timeout, and A2C_REPLAY reports the responses
    // without citing one.
    class gen_base_run_timeout_defer_drain_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b                 = 1;
            no_stimulus_expected   = 1;
            quiet_cycles           = 20;
            output_deadline_cycles = 300;
            drain_catchup_cycles   = 50;
            rule_id                = "A2C_REPLAY";
            want_rule              = "the drain deadline and catch-up of uvm_test_top.env.replay";
            want_timeout           = 0;
        endfunction

        virtual task run_body();
            repeat (2) env.replay.record(1'b1, 0);
        endtask

        virtual function void report_phase(uvm_phase phase);
            if (rules.count("A2C_RUN_TIMEOUT") != 0) `uvm_error("LB_GEN", $sformatf("A2C_REPLAY cites a timeout: %p", rules.messages))
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_drain_test

    // As defer_drain with the log on clk3, of twice clk's period, a clock
    // stop of 100, a drain deadline of 60 and a catch-up of 5: run_body()
    // stops clk3 just before the budget of 100, when the drain has about 18
    // clocks of clk3 left, so the drain gives the log up on the stopped
    // clock about 100.5 clocks of clk3 later, and the deferral must cover
    // that. The run phase then ends with no timeout.
    class gen_base_run_timeout_defer_drain_stopped_test extends gen_base_run_timeout_defer_drain_test;
        virtual a2c_clk_if clk3_vif;

        `uvm_component_utils(gen_base_run_timeout_defer_drain_stopped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            clock_stop_cycles     = 100;
            drain_deadline_cycles = 60;
            drain_catchup_cycles  = 5;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            env.replay.clk_vif = clk3_vif;
        endfunction

        virtual task run_body();
            fork
                begin
                    repeat (98) @(posedge env.clk_vif.clk);
                    lb_clk3_run = 0;
                end
            join_none
            super.run_body();
        endtask
    endclass : gen_base_run_timeout_defer_drain_stopped_test

    // The drain's deferral ends where it should: as defer_drain with a
    // catch-up of 5, the drain gives the log up at its deadline of 300
    // with an A2C_DRAIN warning, and the test then raises an objection
    // that holds the run phase, so the timeout comes at the end of the
    // deferral. The deferral counts the deadline left at the budget, the
    // catch-up, which a log given up at its deadline does not use, and 21
    // clocks for a clock stop, so the warning must come at most those 26
    // clocks, the margin and a clock before the timeout.
    class gen_base_run_timeout_defer_drain_held_test extends lb_gen_defer_base;
        bit held;

        `uvm_component_utils(gen_base_run_timeout_defer_drain_held_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b                 = 1;
            no_stimulus_expected   = 1;
            quiet_cycles           = 20;
            output_deadline_cycles = 300;
            drain_catchup_cycles   = 5;
            rule_id                = "A2C_DRAIN";
            rule_severity          = UVM_WARNING;
            want_rule_errors       = 0;
            rule_slack             = 27;
            want_rule              = "the drain deadline and catch-up of uvm_test_top.env.replay";
        endfunction

        virtual task run_body();
            repeat (2) env.replay.record(1'b1, 0);
        endtask

        // Called again once the drain drops its objection, after its
        // warning.
        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (held || phase.get_imp() != uvm_run_phase::get() || rules.at.size() == 0) return;
            held = 1;
            phase.raise_objection(this, "holds the run phase past the drain");
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (rules.at.size() != 1) `uvm_error("LB_GEN", $sformatf("expected one A2C_DRAIN warning, got them at %p", rules.at))
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_drain_held_test

    // A log that settles while the drain watches another gives the run
    // timeout nothing to defer to: as defer_drain_held with a second log,
    // replay2, on clk3, of twice clk's period, with nothing recorded, and
    // clk3 stopped at clock 10. The drain finds replay2's clock stopped
    // and settles the log before the budget of 100, so the deferral names
    // env.replay alone and ends where defer_drain_held's does.
    class gen_base_run_timeout_defer_drain_settled_test extends gen_base_run_timeout_defer_drain_held_test;
        virtual a2c_clk_if clk3_vif;
        lb_bit_log_t       replay2;

        `uvm_component_utils(gen_base_run_timeout_defer_drain_settled_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            lb_fake_lanes lanes = new();
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            replay2 = lb_bit_log_t::type_id::create("replay2", env);
            replay2.driver = lanes;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            replay2.clk_vif = clk3_vif;
        endfunction

        virtual task run_body();
            fork
                begin
                    repeat (10) @(posedge env.clk_vif.clk);
                    lb_clk3_run = 0;
                end
            join_none
            super.run_body();
        endtask

        virtual function void report_phase(uvm_phase phase);
            foreach (infos.messages[i]) begin
                if (a2c_contains(infos.messages[i], "replay2")) `uvm_error("LB_GEN", $sformatf("an info names the settled log: %s", infos.messages[i]))
            end
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_drain_settled_test

    // Scenario (b): a correct run. Its first frame waits for 3
    // transactions, which come at clock 200, with a deadline of 300 that
    // is counting at the budget of 130, then it lowers the deadline to 50
    // for a tail of 1 transaction. The run ends inside the deferral, with
    // no timeout and no rule error.
    class gen_base_run_timeout_defer_correct_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_correct_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            output_deadline_cycles = 300;
            want_budget            = 130;
            want_rule              = "the output deadline of lb_out (uvm_test_top.env.lb_out_counter)";
            want_timeout           = 0;
        endfunction

        protected task deliver(int unsigned n, int unsigned after);
            env.lb_out_counter.expect_count(n);
            fork
                begin
                    repeat (after) @(posedge env.clk_vif.clk);
                    repeat (n) env.lb_out_counter.analysis_export.write(lb_gen_item::type_id::create("out"));
                end
            join_none
            wait_for_outputs();
        endtask

        virtual task run_body();
            deliver(3, 200);
            output_deadline_cycles = 50;
            deliver(1, 10);
        endtask

        virtual function void report_phase(uvm_phase phase);
            foreach (others[i]) begin
                if (others[i].demote_id == "A2C_TXN_COUNT" && others[i].demoted != 0) `uvm_error("LB_GEN", $sformatf("an output reported a shortfall or an excess: %p", others[i].messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_correct_test

    // The deferral is used once: the output deadline counting at the
    // budget reports, then run_body() waits again with a deadline of 1000,
    // which is counting when the deferral ends. The timeout comes then,
    // and the second deadline never reports.
    class gen_base_run_timeout_defer_once_test extends gen_base_run_timeout_defer_output_test;
        `uvm_component_utils(gen_base_run_timeout_defer_once_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_rule_errors = 2;
        endfunction

        virtual task run_body();
            super.run_body();
            output_deadline_cycles = 1000;
            env.lb_out_counter.expect_count(3);
            wait_for_outputs();
        endtask

        // The first deadline's report and the end-of-test report of the
        // second wait's 3 transactions.
        virtual function void report_phase(uvm_phase phase);
            if (rules.count("deadline of") != 1 || rules.count("end of test with 3 of 3 expected transactions outstanding") != 1) begin
                `uvm_error("LB_GEN", $sformatf("expected one deadline report and one end-of-test report: %p", rules.messages))
            end
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_once_test

    // A wait_for_count() killed while it counts leaves no deadline for the
    // deferral: run_body() waits for 3 transactions with a deadline of
    // 1000 in a process it kills 20 clocks later, then waits for ever, so
    // the timeout comes at the budget of 130 with no deferral.
    class gen_base_run_timeout_defer_killed_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_killed_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_defers = 0;
        endfunction

        virtual task run_body();
            process p;
            repeat (50) @(posedge env.clk_vif.clk);
            env.lb_out_counter.expect_count(3);
            fork
                begin
                    p = process::self();
                    env.lb_out_counter.wait_for_count(env.clk_vif, 1000, quiet_cycles);
                end
            join_none
            repeat (20) @(posedge env.clk_vif.clk);
            p.kill();
            wait (0);
        endtask

        virtual function void report_phase(uvm_phase phase);
            if (timeouts.at.size() != 1 || timeouts.at[0] != released_at + 10ns * 130) begin
                `uvm_error("LB_GEN", $sformatf("expected the timeout at the budget of 130 clocks, at %0t: %p", released_at + 10ns * 130, timeouts.at))
            end
            super.report_phase(phase);
        endfunction
    endclass : gen_base_run_timeout_defer_killed_test

    // As defer_killed with the wait in a named block that another process
    // disables 20 clocks later, after which run_body()'s own process goes
    // on and waits for ever: the disable ends the deadline as the kill does.
    class gen_base_run_timeout_defer_disabled_test extends gen_base_run_timeout_defer_killed_test;
        `uvm_component_utils(gen_base_run_timeout_defer_disabled_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_body();
            repeat (50) @(posedge env.clk_vif.clk);
            env.lb_out_counter.expect_count(3);
            fork
                begin
                    repeat (20) @(posedge env.clk_vif.clk);
                    disable waiting;
                end
            join_none
            begin : waiting
                env.lb_out_counter.wait_for_count(env.clk_vif, 1000, quiet_cycles);
            end
            wait (0);
        endtask
    endclass : gen_base_run_timeout_defer_disabled_test

    // Two waits on one counter overlap: run_body() starts one with a
    // deadline of 40 at clock 50 and another with a deadline of 300 a
    // clock later. The first reports its shortfall before the budget and
    // then declares 3 transactions more, so the second goes on counting,
    // and the first's end must leave it counted at the budget of 160. It
    // reports inside the deferral, and the run ends with no timeout.
    class gen_base_run_timeout_defer_overlap_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_overlap_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_budget  = 160;
            want_timeout = 0;
            want_rule    = "the output deadline of lb_out (uvm_test_top.env.lb_out_counter)";
        endfunction

        virtual task run_body();
            repeat (50) @(posedge env.clk_vif.clk);
            env.lb_out_counter.expect_count(3);
            fork
                begin
                    env.lb_out_counter.wait_for_count(env.clk_vif, 40, quiet_cycles);
                    env.lb_out_counter.expect_count(3);
                end
            join_none
            @(posedge env.clk_vif.clk);
            env.lb_out_counter.wait_for_count(env.clk_vif, 300, quiet_cycles);
        endtask
    endclass : gen_base_run_timeout_defer_overlap_test

    // As defer_overlap with both waits counting at the budget of 130: the
    // first, on clk2 with a deadline of 50, has about 7 clocks of clk2
    // left then, and the second, on clk3 with a deadline of 150, about 87
    // clocks of clk3. clk2's last falling edge before the budget comes 10
    // ns after clk3's, so the first wait samples last, and the deferral
    // must still count the second's clocks left. The first reports its
    // shortfall after the budget and then declares 3 transactions more,
    // so the second goes on, reports inside the deferral, and the run
    // ends with no timeout.
    class gen_base_run_timeout_defer_overlap_left_test extends lb_gen_defer_base;
        virtual a2c_clk_if clk3_vif;

        `uvm_component_utils(gen_base_run_timeout_defer_overlap_left_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_budget  = 130;
            want_timeout = 0;
            want_rule    = "the output deadline of lb_out (uvm_test_top.env.lb_out_counter)";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
        endfunction

        virtual task run_body();
            env.lb_out_counter.expect_count(3);
            fork
                begin
                    env.lb_out_counter.wait_for_count(env.clk2_vif, 50, quiet_cycles);
                    env.lb_out_counter.expect_count(3);
                end
            join_none
            @(posedge env.clk_vif.clk);
            env.lb_out_counter.wait_for_count(clk3_vif, 150, quiet_cycles);
        endtask
    endclass : gen_base_run_timeout_defer_overlap_left_test

    // defer_overlap in the reverse order: run_body() starts a wait with a
    // deadline of 300 at clock 50 and one with a deadline of 40 a clock
    // later. The second reports its shortfall before the budget of 160 and
    // declares 3 transactions more, and its end must leave the first
    // counted, which reports inside the deferral.
    class gen_base_run_timeout_defer_overlap_reverse_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_overlap_reverse_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_budget  = 160;
            want_timeout = 0;
            want_rule    = "the output deadline of lb_out (uvm_test_top.env.lb_out_counter)";
        endfunction

        virtual task run_body();
            repeat (50) @(posedge env.clk_vif.clk);
            env.lb_out_counter.expect_count(3);
            fork
                begin
                    @(posedge env.clk_vif.clk);
                    env.lb_out_counter.wait_for_count(env.clk_vif, 40, quiet_cycles);
                    env.lb_out_counter.expect_count(3);
                end
            join_none
            env.lb_out_counter.wait_for_count(env.clk_vif, 300, quiet_cycles);
        endtask
    endclass : gen_base_run_timeout_defer_overlap_reverse_test

    // As defer_overlap_reverse with the later wait, deadline 1000, killed
    // 20 clocks after it starts: the kill must leave the first wait counted
    // at the budget of 130.
    class gen_base_run_timeout_defer_overlap_killed_test extends lb_gen_defer_base;
        `uvm_component_utils(gen_base_run_timeout_defer_overlap_killed_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_budget  = 130;
            want_timeout = 0;
            want_rule    = "the output deadline of lb_out (uvm_test_top.env.lb_out_counter)";
        endfunction

        virtual task run_body();
            process p;
            repeat (50) @(posedge env.clk_vif.clk);
            env.lb_out_counter.expect_count(3);
            fork
                begin
                    p = process::self();
                    @(posedge env.clk_vif.clk);
                    env.lb_out_counter.wait_for_count(env.clk_vif, 1000, quiet_cycles);
                end
                begin
                    repeat (21) @(posedge env.clk_vif.clk);
                    p.kill();
                end
            join_none
            env.lb_out_counter.wait_for_count(env.clk_vif, 300, quiet_cycles);
        endtask
    endclass : gen_base_run_timeout_defer_overlap_killed_test

    // The counter receives one transaction more than it expects; its
    // A2C_TXN_COUNT of the extra one does not name the timeout, which cannot
    // have caused it.
    class gen_base_run_timeout_over_test extends gen_base_run_timeout_mode_a_test;
        `uvm_component_utils(gen_base_run_timeout_over_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_declared = 1;
            n_extra    = 1;
        endfunction
    endclass : gen_base_run_timeout_over_test

    // Mode B: a comparator holds a DUT item the model lane never matched,
    // and its end-of-test report names the timeout.
    class gen_base_run_timeout_unpaired_test extends gen_base_run_timeout_mode_a_test;
        a2c_in_order_comparator #(rv_item_t) cmp;

        `uvm_component_utils(gen_base_run_timeout_unpaired_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b     = 1;
            want_ports = "rv (uvm_test_top.env.rv_agent.drv), both lanes waiting for the transfer of ";
            want_cmp   = '{"uvm_test_top.cmp: end of test with 1 DUT items unpaired after 0 pairs"};
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            cmp = a2c_in_order_comparator#(rv_item_t)::type_id::create("cmp", this);
        endfunction

        virtual task run_body();
            rv_item_t it = rv_item_t::type_id::create("it");
            it.data = '{tag: 4'h1, value: 20'h2};
            cmp.write_a2c_dut(it);
            super.run_body();
        endtask
    endclass : gen_base_run_timeout_unpaired_test

    // Mode B: a memory comparator holds a read of X that no access
    // followed, and its end-of-test report names the timeout.
    class gen_base_run_timeout_xread_test extends gen_base_run_timeout_mode_a_test;
        memory_comparator #(lb_mem_addr_t, lb_data_t) mem_cmp;

        `uvm_component_utils(gen_base_run_timeout_xread_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b     = 1;
            want_ports = "rv (uvm_test_top.env.rv_agent.drv), both lanes waiting for the transfer of ";
            want_cmp   = '{"uvm_test_top.mem_cmp: end of test with a read of X or Z that no access followed"};
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            mem_cmp = memory_comparator#(lb_mem_addr_t, lb_data_t)::type_id::create("mem_cmp", this);
        endfunction

        virtual task run_body();
            mem_item_t dut = mem_item_t::type_id::create("dut");
            mem_item_t model = mem_item_t::type_id::create("model");
            dut.addr   = 3;
            dut.data   = 'x;
            model.addr = 3;
            model.data = '0;
            mem_cmp.write_a2c_dut(dut);
            mem_cmp.write_a2c_model(model);
            super.run_body();
        endtask
    endclass : gen_base_run_timeout_xread_test

    // The defaults: the budget is derived, with a2c_run_timeout's floor and
    // factor, which are the 2500000 and 20 the spec measures, and a run of
    // 2000 clocks ends within it and logs its length.
    class gen_base_run_timeout_default_test extends lb_gen_base;
        lb_id_counter infos;

        `uvm_component_utils(gen_base_run_timeout_default_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            quiet_cycles         = 20;
            no_stimulus_expected = 1;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            infos = lb_id_counter::type_id::create("infos");
            infos.id = "A2C_RUN_TIMEOUT";
            uvm_report_cb::add(null, infos);
            super.build_phase(phase);
        endfunction

        virtual task run_body();
            repeat (2000) @(posedge env.clk_vif.clk);
        endtask

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            `uvm_info("LB_STATS", $sformatf("run_timeout_cycles %0d, fixed %0d, floor %0d, factor %0d; %0d A2C_RUN_TIMEOUT infos", run_timeout_cycles,
                                            run_timeout.fixed, run_timeout.floor_cycles, run_timeout.factor, infos.infos), UVM_NONE)
            if (run_timeout_cycles != -1 || run_timeout.fixed) `uvm_error("LB_GEN", "the budget is not derived by default")
            if (run_timeout.floor_cycles != A2C_RUN_TIMEOUT_FLOOR_CYCLES || run_timeout.factor != A2C_RUN_TIMEOUT_FACTOR) begin
                `uvm_error("LB_GEN", $sformatf("the floor and factor are %0d and %0d, expected a2c_run_timeout's %0d and %0d", run_timeout.floor_cycles,
                                               run_timeout.factor, A2C_RUN_TIMEOUT_FLOOR_CYCLES, A2C_RUN_TIMEOUT_FACTOR))
            end
            if (A2C_RUN_TIMEOUT_FLOOR_CYCLES != 2500000 || A2C_RUN_TIMEOUT_FACTOR != 20) begin
                `uvm_error("LB_GEN", $sformatf("the default floor and factor are %0d and %0d, expected the 2500000 and 20 specs/SIMULATOR_INTEGRATION.md measures",
                                               A2C_RUN_TIMEOUT_FLOOR_CYCLES, A2C_RUN_TIMEOUT_FACTOR))
            end
            if (srv.get_id_count("A2C_RUN_TIMEOUT") != 1 || infos.infos != 1) `uvm_error("LB_GEN", "expected one A2C_RUN_TIMEOUT info of the run's length")
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
        endfunction
    endclass : gen_base_run_timeout_default_test
