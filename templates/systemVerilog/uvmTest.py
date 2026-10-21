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


def render_tests(uvm):
    cls = uvm['baseTestClass']
    counters = [port for port in uvm['ports'] if port['counter']]
    lines = ["// Waits for reset, runs run_body(), then waits for every output's",
             "// expected transactions. A test sets its own default deadline, quiet",
             "// window and clock stop in its constructor; +a2c_output_deadline_cycles,",
             "// +a2c_quiet_cycles and +a2c_clock_stop_cycles override them. A clock",
             "// with no edge for clock_stop_cycles of its periods has stopped. In",
             "// Mode B the drain at the end of the run phase has its own window,",
             "// deadline and catch-up after a cut, which a test may set in its",
             "// constructor too, and +a2c_drain_quiet_cycles,",
             "// +a2c_drain_deadline_cycles and +a2c_drain_catchup_cycles override.",
             "// Left at -1, the window and deadline take quiet_cycles and",
             "// output_deadline_cycles, and the catch-up takes each replay log's",
             "// deadline. +a2c_drain_cut_expected=1 reports the drain's cuts as",
             "// UVM_INFO.",
             f"class {cls} extends uvm_test;",
             f"    {uvm['tbEnvClass']} env;",
             '    int unsigned output_deadline_cycles = 200000;',
             '    int unsigned quiet_cycles = 1000;',
             '    int unsigned clock_stop_cycles = 1000;',
             '    int          drain_quiet_cycles = -1;',
             '    int          drain_deadline_cycles = -1;',
             '    int          drain_catchup_cycles = -1;',
             '    bit          drain_cut_expected;',
             '',
             f"    `uvm_component_utils({cls})",
             '',
             '    function new(string name, uvm_component parent);',
             '        super.new(name, parent);',
             '    endfunction',
             '',
             '    virtual function void build_phase(uvm_phase phase);',
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
             '        uvm_config_db#(int unsigned)::set(this, "env*", "a2c_clock_stop_cycles", clock_stop_cycles);',
             '        uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_quiet_cycles", drain_quiet_cycles);',
             '        uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_deadline_cycles", drain_deadline_cycles);',
             '        if (drain_catchup_cycles >= 0) begin',
             '            uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_catchup_cycles", drain_catchup_cycles);',
             '        end',
             '        uvm_config_db#(bit)::set(this, "env*", "a2c_drain_cut_expected", drain_cut_expected);',
             f'        env = {uvm["tbEnvClass"]}::type_id::create("env", this);',
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
              '    // frames too. In Mode B its return is a stable point for the model',
              '    // comparators.',
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
              f"endclass : {cls}"]
    return '\n' + textwrap.indent('\n'.join(lines), ' '*4) + '\n'


def render_footer(uvm):
    out = ''
    failTest = uvm['failTest']
    if failTest:
        out += '\n' + textwrap.indent('\n'.join(fail_test(uvm, failTest)), ' '*4) + '\n'
    mismatchTest = uvm['modelMismatchTest']
    if mismatchTest:
        out += '\n' + textwrap.indent('\n'.join(model_mismatch_test(uvm, mismatchTest)), ' '*4) + '\n'
    out += f"\nendpackage : {uvm['testPkgName']}\n\n`endif // {uvm['testPkgGuard']}\n"
    return out


def fail_test(uvm, failTest):
    cls = failTest['className']
    return ["// The smoke test with more transactions expected on the first output than",
            "// the DUT delivers (+a2c_fail_missing_count, default 1). It passes only if",
            "// the counter reported exactly one A2C_TXN_COUNT, one per lane in Mode B,",
            "// each lane ends missing exactly missing_count transactions, and nothing",
            "// else raised a UVM_ERROR or UVM_FATAL, so a counter that stops reporting",
            "// or reports the wrong shortfall fails it.",
            f"class {cls} extends {uvm['smokeTestClass']};",
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
            '        end',
            '        if (demoter.demoted != want || others != 0 || shortfall != "") begin',
            '            `uvm_error("A2C_FAIL_TEST", $sformatf("expected exactly %s and no other error; caught %0d A2C_TXN_COUNT, %0d other UVM_ERROR/UVM_FATAL%s",',
            '                                                  expected, demoter.demoted, others, shortfall))',
            '        end else begin',
            '            `uvm_info("A2C_FAIL_TEST", "the transaction counter reported the missing transactions as intended", UVM_LOW)',
            '        end',
            '    endfunction',
            f"endclass : {cls}"]


def model_mismatch_test(uvm, mismatchTest):
    cls = mismatchTest['className']
    agent = mismatchTest['agent']
    return ["// The smoke test with a mismatch injected at pair +a2c_model_mismatch_at",
            "// (default 1) of the first counted output's model comparator. It runs",
            "// only in Mode B. Only the injected A2C_MODEL_CMP is demoted, so any",
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
