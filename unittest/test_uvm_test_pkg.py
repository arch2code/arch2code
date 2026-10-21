#!/usr/bin/env python3
"""A hasUvm block gets one test package for all its variants, scaffolded with
tests that compile and pass before the user writes any.

The package imports its variant package through the A2C_UVM_PKG define, so
the one file serves every variant's top, and an undefined A2C_UVM_PKG names
itself in the compile error. Its layout is fixed: the generated header with
the include guard, the package line and the imports the variant package
makes; a user span holding `<block>_tb_env extends <block>_env`; the
generated `<block>_base_test`; a user span holding `<block>_smoke_test` with
an empty run_body(); and the generated footer with `<block>_fail_test`. The
base test creates the env through the factory as `<block>_tb_env`, waits for
reset, runs run_body() and then waits for every counted output under one
objection. It hands the env its clock stop and the drain's window, deadline,
catch-up and cut setting through the config_db, each from its plusarg. A
value a test sets in its constructor stands until a plusarg overrides it,
the drain's included: only a drain window or deadline left at -1 takes the
quiet window or output deadline, and a catch-up left at -1 is not set, so
each replay log takes its own deadline. In
Mode B, which the env reads from a2c_dual_dut, each return of
wait_for_outputs() is a stable point for the model comparators. The fail test
adds the missing transactions to the first counted output after the smoke
stimulus, and passes only on exactly one A2C_TXN_COUNT error, or one per lane
in Mode B, with each lane's pending count equal to the missing count. A block
with a model, and so a both DUT, also gets `<block>_model_mismatch_test`,
which injects a mismatch on that output's model comparator, stops with A2C_CFG
outside Mode B, demotes only the A2C_MODEL_CMP that carries the injection
marker, and passes only on exactly one of those with at least mismatch_at
pairs compared. make gen rewrites only the generated sections, so a user
edit in either span survives it.

A copy of `fixtures/uvm-blocks` with the two variants of
test_uvm_register_view.py must give one ubDut_uvm_test_pkg.sv, named by both
tops' A2C_UVM_TEST_SV. A second copy drops ubDut's two output ports, out and
rdM, so it has no counted output: its test package has no fail or model
mismatch test, waits on no output, and still takes the stable point. A third
copy gives ubDut no model, so it keeps the fail test and has no model mismatch
test. A fourth copy gives ubDut an apb master port, mst. The apb slave agent
drains its replay log itself, so that copy's wait_for_outputs() ends in Mode B
with the stable point alone, as every copy's does.

The loopback simulates the template's base test too:
common/systemVerilog/uvm/loopback/a2c_gen_base_test_lb_tests.svh holds
render_tests() of it for a stand-in env between its RENDERED markers, and
must match the template's current text.
"""

import os
import shutil
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree
from test_build_manifest import parse_manifest
import test_uvm_pkg_regmodel as regModel
import test_uvm_register_view as regView
from templates.systemVerilog import uvmTest


NO_OUTPUT_EDITS = [
    ('            out: { interface: ubStream, direction: src }\n', ''),
    ('    - { interface: ubStream, src: uDut, srcport: out, dst: uSink, dstport: in, name: outLink }\n', ''),
    ('            rdM: { interface: ubRd, direction: src }\n', ''),
    ('    - { interface: ubRd, src: uDut, srcport: rdM, dst: uSink, dstport: rdIn, name: rdOut, maxTransferSize: 32 }\n',
     ''),
]

MASTER_EDITS = regModel.MASTER_EDITS

NO_MODEL_EDITS = [
    ('        desc: "DUT under the UVM testbench"\n        hasMdl: true\n',
     '        desc: "DUT under the UVM testbench"\n        hasMdl: false\n'),
]

HEADER = [
    '`ifndef UBDUT_UVM_TEST_PKG_SV',
    '`define UBDUT_UVM_TEST_PKG_SV',
    '`ifndef A2C_UVM_PKG',
    '`define A2C_UVM_PKG A2C_UVM_PKG_is_not_defined__define_it_as_the_variant_uvm_package',
    '`endif',
    'package ubDut_uvm_test_pkg;',
    'import uvm_pkg::*;',
    '`include "uvm_macros.svh"',
    'import a2c_uvm_pkg::*;',
    'import rdy_vld_uvm_pkg::*;',
    'import apb_uvm_pkg::*;',
    'import uvmBlocks_package::*;',
    'import `A2C_UVM_PKG::*;',
]

