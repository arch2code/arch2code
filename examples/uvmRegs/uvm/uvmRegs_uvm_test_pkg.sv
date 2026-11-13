// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegs
// GENERATED_CODE_BEGIN --template=uvmTest --section=header

`ifndef UVMREGS_UVM_TEST_PKG_SV
`define UVMREGS_UVM_TEST_PKG_SV

`ifndef A2C_UVM_PKG
`define A2C_UVM_PKG A2C_UVM_PKG_is_not_defined__define_it_as_the_variant_uvm_package
`endif

package uvmRegs_uvm_test_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;
    import rdy_vld_uvm_pkg::*;
    import apb_uvm_pkg::*;
    // Generated Import package statement(s)
    import uvmRegs_package::*;
    import `A2C_UVM_PKG::*;

// GENERATED_CODE_END

    `uvm_analysis_imp_decl(_in)
    `uvm_analysis_imp_decl(_out)

    // Each input word's expected output, from the register model's mirror
    // when the word enters: add both scale offsets, XOR the tab row its low
    // bits select, and invert under uStat.mode. The tab rows are the ones
    // the env last wrote, since a uvm_mem keeps no mirror. Output words must
    // match in order. The RTL passes a word through in the clock it enters,
    // so its output can reach the scoreboard before its input does.
    class uvmRegs_scoreboard extends uvm_component;
        uvm_analysis_imp_in #(in_item_t, uvmRegs_scoreboard) in_export;
        uvm_analysis_imp_out #(out_item_t, uvmRegs_scoreboard) out_export;
        uvmRegs_reg_block regmodel;
        uvm_reg_data_t tab[UVM_REGS_TAB_ROWS];
        protected uvmRegsWordT expected[$];
        protected uvmRegsWordT actual[$];
        int unsigned checked;

        `uvm_component_utils(uvmRegs_scoreboard)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            in_export = new("in_export", this);
            out_export = new("out_export", this);
        endfunction

        function uvmRegsWordT predict(uvmRegsWordT w);
            uvmRegsWordT s = w + uvmRegsWordT'(regmodel.uScale0.offset.offset.get_mirrored_value())
                               + uvmRegsWordT'(regmodel.uScale1.offset.offset.get_mirrored_value());
            uvmRegsWordT e = s ^ uvmRegsWordT'(tab[s % UVM_REGS_TAB_ROWS]);
            return regmodel.uStat.mode.invert.get_mirrored_value() ? ~e : e;
        endfunction

        function void write_in(in_item_t it);
            expected.push_back(predict(it.data.word));
            compare();
        endfunction

        function void write_out(out_item_t it);
            actual.push_back(it.data.word);
            compare();
        endfunction

        protected function void compare();
            while (expected.size() != 0 && actual.size() != 0) begin
                uvmRegsWordT exp = expected.pop_front();
                uvmRegsWordT got = actual.pop_front();
                if (got !== exp) begin
                    `uvm_error("UVM_REGS_SB", $sformatf("word %0d on out is 'h%0h, expected 'h%0h", checked, got, exp))
                end
                checked++;
            end
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (expected.size() != 0) begin
                `uvm_error("UVM_REGS_SB", $sformatf("%0d words sent no word on out", expected.size()))
            end
            if (actual.size() != 0) begin
                `uvm_error("UVM_REGS_SB", $sformatf("%0d words arrived on out with no word sent", actual.size()))
            end
            `uvm_info("UVM_REGS_SB", $sformatf("%0d words checked", checked), UVM_LOW)
        endfunction
    endclass : uvmRegs_scoreboard

    // n words, word i being first + i * 7.
    class uvmRegs_word_seq extends uvm_sequence #(in_item_t);
        int unsigned n = UVM_REGS_WORDS;
        uvmRegsWordT first;

        `uvm_object_utils(uvmRegs_word_seq)

        function new(string name = "uvmRegs_word_seq");
            super.new(name);
        endfunction

        virtual task body();
            in_item_t it;
            for (int unsigned i = 0; i < n; i++) begin
                it = in_item_t::type_id::create("it");
                start_item(it);
                it.data.word = first + uvmRegsWordT'(i * 7);
                finish_item(it);
            end
        endtask
    endclass : uvmRegs_word_seq

    class uvmRegs_tb_env extends uvmRegs_env;
        uvmRegs_scoreboard sb;

        `uvm_component_utils(uvmRegs_tb_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            sb = uvmRegs_scoreboard::type_id::create("sb", this);
            sb.regmodel = regmodel;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            in_agent.mon.ap.connect(sb.in_export);
            out_agent.mon.ap.connect(sb.out_export);
        endfunction

        task write_reg(uvm_reg rg, uvm_reg_data_t value);
            uvm_status_e   status;
            uvm_reg_data_t readback;
            rg.write(status, value);
            if (status != UVM_IS_OK) begin
                `uvm_error("A2C_REG", $sformatf("%s write of 'h%0h returned %s", rg.get_full_name(), value, status.name()))
            end
            rg.read(status, readback);
            if (status != UVM_IS_OK || readback != value) begin
                `uvm_error("A2C_REG", $sformatf("%s read back 'h%0h (%s), wrote 'h%0h", rg.get_full_name(), readback, status.name(), value))
            end
        endtask

        task expect_reg(uvm_reg rg, uvm_reg_data_t value);
            uvm_status_e   status;
            uvm_reg_data_t got;
            rg.read(status, got);
            if (status != UVM_IS_OK || got != value) begin
                `uvm_error("A2C_REG", $sformatf("%s reads 'h%0h (%s), expected 'h%0h", rg.get_full_name(), got, status.name(), value))
            end
        endtask

        task expect_mem(uvm_mem mem, uvm_reg_addr_t row, uvm_reg_data_t value);
            uvm_status_e   status;
            uvm_reg_data_t got;
            mem.read(status, row, got);
            if (status != UVM_IS_OK || got != value) begin
                `uvm_error("A2C_REG", $sformatf("%s row %0d reads 'h%0h (%s), expected 'h%0h", mem.get_full_name(), row, got,
                                                status.name(), value))
            end
        endtask

        // Programs every leaf by name, each tab row with its index times
        // tab_step, and checks the registers no write touches.
        task program_regs(uvm_reg_data_t offset0, uvm_reg_data_t offset1, bit invert, uvm_reg_data_t tab_step);
            uvm_status_e status;
            `uvm_info("A2C_TEST", $sformatf("offsets 'h%0h 'h%0h, invert %0b, tab step 'h%0h", offset0, offset1, invert, tab_step), UVM_LOW)
            expect_reg(regmodel.uBridge.uDeep.ident, UVM_REGS_IDENT);
            write_reg(regmodel.uScale0.offset, offset0);
            write_reg(regmodel.uScale1.offset, offset1);
            write_reg(regmodel.uStat.mode, invert);
            write_reg(regmodel.uStat.scratch, 'hbeef);
            write_reg(regmodel.uBridge.uDeep.cfg, 'ha5);
            write_reg(regmodel.uWrap.uInner.tag, 'h3c);
            for (int unsigned r = 0; r < UVM_REGS_TAB_ROWS; r++) begin
                sb.tab[r] = (r * tab_step) & ((uvm_reg_data_t'(1) << regmodel.uStat.tab.get_n_bits()) - 1);
                regmodel.uStat.tab.write(status, r, sb.tab[r]);
                if (status != UVM_IS_OK) begin
                    `uvm_error("A2C_REG", $sformatf("tab row %0d write returned %s", r, status.name()))
                end
            end
            for (int unsigned r = 0; r < UVM_REGS_TAB_ROWS; r++) begin
                expect_mem(regmodel.uStat.tab, r, sb.tab[r]);
            end
        endtask

        // Sends n words from first and declares their outputs to the out
        // counter.
        task send(int unsigned n, uvmRegsWordT first = 0);
            uvmRegs_word_seq seq = uvmRegs_word_seq::type_id::create("word_seq");
            seq.n     = n;
            seq.first = first;
            out_counter.expect_count(n);
            seq.start(in_agent.sqr);
        endtask
    endclass : uvmRegs_tb_env

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
    class uvmRegs_base_test extends uvm_test implements a2c_run_work;
        uvmRegs_tb_env env;
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

        `uvm_component_utils(uvmRegs_base_test)

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
            env = uvmRegs_tb_env::type_id::create("env", this);
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
    endclass : uvmRegs_base_test

// GENERATED_CODE_END

    // Programs every leaf through its instance path, streams
    // UVM_REGS_WORDS words, and reads back the count and the hist row of
    // each of the last words once the outputs are in.
    class uvmRegs_smoke_test extends uvmRegs_base_test;
        `uvm_component_utils(uvmRegs_smoke_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_body();
            uvmRegsWordT first = UVM_REGS_WORDS;
            env.program_regs(UVM_REGS_TB_OFFSET0, UVM_REGS_TB_OFFSET1, 1, UVM_REGS_TB_TAB_STEP);
            env.send(UVM_REGS_WORDS, first);
            wait_for_outputs();
            env.expect_reg(env.regmodel.uStat.count, UVM_REGS_WORDS);
            for (int unsigned i = UVM_REGS_WORDS - UVM_REGS_TAB_ROWS; i < UVM_REGS_WORDS; i++) begin
                uvmRegsWordT s = first + uvmRegsWordT'(i * 7) + UVM_REGS_TB_OFFSET0 + UVM_REGS_TB_OFFSET1;
                env.expect_mem(env.regmodel.uStat.hist, s % UVM_REGS_TAB_ROWS, s);
            end
        endtask
    endclass : uvmRegs_smoke_test

    // Front-door checks, no words. uvm_reg_hw_reset_seq reads the reset
    // value of every register of the root block, then of uBridge.uDeep alone
    // through its own map, which is a submap of the root's.
    class uvmRegs_reg_test extends uvmRegs_base_test;
        `uvm_component_utils(uvmRegs_reg_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            no_stimulus_expected = 1;
        endfunction

        virtual task run_body();
            uvm_reg_hw_reset_seq root_seq  = uvm_reg_hw_reset_seq::type_id::create("root_reset_seq");
            uvm_reg_hw_reset_seq child_seq = uvm_reg_hw_reset_seq::type_id::create("child_reset_seq");
            root_seq.model = env.regmodel;
            root_seq.start(null);
            child_seq.model = env.regmodel.uBridge.uDeep;
            child_seq.start(null);
        endtask
    endclass : uvmRegs_reg_test

    // uvm_mem_walk_seq on uStat walks tab, the block's only RW memory, at
    // the decoder's row stride, which is wider than its rows.
    class uvmRegs_mem_walk_test extends uvmRegs_base_test;
        `uvm_component_utils(uvmRegs_mem_walk_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            no_stimulus_expected = 1;
        endfunction

        virtual task run_body();
            uvm_mem_walk_seq walk_seq = uvm_mem_walk_seq::type_id::create("walk_seq");
            walk_seq.model = env.regmodel.uStat;
            walk_seq.start(null);
        endtask
    endclass : uvmRegs_mem_walk_test

    // Mode B only. Writes uWrap.uInner.tag while the words are still due on
    // out. It passes only if the guard raised exactly one A2C_MIDSTREAM,
    // naming tag by its path through the model, and nothing else raised a
    // UVM_ERROR or UVM_FATAL.
    class uvmRegs_midstream_test extends uvmRegs_base_test;
        a2c_error_demoter demoter;

        `uvm_component_utils(uvmRegs_midstream_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            demoter = a2c_error_demoter::type_id::create("demoter");
            demoter.demote_id = "A2C_MIDSTREAM";
            demoter.demote_text = "uWrap.uInner.tag";
            uvm_report_cb::add(null, demoter);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (!env.dual_dut) begin
                `uvm_fatal("A2C_CFG", "uvmRegs_midstream_test needs the model DUT's guard and runs only on the both DUT")
            end
        endfunction

        virtual task run_body();
            uvm_status_e status;
            env.program_regs(UVM_REGS_TB_OFFSET0, UVM_REGS_TB_OFFSET1, 0, UVM_REGS_TB_TAB_STEP);
            fork
                env.send(UVM_REGS_WORDS);
            join_none
            env.regmodel.uWrap.uInner.tag.write(status, 'h77);
            wait fork;
        endtask

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned others = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);
            super.report_phase(phase);
            if (demoter.demoted != 1 || others != 0) begin
                `uvm_error("A2C_MIDSTREAM_TEST", $sformatf("expected exactly one A2C_MIDSTREAM naming uWrap.uInner.tag and no other error; caught %0d, %0d other UVM_ERROR/UVM_FATAL",
                                                           demoter.demoted, others))
            end else begin
                `uvm_info("A2C_MIDSTREAM_TEST", "the guard reported the write to uWrap.uInner.tag as intended", UVM_LOW)
            end
        endfunction
    endclass : uvmRegs_midstream_test

// GENERATED_CODE_BEGIN --template=uvmTest --section=footer

    // The smoke test with more transactions expected on the first output than
    // the DUT delivers (+a2c_fail_missing_count, default 1). It passes only if
    // the counter reported exactly one A2C_TXN_COUNT, one per lane in Mode B,
    // each lane ends missing exactly missing_count transactions, and nothing
    // else raised a UVM_ERROR or UVM_FATAL, so a counter that stops reporting
    // or reports the wrong shortfall fails it. The missing transaction never
    // closes its unit, so the real-time rules are off.
    class uvmRegs_fail_test extends uvmRegs_smoke_test;
        a2c_error_demoter demoter;
        int unsigned missing_count = 1;

        `uvm_component_utils(uvmRegs_fail_test)

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
    endclass : uvmRegs_fail_test

    // The smoke test with a mismatch injected at pair +a2c_model_mismatch_at
    // (default 1) of the first counted output's model comparator. It runs
    // only in Mode B. Only the injected A2C_MODEL_CMP is demoted, so any
    // other mismatch stays an error. It passes only if that one report
    // arrived, the comparator compared at least mismatch_at pairs, and
    // nothing else raised a UVM_ERROR or UVM_FATAL.
    class uvmRegs_model_mismatch_test extends uvmRegs_smoke_test;
        a2c_error_demoter demoter;
        int unsigned mismatch_at = 1;

        `uvm_component_utils(uvmRegs_model_mismatch_test)

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
                `uvm_fatal("A2C_CFG", "uvmRegs_model_mismatch_test compares the model DUT against the RTL and runs only on the both DUT")
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
    endclass : uvmRegs_model_mismatch_test

endpackage : uvmRegs_uvm_test_pkg

`endif // UVMREGS_UVM_TEST_PKG_SV

// GENERATED_CODE_END
