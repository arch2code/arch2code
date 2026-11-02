// A loopback run of the base test that templates/systemVerilog/uvmTest.py
// generates, so its handling of the drain knobs is simulated, not only
// read. The span between the RENDERED markers is render_tests() of that
// template for lb_gen_env, a stand-in for the generated env with one clock,
// an input port, lb_in, a status input, lb_st, and one counted output,
// lb_out;
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
    // (+a2c_no_stimulus_expected=1) is set.
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
        int          joint_stall_cycles = -1;
        bit          no_stimulus_expected;

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
        function int unsigned stimulus_sent();
            int unsigned n = 0;
            n += a2c_items_sent#(lb_in_item_t)::of(env.lb_in_agent);
            n += a2c_items_sent#(lb_st_item_t)::of(env.lb_st_agent);
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
