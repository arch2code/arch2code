# The test package of a hasUvm block, one for all its variants. The variant
# package it imports is named by the A2C_UVM_PKG define, so one file compiles
# against whichever variant the build selects. The user spans between the
# sections hold the block's <block>_tb_env, which the base test creates, and
# the tests that extend the base test.
import textwrap

from pysrc.systemVerilogGeneratorHelper import importPackages


def render(args, prj, data):
    uvm = data['uvm']
    match args.section:
        case 'header':
            out = render_header(args, prj, data, uvm)
        case 'tests':
            out = render_tests(uvm)
        case 'footer':
            out = render_footer(uvm)
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are header, tests or footer")
    return textwrap.indent(out, ' '*args.sectionindent)


def render_header(args, prj, data, uvm):
    guard = uvm['testPkgGuard']
    out = [f"`ifndef {guard}", f"`define {guard}", '',
           # An undefined macro would stop the compile at the import with no
           # hint of what to define, so the package name says it instead.
           '`ifndef A2C_UVM_PKG',
           '`define A2C_UVM_PKG A2C_UVM_PKG_is_not_defined__define_it_as_the_variant_uvm_package',
           '`endif', '',
           f"package {uvm['testPkgName']};"]
    lines = ['import uvm_pkg::*;', '`include "uvm_macros.svh"', 'import a2c_uvm_pkg::*;']
    lines += [f'import {pkg}::*;' for pkg in uvm['agentPackages']]
    lines.append(importPackages(args, prj, data['blockInfo']['_context'], data))
    lines.append('import `A2C_UVM_PKG::*;')
    return '\n' + '\n'.join(out) + '\n' + textwrap.indent('\n'.join(lines), ' '*4) + '\n'


def data_inputs(uvm):
    # Register writes alone leave the data path idle, so the register bus
    # counts as stimulus only on a block it is the only input of.
    inputs = [port for port in uvm['ports'] if port['role'] == 'dst']
    bus = uvm['registerBus']['port'] if uvm['registerBus'] else None
    return [port for port in inputs if port['name'] != bus] or inputs


