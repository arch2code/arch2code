// A loopback run of the base test that templates/systemVerilog/uvmTest.py
// generates, so its handling of the drain knobs is simulated, not only
// read. The span between the RENDERED markers is render_tests() of that
// template for lb_gen_env, a stand-in for the generated env with no ports
// and one clock; unittest/test_uvm_test_pkg.py fails when the span and the
// template differ. Included in a2c_uvm_loopback_pkg after
// a2c_replay_drain_lb_tests.svh, whose fake lanes the env's replay log
// uses.

    // What the base test reads of a generated env, and one replay log.
    class lb_gen_env extends uvm_env;
        virtual a2c_clk_if clk_vif;
        bit                dual_dut = 1;
        lb_bit_log_t       replay;

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
    // UVM_INFO.
    class lb_gen_base extends uvm_test;
        lb_gen_env env;
        int unsigned output_deadline_cycles = 200000;
        int unsigned quiet_cycles = 1000;
        int unsigned clock_stop_cycles = 1000;
        int          drain_quiet_cycles = -1;
        int          drain_deadline_cycles = -1;
        int          drain_catchup_cycles = -1;
        bit          drain_cut_expected;

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
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_clock_stop_cycles", clock_stop_cycles);
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_quiet_cycles", drain_quiet_cycles);
            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_deadline_cycles", drain_deadline_cycles);
            if (drain_catchup_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_catchup_cycles", drain_catchup_cycles);
            end
            uvm_config_db#(bit)::set(this, "env*", "a2c_drain_cut_expected", drain_cut_expected);
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

    // A test that sets the drain's window, deadline and catch-up in its
    // constructor: the replay log must get those, not the values the base
    // test derives.
    class gen_base_drain_ctor_test extends lb_gen_base;
        int unsigned want[3] = '{37, 4100, 99};

        `uvm_component_utils(gen_base_drain_ctor_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            drain_quiet_cycles    = 37;
            drain_deadline_cycles = 4100;
            drain_catchup_cycles  = 99;
        endfunction

        virtual function void end_of_elaboration_phase(uvm_phase phase);
            int unsigned got[3] = '{env.replay.drain_quiet_cycles, env.replay.drain_deadline_cycles, env.replay.catchup_cycles()};
            super.end_of_elaboration_phase(phase);
            `uvm_info("LB_STATS", $sformatf("the replay log's window, deadline and catch-up: %p", got), UVM_NONE)
            if (got != want) `uvm_error("LB_GEN", $sformatf("the replay log got %p, expected %p", got, want))
        endfunction

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
        endfunction
    endclass : gen_base_drain_ctor_test

    // A test that sets only the quiet window and the output deadline in its
    // constructor: the drain's window and deadline must follow them, and
    // the catch-up the log's deadline.
    class gen_base_drain_default_test extends gen_base_drain_ctor_test;
        `uvm_component_utils(gen_base_drain_default_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            drain_quiet_cycles     = -1;
            drain_deadline_cycles  = -1;
            drain_catchup_cycles   = -1;
            quiet_cycles           = 45;
            output_deadline_cycles = 5000;
            want                   = '{45, 5000, 5000};
        endfunction
    endclass : gen_base_drain_default_test

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
