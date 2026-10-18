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
             "// expected transactions. +a2c_output_deadline_cycles and +a2c_quiet_cycles",
             "// set the wait's deadline and quiet window; a test may also set them in",
             "// build_phase after super.build_phase.",
             f"class {cls} extends uvm_test;",
             f"    {uvm['tbEnvClass']} env;",
             '    int unsigned output_deadline_cycles = 200000;',
             '    int unsigned quiet_cycles = 1000;',
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
              '    // frames too.',
              '    task wait_for_outputs();']
    if counters:
        lines.append('        fork')
        lines += [f"            env.{port['counter']}.wait_for_count(env.{port['clockVif']}, output_deadline_cycles, quiet_cycles);"
                  for port in counters]
        lines.append('        join')
    lines += ['    endtask',
              f"endclass : {cls}"]
    return '\n' + textwrap.indent('\n'.join(lines), ' '*4) + '\n'


def render_footer(uvm):
    out = ''
    failTest = uvm['failTest']
    if failTest:
        cls = failTest['className']
        lines = ["// The smoke test with more transactions expected on the first output than",
                 "// the DUT delivers (+a2c_fail_missing_beats, default 1). It passes only if",
                 "// the counter reported exactly one A2C_TXN_COUNT and nothing else raised a",
                 "// UVM_ERROR or UVM_FATAL, so a counter that stops reporting fails it.",
                 f"class {cls} extends {uvm['smokeTestClass']};",
                 '    a2c_error_demoter demoter;',
                 '    int unsigned missing_beats = 1;',
                 '',
                 f"    `uvm_component_utils({cls})",
                 '',
                 '    function new(string name, uvm_component parent);',
                 '        super.new(name, parent);',
                 '    endfunction',
                 '',
                 '    virtual function void build_phase(uvm_phase phase);',
                 '        super.build_phase(phase);',
                 '        void\'($value$plusargs("a2c_fail_missing_beats=%d", missing_beats));',
                 '        demoter = a2c_error_demoter::type_id::create("demoter");',
                 '        demoter.demote_id = "A2C_TXN_COUNT";',
                 '        uvm_report_cb::add(null, demoter);',
                 '    endfunction',
                 '',
                 '    virtual task run_body();',
                 f"        env.{failTest['counter']}.expect_count(missing_beats);",
                 '        super.run_body();',
                 '    endtask',
                 '',
                 '    virtual function void report_phase(uvm_phase phase);',
                 '        uvm_report_server srv = uvm_report_server::get_server();',
                 '        int unsigned others = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);',
                 '        super.report_phase(phase);',
                 '        if (demoter.demoted != 1 || others != 0) begin',
                 '            `uvm_error("A2C_FAIL_TEST", $sformatf("expected exactly one A2C_TXN_COUNT error and no other error; caught %0d A2C_TXN_COUNT, %0d other UVM_ERROR/UVM_FATAL",',
                 '                                                  demoter.demoted, others))',
                 '        end else begin',
                 '            `uvm_info("A2C_FAIL_TEST", "the transaction counter reported the missing transactions as intended", UVM_LOW)',
                 '        end',
                 '    endfunction',
                 f"endclass : {cls}"]
        out += '\n' + textwrap.indent('\n'.join(lines), ' '*4) + '\n'
    out += f"\nendpackage : {uvm['testPkgName']}\n\n`endif // {uvm['testPkgGuard']}\n"
    return out
