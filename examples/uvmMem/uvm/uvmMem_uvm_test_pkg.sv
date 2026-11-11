// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=uvmTest --section=header

`ifndef UVMMEM_UVM_TEST_PKG_SV
`define UVMMEM_UVM_TEST_PKG_SV

`ifndef A2C_UVM_PKG
`define A2C_UVM_PKG A2C_UVM_PKG_is_not_defined__define_it_as_the_variant_uvm_package
`endif

package uvmMem_uvm_test_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;
    import rdy_vld_uvm_pkg::*;
    import memory_uvm_pkg::*;
    // Generated Import package statement(s)
    import uvmMem_package::*;
    import `A2C_UVM_PKG::*;

// GENERATED_CODE_END

    `uvm_analysis_imp_decl(_cmd)
    `uvm_analysis_imp_decl(_out)

    // Each command's expected word is the one its rdAddr holds before its
    // own write: the last word an earlier command wrote there, or the
    // memory's fill for a word no command has written. Output words must
    // match in order.
    class uvmMem_scoreboard extends uvm_component;
        uvm_analysis_imp_cmd #(cmd_item_t, uvmMem_scoreboard) cmd_export;
        uvm_analysis_imp_out #(out_item_t, uvmMem_scoreboard) out_export;
        a2c_mem_model #(uvmMemWordSt) mem;
        protected uvmMemWordSt written[bit [63:0]];
        protected uvmMemWordSt expected[$];
        int unsigned checked;
        int unsigned errors;

        `uvm_component_utils(uvmMem_scoreboard)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            cmd_export = new("cmd_export", this);
            out_export = new("out_export", this);
        endfunction

        function void write_cmd(cmd_item_t it);
            uvmMemWordSt w;
            if (written.exists(64'(it.data.rdAddr))) begin
                expected.push_back(written[64'(it.data.rdAddr)]);
            end else begin
                expected.push_back(mem.read(64'(it.data.rdAddr)));
            end
            w.word = it.data.data;
            written[64'(it.data.wrAddr)] = w;
        endfunction

        function void write_out(out_item_t it);
            uvmMemWordSt exp;
            if (expected.size() == 0) begin
                `uvm_error("UVM_MEM_SB", $sformatf("word 'h%0h arrived on out with no command outstanding", it.data.word))
                errors++;
                return;
            end
            exp = expected.pop_front();
            if (it.data !== exp) begin
                `uvm_error("UVM_MEM_SB", $sformatf("word %0d on out is 'h%0h, expected 'h%0h", checked, it.data.word, exp.word))
                errors++;
            end
            checked++;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (expected.size() != 0) begin
                `uvm_error("UVM_MEM_SB", $sformatf("%0d commands sent no word on out", expected.size()))
            end
            `uvm_info("UVM_MEM_SB", $sformatf("%0d words checked", checked), UVM_LOW)
        endfunction
    endclass : uvmMem_scoreboard

    // n commands. Each reads, with equal odds, the address it writes, the
    // address the command before it wrote, or any address, so reads through
    // rd follow writes through wr from the command before and from a few
    // commands earlier.
    class uvmMem_copy_seq extends uvm_sequence #(cmd_item_t);
        int unsigned n = 32;
        // Each command is preceded by 0 to max_gap idle clocks.
        int unsigned max_gap = 0;

        `uvm_object_utils(uvmMem_copy_seq)

        function new(string name = "uvmMem_copy_seq");
            super.new(name);
        endfunction

        virtual task body();
            cmd_item_t  it;
            uvmMemAddrT last = '0;
            for (int unsigned i = 0; i < n; i++) begin
                it = cmd_item_t::type_id::create("it");
                start_item(it);
                it.data.wrAddr = uvmMemAddrT'($urandom());
                it.data.data   = uvmMemDataT'($urandom());
                case ($urandom_range(2, 0))
                    0: it.data.rdAddr = it.data.wrAddr;
                    1: it.data.rdAddr = last;
                    default: it.data.rdAddr = uvmMemAddrT'($urandom());
                endcase
                it.gap = (max_gap == 0) ? 0 : $urandom_range(max_gap, 0);
                last = it.data.wrAddr;
                finish_item(it);
            end
        endtask
    endclass : uvmMem_copy_seq

    // wr and rd share one memory with a random fill, as the two ports of one
    // RAM outside the DUT.
    class uvmMem_tb_env extends uvmMem_env;
        a2c_mem_model #(uvmMemWordSt) mem;
        uvmMem_scoreboard sb;

        `uvm_component_utils(uvmMem_tb_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            wr_config_t wr_cfg;
            rd_config_t rd_cfg;
            super.build_phase(phase);
            mem = a2c_mem_model#(uvmMemWordSt)::type_id::create("mem");
            mem.fill = A2C_MEM_FILL_RANDOM;
            if (!uvm_config_db#(wr_config_t)::get(this, "wr_agent", "cfg", wr_cfg)
                || !uvm_config_db#(rd_config_t)::get(this, "rd_agent", "cfg", rd_cfg)) begin
                `uvm_fatal("A2C_CFG", "no config for wr_agent or rd_agent")
            end
            wr_cfg.mem = mem;
            rd_cfg.mem = mem;
            sb = uvmMem_scoreboard::type_id::create("sb", this);
            sb.mem = mem;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            cmd_agent.mon.ap.connect(sb.cmd_export);
            out_agent.mon.ap.connect(sb.out_export);
        endfunction

        // In Mode B every model lane access of wr and rd must come with
        // credit, and each BFM must have held some, or the run did not
        // exercise the credit rendezvous.
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (!dual_dut) return;
            check_credit("wr", wr_agent.drv);
            check_credit("rd", rd_agent.drv);
        endfunction

        protected function void check_credit(string port, memory_driver#(uvmMemAddrSt, uvmMemWordSt) drv);
            string counts = $sformatf("%s: the model's BFM held %0d accesses for credit, with held high at %0d sample edges, and the model lane made %0d accesses without credit",
                                      port, drv.held_access_count(), drv.held_clock_count(), drv.uncredited_count());
            if (drv.held_access_count() == 0 || drv.uncredited_count() != 0) begin
                `uvm_error("UVM_MEM_CREDIT", {counts, "; expected some held and none without credit"})
            end else begin
                `uvm_info("UVM_MEM_CREDIT", counts, UVM_LOW)
            end
        endfunction

        // Sends n commands and declares their words to the out counter.
        task send(int unsigned n, int unsigned max_gap = 0);
            uvmMem_copy_seq seq = uvmMem_copy_seq::type_id::create("copy_seq");
            seq.n       = n;
            seq.max_gap = max_gap;
            out_counter.expect_count(n);
            `uvm_info("A2C_TEST", $sformatf("%0d commands, max_gap %0d", n, max_gap), UVM_LOW)
            seq.start(cmd_agent.sqr);
        endtask
    endclass : uvmMem_tb_env

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
    class uvmMem_base_test extends uvm_test implements a2c_run_work;
        uvmMem_tb_env env;
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

        `uvm_component_utils(uvmMem_base_test)

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
            env = uvmMem_tb_env::type_id::create("env", this);
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
            n += a2c_items_sent#(cmd_item_t)::of(env.cmd_agent);
            return n;
        endfunction

        // The transactions the output counters expect.
        virtual function int unsigned outputs_declared();
            int unsigned n = 0;
            n += env.out_counter.declared();
            return n;
        endfunction
    endclass : uvmMem_base_test

// GENERATED_CODE_END

    // 32 commands back to back.
    class uvmMem_smoke_test extends uvmMem_base_test;
        `uvm_component_utils(uvmMem_smoke_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_body();
            env.send(32);
        endtask
    endclass : uvmMem_smoke_test

    // 256 commands with up to 3 idle clocks before each.
    class uvmMem_random_test extends uvmMem_base_test;
        `uvm_component_utils(uvmMem_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_body();
            env.send(256, 3);
        endtask
    endclass : uvmMem_random_test

// GENERATED_CODE_BEGIN --template=uvmTest --section=footer

    // The smoke test with more transactions expected on the first output than
    // the DUT delivers (+a2c_fail_missing_count, default 1). It passes only if
    // the counter reported exactly one A2C_TXN_COUNT, one per lane in Mode B,
    // each lane ends missing exactly missing_count transactions, and nothing
    // else raised a UVM_ERROR or UVM_FATAL, so a counter that stops reporting
    // or reports the wrong shortfall fails it. The missing transaction never
    // closes its unit, so the real-time rules are off.
    class uvmMem_fail_test extends uvmMem_smoke_test;
        a2c_error_demoter demoter;
        int unsigned missing_count = 1;

        `uvm_component_utils(uvmMem_fail_test)

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
            if (demoter.demoted != want || others != 0 || shortfall != "") begin
                `uvm_error("A2C_FAIL_TEST", $sformatf("expected exactly %s and no other error; caught %0d A2C_TXN_COUNT, %0d other UVM_ERROR/UVM_FATAL%s",
                                                      expected, demoter.demoted, others, shortfall))
            end else begin
                `uvm_info("A2C_FAIL_TEST", "the transaction counter reported the missing transactions as intended", UVM_LOW)
            end
        endfunction
    endclass : uvmMem_fail_test

    // The smoke test with a mismatch injected at pair +a2c_model_mismatch_at
    // (default 1) of the first counted output's model comparator. It runs
    // only in Mode B. Only the injected A2C_MODEL_CMP is demoted, so any
    // other mismatch stays an error. It passes only if that one report
    // arrived, the comparator compared at least mismatch_at pairs, and
    // nothing else raised a UVM_ERROR or UVM_FATAL.
    class uvmMem_model_mismatch_test extends uvmMem_smoke_test;
        a2c_error_demoter demoter;
        int unsigned mismatch_at = 1;

        `uvm_component_utils(uvmMem_model_mismatch_test)

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
                `uvm_fatal("A2C_CFG", "uvmMem_model_mismatch_test compares the model DUT against the RTL and runs only on the both DUT")
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
    endclass : uvmMem_model_mismatch_test

endpackage : uvmMem_uvm_test_pkg

`endif // UVMMEM_UVM_TEST_PKG_SV

// GENERATED_CODE_END