def render_tests(uvm):
    cls = uvm['baseTestClass']
    counters = [port for port in uvm['ports'] if port['counter']]
    inputs = [port for port in uvm['ports'] if port['role'] == 'dst']
    dataInputs = data_inputs(uvm)
    lines = ["// Waits for reset, runs run_body(), then waits for every output's",
             "// expected transactions. A test sets its own default deadline, quiet",
             "// window and clock stop in its constructor; +a2c_output_deadline_cycles,",
             "// +a2c_quiet_cycles and +a2c_clock_stop_cycles override them. A clock",
             "// with no edge for clock_stop_cycles of its periods has stopped. In",
             "// paired mode the drain at the end of the run phase has its own window,",
             "// deadline and catch-up after a cut, which a test may set in its",
             "// constructor too, and +a2c_drain_quiet_cycles,",
             "// +a2c_drain_deadline_cycles and +a2c_drain_catchup_cycles override.",
             "// Left at -1, the window and deadline take quiet_cycles and",
             "// output_deadline_cycles, and the catch-up takes each replay log's",
             "// deadline. +a2c_drain_cut_expected=1 reports the drain's cuts as",
             "// UVM_INFO. A master in paired mode declares a lane dead when it trails",
             "// the other by lane_skew_cycles clocks, and the other lane dead too",
             "// when, left alone, it makes no progress for lone_lane_cycles",
             "// clocks. In either mode a master that holds an item while no port",
             "// makes a handshake for joint_stall_cycles clocks raises one",
             "// A2C_JOINT_STALL. In paired mode the masters then declare every live",
             "// lane dead, and in single mode the run ends there, as at the run",
             "// timeout. Left at -1 each keeps the master's own",
             "// 200000, +a2c_lane_skew_cycles, +a2c_lone_lane_cycles and",
             "// +a2c_joint_stall_cycles override them, and 0 turns a rule off. A",
             "// paired-mode master that holds its next item back for the model lane,",
             "// with the DUT lane ready for it, for model_throttle_cycles clocks in a",
             "// row raises A2C_MODEL_THROTTLE; left at -1 it keeps the master's",
             "// own bound, +a2c_model_throttle_cycles overrides it, and 0 turns the",
             "// rule off. A run that sends nothing on an input, the register bus",
             "// aside on a block with another input, and expects no output",
             "// transaction warns at check_phase, unless no_stimulus_expected",
             "// (+a2c_no_stimulus_expected=1) is set, which also lets every",
             "// comparator compare no pair. A run phase still running at",
             f"// its run timeout, counted in clocks of {uvm['clocks'][0]['clock']}, ends with one",
             "// A2C_RUN_TIMEOUT error naming the ports that wait and the objections",
             "// raised, and check_phase still runs. Left at -1, the timeout is",
             "// run_timeout_floor_cycles plus run_timeout_factor times the work the",
             "// test has declared, each knob left at -1 taking a2c_run_timeout's",
             "// default, and a progress rule counting at that point may report",
             "// first; run_timeout_cycles above 0 fixes it and 0 turns it off, as",
             "// does run_timeout.fix(), from any phase.",
             "// +a2c_run_timeout_cycles, +a2c_run_timeout_floor_cycles and",
             "// +a2c_run_timeout_factor override them. rt_gap_cycles,",
             "// rt_latency_cycles, rt_lag_cycles, rt_refusal_cycles and",
             "// rt_on_model set the real-time rules of every a2c_rt_checker the",
             "// env holds; left at -1 each keeps the checker's own, and",
             "// +a2c_rt_gap_cycles, +a2c_rt_latency_cycles, +a2c_rt_lag_cycles,",
             "// +a2c_rt_refusal_cycles and +a2c_rt_on_model override them. With",
             "// expect_from_model (+a2c_expect_from_model=1) set, an output needs no",
             "// expect_count() in paired mode: the model lane's count is the DUT lane's",
             "// expectation, and wait_for_outputs() returns once the outputs have",
             "// been quiet for quiet_cycles. A run with one DUT has no model lane,",
             "// so build_phase clears expect_from_model there and the test declares",
             "// its counts. reset_dut() pulses the resets mid-run.",
             f"class {cls} extends uvm_test implements a2c_run_work;",
             f"    {uvm['tbEnvClass']} env;",
             '    int unsigned output_deadline_cycles = 200000;',
             '    int unsigned quiet_cycles = 1000;',
             '    int unsigned clock_stop_cycles = 1000;',
             '    int          drain_quiet_cycles = -1;',
             '    int          drain_deadline_cycles = -1;',
             '    int          drain_catchup_cycles = -1;',
             '    bit          drain_cut_expected;',
             '    int          lane_skew_cycles = -1;',
             '    int          lone_lane_cycles = -1;',
             '    int          joint_stall_cycles = -1;',
             '    int          model_throttle_cycles = -1;',
             '    bit          no_stimulus_expected;',
             '    bit          expect_from_model;',
             '    int          run_timeout_cycles = -1;',
             '    int          run_timeout_floor_cycles = -1;',
             '    int          run_timeout_factor = -1;',
             '    int          rt_gap_cycles = -1;',
             '    int          rt_latency_cycles = -1;',
             '    int          rt_lag_cycles = -1;',
             '    int          rt_refusal_cycles = -1;',
             '    int          rt_on_model = -1;',
             '    a2c_run_timeout run_timeout;',
             '',
             f"    `uvm_component_utils({cls})",
             '',
             '    function new(string name, uvm_component parent);',
             '        super.new(name, parent);',
             '    endfunction',
             '',
             '    virtual function void build_phase(uvm_phase phase);',
             '        bit dual;',
             '        super.build_phase(phase);',
             '        void\'($value$plusargs("a2c_output_deadline_cycles=%d", output_deadline_cycles));',
             '        void\'($value$plusargs("a2c_quiet_cycles=%d", quiet_cycles));',
             '        void\'($value$plusargs("a2c_clock_stop_cycles=%d", clock_stop_cycles));',
             '        if (drain_quiet_cycles < 0) drain_quiet_cycles = quiet_cycles;',
             '        if (drain_deadline_cycles < 0) drain_deadline_cycles = output_deadline_cycles;',
             '        void\'($value$plusargs("a2c_drain_quiet_cycles=%d", drain_quiet_cycles));',
             '        void\'($value$plusargs("a2c_drain_deadline_cycles=%d", drain_deadline_cycles));',
             '        void\'($value$plusargs("a2c_drain_catchup_cycles=%d", drain_catchup_cycles));',
             '        void\'($value$plusargs("a2c_drain_cut_expected=%d", drain_cut_expected));',
             '        void\'($value$plusargs("a2c_lane_skew_cycles=%d", lane_skew_cycles));',
             '        void\'($value$plusargs("a2c_lone_lane_cycles=%d", lone_lane_cycles));',
             '        void\'($value$plusargs("a2c_joint_stall_cycles=%d", joint_stall_cycles));',
             '        void\'($value$plusargs("a2c_model_throttle_cycles=%d", model_throttle_cycles));',
             '        void\'($value$plusargs("a2c_no_stimulus_expected=%d", no_stimulus_expected));',
             '        void\'($value$plusargs("a2c_expect_from_model=%d", expect_from_model));',
             '        void\'($value$plusargs("a2c_run_timeout_cycles=%d", run_timeout_cycles));',
             '        void\'($value$plusargs("a2c_run_timeout_floor_cycles=%d", run_timeout_floor_cycles));',
             '        void\'($value$plusargs("a2c_run_timeout_factor=%d", run_timeout_factor));',
             '        void\'($value$plusargs("a2c_rt_gap_cycles=%d", rt_gap_cycles));',
             '        void\'($value$plusargs("a2c_rt_latency_cycles=%d", rt_latency_cycles));',
             '        void\'($value$plusargs("a2c_rt_lag_cycles=%d", rt_lag_cycles));',
             '        void\'($value$plusargs("a2c_rt_refusal_cycles=%d", rt_refusal_cycles));',
             '        void\'($value$plusargs("a2c_rt_on_model=%d", rt_on_model));',
             '        uvm_config_db#(int unsigned)::set(this, "env*", "a2c_clock_stop_cycles", clock_stop_cycles);',
             '        uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_quiet_cycles", drain_quiet_cycles);',
             '        uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_deadline_cycles", drain_deadline_cycles);',
             '        if (drain_catchup_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_catchup_cycles", drain_catchup_cycles);',
             '        end',
             '        uvm_config_db#(bit)::set(this, "env*", "a2c_drain_cut_expected", drain_cut_expected);',
             '        if (!uvm_config_db#(bit)::get(this, "env", "a2c_dual_dut", dual)) dual = 0;',
             '        expect_from_model &= dual;',
             '        uvm_config_db#(bit)::set(this, "env*", "a2c_expect_from_model", expect_from_model);',
             '        if (no_stimulus_expected) uvm_config_db#(bit)::set(this, "env*", "a2c_allow_no_pairs", 1\'b1);',
             '        if (lane_skew_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_lane_skew_cycles", lane_skew_cycles);',
             '        end',
             '        if (lone_lane_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_lone_lane_cycles", lone_lane_cycles);',
             '        end',
             '        if (joint_stall_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_joint_stall_cycles", joint_stall_cycles);',
             '        end',
             '        if (model_throttle_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_model_throttle_cycles", model_throttle_cycles);',
             '        end',
             '        if (run_timeout_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_cycles", run_timeout_cycles);',
             '        end',
             '        if (run_timeout_floor_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_floor_cycles", run_timeout_floor_cycles);',
             '        end',
             '        if (run_timeout_factor >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_factor", run_timeout_factor);',
             '        end',
             '        if (rt_gap_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_rt_gap_cycles", rt_gap_cycles);',
             '        end',
             '        if (rt_latency_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_rt_latency_cycles", rt_latency_cycles);',
             '        end',
             '        if (rt_lag_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_rt_lag_cycles", rt_lag_cycles);',
             '        end',
             '        if (rt_refusal_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_rt_refusal_cycles", rt_refusal_cycles);',
             '        end',
             '        if (rt_on_model >= 0) begin',
             '            uvm_config_db#(bit)::set(this, "env*", "a2c_rt_on_model", rt_on_model != 0);',
             '        end',
             f'        env = {uvm["tbEnvClass"]}::type_id::create("env", this);',
             '        run_timeout = a2c_run_timeout::type_id::create("run_timeout", this);',
             '    endfunction',
             '',
             '    virtual function void connect_phase(uvm_phase phase);',
             '        super.connect_phase(phase);',
             f"        run_timeout.clk_vif = env.{uvm['clocks'][0]['vif']};",
             f"        run_timeout.clock   = \"{uvm['clocks'][0]['clock']}\";",
             '        run_timeout.work    = this;',
             '    endfunction',
             '',
             '    virtual function void start_of_simulation_phase(uvm_phase phase);',
             '        super.start_of_simulation_phase(phase);',
             '        a2c_rerun::start();',
             '    endfunction',
             '',
             '    virtual task run_phase(uvm_phase phase);',
             '        phase.raise_objection(this);']
    lines += [f"        env.{clock['vif']}.wait_reset_release();" for clock in uvm['clocks']]
    lines += ['        run_body();',
              '        wait_for_outputs();',
              '        phase.drop_objection(this);',
              '    endtask',
              '',
              '    virtual task run_body();',
              '    endtask',
              '',
              '    // Each output waits on its own clock. A test may call this between',
              '    // frames too. In paired mode its return is a stable point for the',
              '    // model comparators.',
              '    task wait_for_outputs();']
    if counters:
        lines.append('        fork')
        lines += [f"            env.{port['counter']}.wait_for_count(env.{port['clockVif']}, output_deadline_cycles, quiet_cycles);"
                  for port in counters]
        lines.append('        join')
    lines += ['        if (env.dual_dut) begin',
              '            env.model_stable_point();',
              '        end',
              '    endtask',
              '']
    resets = [clock for clock in uvm['clocks'] if clock['reset']]
    hasRegModel = uvm['registerBus'] is not None
    lines += ['    // Pulses every reset of the block and returns once each clock samples',
              '    // its reset released. The RTL and the agents abandon what is in',
              '    // flight, and the counters and comparators start again from the']
    if hasRegModel:
        lines += ['    // release. The register model goes back to its reset values, as the',
                  '    // registers do. The model has no mid-run reset, so a run that holds',
                  '    // it gets an A2C_RESET error instead.']
    else:
        lines += ['    // release. The model has no mid-run reset, so a run that holds it',
                  '    // gets an A2C_RESET error instead.']
    lines += ['    task reset_dut();',
              '        bit model;',
              '        void\'(uvm_config_db#(bit)::get(this, "env", "a2c_model_dut", model));',
              '        if (model || env.dual_dut) begin',
              '            `uvm_error("A2C_RESET", "reset_dut(): the run holds the SystemC model, which cannot be reset mid-run; reset only with --uvmDut rtl")',
              '            return;',
              '        end']
    if resets:
        lines.append('        fork')
        lines += [f"            env.{clock['vif']}.request_reset();" for clock in resets]
        lines.append('        join')
        if hasRegModel:
            lines.append('        env.regmodel.reset();')
    else:
        lines.append('        `uvm_error("A2C_RESET", "reset_dut(): the block has no reset to pulse")')
    skipsBus = len(dataInputs) < len(inputs)
    lines += ['    endtask',
              '']
    if skipsBus:
        lines += ['    // Warns about a run that sent nothing on any input but the register',
                  '    // bus and declared no transaction on any output, as the scaffolded',
                  '    // smoke test does until its run_body() sends stimulus, since register',
                  '    // writes alone leave the data path unexercised. A paired-mode',
                  "    // comparator or a check of the test's own may still have run, so the",
                  '    // warning claims no more.']
        sentWhere = 'on any input other than the register bus'
    else:
        lines += ['    // Warns about a run that sent nothing on any input and declared no',
                  '    // transaction on any output, as the scaffolded smoke test does until',
                  '    // its run_body() sends stimulus. A paired-mode comparator or a check',
                  "    // of the test's own may still have run, so the warning claims no more."]
        sentWhere = 'on any input'
    lines += ['    virtual function void check_phase(uvm_phase phase);',
              '        super.check_phase(phase);',
              '        if (no_stimulus_expected || data_stimulus_sent() != 0) return;']
    lines += [f"        if (env.{port['counter']}.declared() != 0) return;" for port in counters]
    lines += [f'        `uvm_warning("A2C_NO_STIMULUS", $sformatf("%s sent no transaction {sentWhere} and declared no transaction on any output. Send stimulus in run_body(), through the input agents\' sequencers or a status input\'s cfg.value, and declare each output\'s transactions with expect_count() on its counter, or set no_stimulus_expected (+a2c_no_stimulus_expected=1) in a test meant to send nothing",',
              '                                                  get_type_name()))',
              '    endfunction',
              '',
              "    // The items the input ports' agents have sent, through their",
              "    // sequencers or, for a status input, their drivers.",
              '    virtual function int unsigned stimulus_sent();',
              '        int unsigned n = 0;']
    lines += [f"        n += a2c_items_sent#({port['name']}_item_t)::of(env.{port['agent']});" for port in inputs]
    lines += ['        return n;',
              '    endfunction',
              '']
    if skipsBus:
        lines += ["    // The items the input ports' agents other than the register bus's",
                  '    // have sent.']
    else:
        lines += ["    // The items the input ports' agents have sent, as stimulus_sent()",
                  '    // counts them before a test adds its own.']
    lines += ['    virtual function int unsigned data_stimulus_sent();',
              '        int unsigned n = 0;']
    lines += [f"        n += a2c_items_sent#({port['name']}_item_t)::of(env.{port['agent']});" for port in dataInputs]
    lines += ['        return n;',
              '    endfunction',
              '',
              "    // The transactions the output counters expect.",
              '    virtual function int unsigned outputs_declared();',
              '        int unsigned n = 0;']
    lines += [f"        n += env.{port['counter']}.declared();" for port in counters]
    lines += ['        return n;',
              '    endfunction',
              f"endclass : {cls}"]
    return '\n' + textwrap.indent('\n'.join(lines), ' '*4) + '\n'