SPAN_1 = [
    'class ubDut_tb_env extends ubDut_env;',
    '`uvm_component_utils(ubDut_tb_env)',
    'function new(string name, uvm_component parent);',
    'super.new(name, parent);',
    'endfunction',
    'endclass : ubDut_tb_env',
]

BASE_TEST = [
    'class ubDut_base_test extends uvm_test;',
    'ubDut_tb_env env;',
    'int unsigned output_deadline_cycles = 200000;',
    'int unsigned quiet_cycles = 1000;',
    'int unsigned clock_stop_cycles = 1000;',
    'int          drain_quiet_cycles = -1;',
    'int          drain_deadline_cycles = -1;',
    'int          drain_catchup_cycles = -1;',
    'bit          drain_cut_expected;',
    '`uvm_component_utils(ubDut_base_test)',
    'void\'($value$plusargs("a2c_output_deadline_cycles=%d", output_deadline_cycles));',
    'void\'($value$plusargs("a2c_quiet_cycles=%d", quiet_cycles));',
    'void\'($value$plusargs("a2c_clock_stop_cycles=%d", clock_stop_cycles));',
    'if (drain_quiet_cycles < 0) drain_quiet_cycles = quiet_cycles;',
    'if (drain_deadline_cycles < 0) drain_deadline_cycles = output_deadline_cycles;',
    'void\'($value$plusargs("a2c_drain_quiet_cycles=%d", drain_quiet_cycles));',
    'void\'($value$plusargs("a2c_drain_deadline_cycles=%d", drain_deadline_cycles));',
    'void\'($value$plusargs("a2c_drain_catchup_cycles=%d", drain_catchup_cycles));',
    'void\'($value$plusargs("a2c_drain_cut_expected=%d", drain_cut_expected));',
    'uvm_config_db#(int unsigned)::set(this, "env*", "a2c_clock_stop_cycles", clock_stop_cycles);',
    'uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_quiet_cycles", drain_quiet_cycles);',
    'uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_deadline_cycles", drain_deadline_cycles);',
    'if (drain_catchup_cycles >= 0) begin',
    'uvm_config_db#(int unsigned)::set(this, "env*", "a2c_drain_catchup_cycles", drain_catchup_cycles);',
    'uvm_config_db#(bit)::set(this, "env*", "a2c_drain_cut_expected", drain_cut_expected);',
    'env = ubDut_tb_env::type_id::create("env", this);',
    'virtual task run_phase(uvm_phase phase);',
    'phase.raise_objection(this);',
    'env.clk_vif.wait_reset_release();',
    'run_body();',
    'wait_for_outputs();',
    'phase.drop_objection(this);',
    'virtual task run_body();',
    'task wait_for_outputs();',
]
OUTPUT_WAIT = [
    'fork',
    'env.out_counter.wait_for_count(env.clk_vif, output_deadline_cycles, quiet_cycles);',
    'join',
]
STABLE_POINT = [
    'if (env.dual_dut) begin',
    'env.model_stable_point();',
    'end',
    'endtask',
    'endclass : ubDut_base_test',
]

# The Mode B tail of wait_for_outputs(), whole and in order.
MODE_B_TAIL = ['if (env.dual_dut) begin', 'env.model_stable_point();', 'end', 'endtask']

SPAN_2 = [
    'class ubDut_smoke_test extends ubDut_base_test;',
    '`uvm_component_utils(ubDut_smoke_test)',
    'virtual task run_body();',
    'endtask',
    'endclass : ubDut_smoke_test',
]

FAIL_TEST = [
    'class ubDut_fail_test extends ubDut_smoke_test;',
    'a2c_error_demoter demoter;',
    'int unsigned missing_count = 1;',
    'void\'($value$plusargs("a2c_fail_missing_count=%d", missing_count));',
    'demoter.demote_id = "A2C_TXN_COUNT";',
    'uvm_report_cb::add(null, demoter);',
    'super.run_body();',
    'env.out_counter.expect_count(missing_count);',
    'int unsigned want = 1;',
    'if (env.dual_dut) begin',
    'want     = 2;',
    'for (int lane = 0; lane < want; lane++) begin',
    "int unsigned pending = env.out_counter.lane_pending(a2c_lane_e'(lane));",
    'if (pending != missing_count) begin',
    'if (demoter.demoted != want || others != 0 || shortfall != "") begin',
    'endclass : ubDut_fail_test',
]

MISMATCH_TEST = [
    'class ubDut_model_mismatch_test extends ubDut_smoke_test;',
    'a2c_error_demoter demoter;',
    'int unsigned mismatch_at = 1;',
    'void\'($value$plusargs("a2c_model_mismatch_at=%d", mismatch_at));',
    'demoter.demote_id = "A2C_MODEL_CMP";',
    'demoter.demote_text = "(injected mismatch)";',
    'uvm_report_cb::add(null, demoter);',
    'virtual function void connect_phase(uvm_phase phase);',
    'if (!env.dual_dut) begin',
    '`uvm_fatal("A2C_CFG", "ubDut_model_mismatch_test compares the model DUT against the RTL and runs only on the both DUT")',
    'env.out_agent.model_cmp.inject_mismatch(mismatch_at);',
    'int unsigned pairs = env.out_agent.model_cmp.get_pairs();',
    'if (demoter.demoted != 1 || others != 0 || pairs < mismatch_at) begin',
    'endclass : ubDut_model_mismatch_test',
]

FOOTER = ['endpackage : ubDut_uvm_test_pkg', '`endif // UBDUT_UVM_TEST_PKG_SV']

USER_LINE = '// a user line in the env span'

LOOPBACK_COPY = os.path.join(base_dir, 'common', 'systemVerilog', 'uvm', 'loopback', 'a2c_gen_base_test_lb_tests.svh')
LOOPBACK_UVM = {'baseTestClass': 'lb_gen_base', 'tbEnvClass': 'lb_gen_env', 'ports': [],
                'clocks': [{'vif': 'clk_vif'}]}


def regions(path):
    """The file as [(kind, [stripped non-blank lines])]: 'user' for text
    outside the markers, else the generated section's name."""
    out = [('user', [])]
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if line.startswith('// GENERATED_CODE_BEGIN'):
                out.append((line.split('--section=')[1], []))
            elif line.startswith('// GENERATED_CODE_END'):
                out.append(('user', []))
            elif line and not line.startswith('// GENERATED_CODE_PARAM') and line != '//':
                out[-1][1].append(line)
    return [(kind, lines) for kind, lines in out if kind != 'user' or lines]


def in_order(lines, expected):
    """Whether expected occurs in lines in order, each line once."""
    position = 0
    for line in expected:
        if line not in lines[position:]:
            return False
        position = lines.index(line, position) + 1
    return True


def check_layout(path, hasOutput, hasModel=True):
    problems = []
    name = os.path.basename(path)
    layout = regions(path)
    kinds = [kind for kind, _ in layout]
    if kinds != ['header', 'user', 'tests', 'user', 'footer']:
        return [f"{name} has the regions {kinds}, expected header, user, tests, user, footer"]
    (_, header), (_, span1), (_, tests), (_, span2), (_, footer) = layout
    baseTest = BASE_TEST + (OUTPUT_WAIT if hasOutput else []) + STABLE_POINT
    footerTests = (FAIL_TEST if hasOutput else []) + (MISMATCH_TEST if hasOutput and hasModel else [])
    for what, lines, expected in (('header', header, HEADER), ('env span', span1, SPAN_1),
                                  ('tests section', tests, baseTest), ('smoke span', span2, SPAN_2),
                                  ('footer', footer, footerTests + FOOTER)):
        if not in_order(lines, expected):
            problems.append(f"{name} {what} is\n    {lines}\n  expected in order\n    {expected}")
    if not hasOutput and any(line in tests + footer for line in OUTPUT_WAIT + FAIL_TEST[:1]):
        problems.append(f"{name} waits on an output or declares a fail test, and the block has no counted output")
    if not (hasOutput and hasModel) and MISMATCH_TEST[0] in footer:
        problems.append(f"{name} declares a model mismatch test, and the block has no model or no counted output")
    start = tests.index(MODE_B_TAIL[0]) if MODE_B_TAIL[0] in tests else -1
    if start < 0 or tests[start:start + len(MODE_B_TAIL)] != MODE_B_TAIL:
        problems.append(f"{name} tests section is\n    {tests}\n  expected the Mode B tail\n    {MODE_B_TAIL}")
    return problems


def make(project, target):
    result = regModel.make(project, target)
    return None if result.returncode == 0 else f"make {target} failed:\n{result.stdout}{result.stderr}"