def render_footer(uvm):
    out = ''
    failTest = uvm['failTest']
    if failTest:
        out += '\n' + textwrap.indent('\n'.join(fail_test(uvm, failTest)), ' '*4) + '\n'
    rtFireTest = uvm['rtFireTest']
    if rtFireTest:
        out += '\n' + textwrap.indent('\n'.join(rt_fire_test(uvm, rtFireTest)), ' '*4) + '\n'
    mismatchTest = uvm['modelMismatchTest']
    if mismatchTest:
        out += '\n' + textwrap.indent('\n'.join(model_mismatch_test(uvm, mismatchTest)), ' '*4) + '\n'
    out += f"\nendpackage : {uvm['testPkgName']}\n\n`endif // {uvm['testPkgGuard']}\n"
    return out


def fail_test(uvm, failTest):
    cls = failTest['className']
    # A block with no input port cannot send stimulus, so its fail test has
    # nothing to require of the smoke test.
    inputs = [port for port in uvm['ports'] if port['role'] == 'dst']
    hasInputs = bool(inputs)
    sentWhere = ' on an input other than the register bus' if len(data_inputs(uvm)) < len(inputs) else ''
    lines = ["// The smoke test with more transactions expected on the first output than",
            "// the DUT delivers (+a2c_fail_missing_count, default 1). It passes only if",
            "// the counter reported exactly one A2C_TXN_COUNT, one per lane in paired",
            "// mode, each lane ends missing exactly missing_count transactions, and",
            "// nothing else raised a UVM_ERROR or UVM_FATAL, so a counter that stops",
            "// reporting or reports the wrong shortfall fails it. The missing",
            "// transaction never closes its unit, so the real-time rules are off. It",
            "// clears expect_from_model, whose model lane would absorb the missing",
            "// count, so the smoke test declares its counts as in a run with one DUT."]
    if hasInputs:
        lines += ['// ' + line for line in textwrap.wrap(
            f"It also fails when the smoke test sent no stimulus{sentWhere}, since the shortfall alone "
            "would then pass with a dead data path.", 71)]
    lines += [f"class {cls} extends {uvm['smokeTestClass']};",
            '    a2c_error_demoter demoter;',
            '    int unsigned missing_count = 1;',
            '',
            f"    `uvm_component_utils({cls})",
            '',
            '    function new(string name, uvm_component parent);',
            '        super.new(name, parent);',
            '    endfunction',
            '',
            '    virtual function void build_phase(uvm_phase phase);',
            '        super.build_phase(phase);',
            '        void\'($value$plusargs("a2c_fail_missing_count=%d", missing_count));',
            '        demoter = a2c_error_demoter::type_id::create("demoter");',
            '        demoter.demote_id = "A2C_TXN_COUNT";',
            '        uvm_report_cb::add(null, demoter);',
            "        // Wins over the rt_* knobs, plusargs and set_limits().",
            '        uvm_config_db#(bit)::set(this, "env*", "a2c_rt_off", 1\'b1);',
            '        expect_from_model = 0;',
            '        uvm_config_db#(bit)::set(this, "env*", "a2c_expect_from_model", 1\'b0);',
            '    endfunction',
            '',
            '    virtual task run_body();',
            '        super.run_body();',
            f"        env.{failTest['counter']}.expect_count(missing_count);",
            '    endtask',
            '',
            '    virtual function void report_phase(uvm_phase phase);',
            '        uvm_report_server srv = uvm_report_server::get_server();',
            '        int unsigned others = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);',
            '        int unsigned want = 1;',
            '        string       expected = "one A2C_TXN_COUNT error";',
            '        string       shortfall = "";',
            '        super.report_phase(phase);',
            '        if (env.dual_dut) begin',
            '            want     = 2;',
            '            expected = "one A2C_TXN_COUNT error per lane";',
            '        end',
            '        for (int lane = 0; lane < want; lane++) begin',
            f"            int unsigned pending = env.{failTest['counter']}.lane_pending(a2c_lane_e'(lane));",
            '            if (pending != missing_count) begin',
            '                shortfall = {shortfall, $sformatf("; the %s lane misses %0d, expected %0d", a2c_lane_name(a2c_lane_e\'(lane)),',
            '                                                  pending, missing_count)};',
            '            end',
            '        end']
    if hasInputs:
        lines += ['        if (data_stimulus_sent() == 0) begin',
                  f"            `uvm_error(\"A2C_FAIL_TEST\", \"{uvm['smokeTestClass']} sent no stimulus{sentWhere}, so the missing transactions would also be missing with a dead data path; send stimulus in its run_body()\")",
                  '        end else if (demoter.demoted != want || others != 0 || shortfall != "") begin']
    else:
        lines += ['        if (demoter.demoted != want || others != 0 || shortfall != "") begin']
    lines += ['            `uvm_error("A2C_FAIL_TEST", $sformatf("expected exactly %s and no other error; caught %0d A2C_TXN_COUNT, %0d other UVM_ERROR/UVM_FATAL%s",',
            '                                                  expected, demoter.demoted, others, shortfall))',
            '        end else begin',
            '            `uvm_info("A2C_FAIL_TEST", "the transaction counter reported the missing transactions as intended", UVM_LOW)',
            '        end',
            '    endfunction',
            f"endclass : {cls}"]
    return lines