def build(project, extraEdits):
    shutil.copytree(regView.FIXTURE, project)
    regView.edit_fixture(project)
    path = os.path.join(project, regView.ARCH)
    with open(path) as f:
        text = f.read()
    for old, new in extraEdits:
        if text.count(old) != 1:
            raise RuntimeError(f"fixture no longer carries the single anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)
    for target in ('db', 'newmodule', 'gen'):
        failure = make(project, target)
        if failure:
            return failure
    return None


def check_two_variants(project):
    failure = build(project, [])
    if failure:
        return [failure]
    uvmDir = os.path.join(project, 'uvm')
    testPkgs = sorted(name for name in os.listdir(uvmDir) if name.endswith('_uvm_test_pkg.sv'))
    if testPkgs != ['ubDut_uvm_test_pkg.sv']:
        return [f"uvm/ holds the test packages {testPkgs}, expected ubDut_uvm_test_pkg.sv alone"]
    path = os.path.join(uvmDir, 'ubDut_uvm_test_pkg.sv')
    problems = check_layout(path, hasOutput=True)
    man = parse_manifest(os.path.join(project, '.gen', 'build.mk'))
    for variant in regView.PKG:
        key = f'A2C_UVM_TEST_SV_ubDut_{variant}_uvm_tb'
        if man.get(key) != [path]:
            problems.append(f"{key} is {man.get(key)}, expected [{path}]")
    # make gen keeps a user edit in a span and regenerates the sections.
    with open(path) as f:
        text = f.read()
    with open(path, 'w') as f:
        f.write(text.replace('    class ubDut_tb_env extends', f'    {USER_LINE}\n    class ubDut_tb_env extends', 1))
    failure = make(project, 'gen')
    if failure:
        return problems + [failure]
    layout = regions(path)
    if USER_LINE not in layout[1][1]:
        problems.append(f"make gen dropped the user line from the env span: {layout[1][1]}")
    problems += check_layout(path, hasOutput=True)
    return problems


def check_no_output(project):
    failure = build(project, NO_OUTPUT_EDITS)
    if failure:
        return [failure]
    return check_layout(os.path.join(project, 'uvm', 'ubDut_uvm_test_pkg.sv'), hasOutput=False)


def check_no_model(project):
    failure = build(project, NO_MODEL_EDITS)
    if failure:
        return [failure]
    return check_layout(os.path.join(project, 'uvm', 'ubDut_uvm_test_pkg.sv'), hasOutput=True, hasModel=False)


def check_master(project):
    failure = build(project, MASTER_EDITS)
    if failure:
        return [failure]
    problems = check_layout(os.path.join(project, 'uvm', 'ubDut_uvm_test_pkg.sv'), hasOutput=True)
    for name in sorted(os.listdir(os.path.join(project, 'uvm'))):
        with open(os.path.join(project, 'uvm', name)) as f:
            if 'wait_for_replay' in f.read():
                problems.append(f"{name} mentions wait_for_replay, which the slave's drain replaced")
    return problems


def check_loopback_copy(_project):
    with open(LOOPBACK_COPY) as f:
        text = f.read()
    begin = '    // RENDERED BEGIN\n'
    end = '    // RENDERED END\n'
    if text.count(begin) != 1 or text.count(end) != 1:
        return [f"{LOOPBACK_COPY} lacks one RENDERED BEGIN and one RENDERED END marker"]
    copy = text[text.index(begin) + len(begin):text.index(end)]
    rendered = uvmTest.render_tests(LOOPBACK_UVM).lstrip('\n')
    if copy != rendered:
        return [f"{LOOPBACK_COPY} holds a stale render of the base test; replace the span between its markers with\n{rendered}"]
    return []


def run_all_tests():
    print("\n" + "=" * 70)
    print("UVM TEST PACKAGE SCAFFOLD")
    print("=" * 70)
    tmp = tempfile.mkdtemp(prefix='uvm_test_pkg_', dir=test_dir)
    ok = True
    try:
        for name, check in (('one test package for two variants, kept across make gen', check_two_variants),
                            ('no fail test without a counted output', check_no_output),
                            ('no model mismatch test without a model', check_no_model),
                            ('no generated drain for an apb master port', check_master),
                            ('the loopback simulates the current base test', check_loopback_copy)):
            problems = check(os.path.join(tmp, check.__name__))
            for problem in problems:
                print(f"  FAIL: {name}: {problem}")
            if not problems:
                print(f"  PASS: {name}")
            ok = ok and not problems
    finally:
        remove_tree(tmp)
    if ok:
        print("\nPASS: the test package scaffold has its layout and working defaults")
        return 0
    print("\nFAIL: the test package scaffold is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