def rt_fire_test(uvm, rtFireTest):
    cls = rtFireTest['className']
    return ["// The smoke test with the lag bound of every a2c_rt_checker under env at",
            "// 1 clock (rt_lag_cycles), below the lag of any DUT that registers its",
            "// output, which proves each checker's wiring: every output unit it pairs",
            "// with an input unit misses its deadline once. Each A2C_RT_DEADLINE is",
            "// demoted and counted. It passes only if env holds a checker that is not",
            "// off, each such checker paired at least one unit and failed each one",
            "// once, and the demoted errors are the failures of the checkers that",
            "// judge, which on the model DUT is none unless rt_on_model is set. A",
            "// checker under env that is off, by a2c_rt_off or turn_off(), is left",
            "// out.",
            f"class {cls} extends {uvm['smokeTestClass']};",
            '    a2c_error_demoter demoter;',
            '',
            f"    `uvm_component_utils({cls})",
            '',
            '    function new(string name, uvm_component parent);',
            '        super.new(name, parent);',
            '        rt_lag_cycles = 1;',
            '    endfunction',
            '',
            '    virtual function void build_phase(uvm_phase phase);',
            '        super.build_phase(phase);',
            '        demoter = a2c_error_demoter::type_id::create("demoter");',
            '        demoter.demote_id = "A2C_RT_DEADLINE";',
            '        uvm_report_cb::add(null, demoter);',
            '    endfunction',
            '',
            "    // The checkers under env that are on.",
            '    function void env_checkers(output a2c_rt_checker_base found[$]);',
            '        a2c_rt_checker_base all[$];',
            '        a2c_rt_checker_base::get_checkers(all);',
            '        foreach (all[k]) begin',
            '            uvm_component p = all[k].get_parent();',
            '            while (p != null && p != env) p = p.get_parent();',
            '            if (p != null && !all[k].off) found.push_back(all[k]);',
            '        end',
            '    endfunction',
            '',
            "    // Every failure prints, so the demoter counts each one.",
            '    virtual function void start_of_simulation_phase(uvm_phase phase);',
            '        a2c_rt_checker_base rts[$];',
            '        super.start_of_simulation_phase(phase);',
            '        env_checkers(rts);',
            "        foreach (rts[k]) rts[k].max_reported = '1;",
            '    endfunction',
            '',
            '    virtual function void report_phase(uvm_phase phase);',
            '        a2c_rt_checker_base rts[$];',
            '        int unsigned want = 0;',
            '        string       wrong = "";',
            '        super.report_phase(phase);',
            '        env_checkers(rts);',
            '        foreach (rts[k]) begin',
            '            if (rts[k].units_checked() == 0 || rts[k].failures_seen() != rts[k].units_checked()) begin',
            '                wrong = {wrong, $sformatf("; %s paired %0d units and failed %0d", rts[k].get_full_name(),',
            '                                          rts[k].units_checked(), rts[k].failures_seen())};',
            '            end',
            '            if (rts[k].judges()) want += rts[k].units_checked();',
            '        end',
            '        if (rts.size() == 0) begin',
            f'            `uvm_error("A2C_RT_FIRE", "{cls} found no a2c_rt_checker under env with its rules on; the test proves the wiring of the env\'s checkers")',
            '        end else if (wrong != "" || demoter.demoted != want) begin',
            '            `uvm_error("A2C_RT_FIRE", $sformatf("expected each checker to fail each unit it paired once, and %0d A2C_RT_DEADLINE errors; caught %0d%s",',
            '                                                want, demoter.demoted, wrong))',
            '        end else begin',
            '            `uvm_info("A2C_RT_FIRE", $sformatf("%0d checkers each failed every unit they paired, %0d A2C_RT_DEADLINE errors as intended",',
            '                                               rts.size(), demoter.demoted), UVM_LOW)',
            '        end',
            '    endfunction',
            f"endclass : {cls}"]


def model_mismatch_test(uvm, mismatchTest):
    cls = mismatchTest['className']
    agent = mismatchTest['agent']
    return ["// The smoke test with a mismatch injected at pair +a2c_model_mismatch_at",
            "// (default 1) of the first counted output's model comparator. It runs",
            "// only in paired mode. Only the injected A2C_MODEL_CMP is demoted, so any",
            "// other mismatch stays an error. It passes only if that one report",
            "// arrived, the comparator compared at least mismatch_at pairs, and",
            "// nothing else raised a UVM_ERROR or UVM_FATAL.",
            f"class {cls} extends {uvm['smokeTestClass']};",
            '    a2c_error_demoter demoter;',
            '    int unsigned mismatch_at = 1;',
            '',
            f"    `uvm_component_utils({cls})",
            '',
            '    function new(string name, uvm_component parent);',
            '        super.new(name, parent);',
            '    endfunction',
            '',
            '    virtual function void build_phase(uvm_phase phase);',
            '        super.build_phase(phase);',
            '        void\'($value$plusargs("a2c_model_mismatch_at=%d", mismatch_at));',
            '        demoter = a2c_error_demoter::type_id::create("demoter");',
            '        demoter.demote_id = "A2C_MODEL_CMP";',
            '        demoter.demote_text = "(injected mismatch)";',
            '        uvm_report_cb::add(null, demoter);',
            '    endfunction',
            '',
            '    virtual function void connect_phase(uvm_phase phase);',
            '        super.connect_phase(phase);',
            '        if (!env.dual_dut) begin',
            f'            `uvm_fatal("A2C_CFG", "{cls} compares the model DUT against the RTL and runs only on the both DUT")',
            '        end',
            f"        env.{agent}.model_cmp.inject_mismatch(mismatch_at);",
            '    endfunction',
            '',
            '    virtual function void report_phase(uvm_phase phase);',
            '        uvm_report_server srv = uvm_report_server::get_server();',
            '        int unsigned others = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);',
            f"        int unsigned pairs = env.{agent}.model_cmp.get_pairs();",
            '        super.report_phase(phase);',
            '        if (demoter.demoted != 1 || others != 0 || pairs < mismatch_at) begin',
            '            `uvm_error("A2C_MISMATCH_TEST", $sformatf("expected exactly one injected A2C_MODEL_CMP at pair %0d and no other error; caught %0d injected, %0d other UVM_ERROR/UVM_FATAL, %0d pairs compared",',
            '                                                      mismatch_at, demoter.demoted, others, pairs))',
            '        end else begin',
            '            `uvm_info("A2C_MISMATCH_TEST", "the model comparator reported the injected mismatch as intended", UVM_LOW)',
            '        end',
            '    endfunction',
            f"endclass : {cls}"]
