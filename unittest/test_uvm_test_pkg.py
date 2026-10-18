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
objection. The fail test adds the missing transactions to the first counted
output after the smoke stimulus, and passes only on exactly one
A2C_TXN_COUNT error. make gen rewrites only the generated sections, so a user
edit in either span survives it.

A copy of `fixtures/uvm-blocks` with the two variants of
test_uvm_register_view.py must give one ubDut_uvm_test_pkg.sv, named by both
tops' A2C_UVM_TEST_SV. A second copy drops ubDut's output port, so it has no
counted output: its test package has no fail test and waits on no output.
"""

import os
import shutil
import sys
import tempfile

from _addrctl_helpers import test_dir
from _tmp_helpers import remove_tree
from test_build_manifest import parse_manifest
import test_uvm_pkg_regmodel as regModel
import test_uvm_register_view as regView


NO_OUTPUT_EDITS = [
    ('            out: { interface: ubStream, direction: src }\n', ''),
    ('    - { interface: ubStream, src: uDut, srcport: out, dst: uSink, dstport: in, name: outLink }\n', ''),
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
    '`uvm_component_utils(ubDut_base_test)',
    'void\'($value$plusargs("a2c_output_deadline_cycles=%d", output_deadline_cycles));',
    'void\'($value$plusargs("a2c_quiet_cycles=%d", quiet_cycles));',
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
    'if (demoter.demoted != 1 || others != 0) begin',
    'endclass : ubDut_fail_test',
]

FOOTER = ['endpackage : ubDut_uvm_test_pkg', '`endif // UBDUT_UVM_TEST_PKG_SV']

USER_LINE = '// a user line in the env span'


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


def check_layout(path, hasOutput):
    problems = []
    name = os.path.basename(path)
    layout = regions(path)
    kinds = [kind for kind, _ in layout]
    if kinds != ['header', 'user', 'tests', 'user', 'footer']:
        return [f"{name} has the regions {kinds}, expected header, user, tests, user, footer"]
    (_, header), (_, span1), (_, tests), (_, span2), (_, footer) = layout
    baseTest = BASE_TEST + (OUTPUT_WAIT if hasOutput else [])
    for what, lines, expected in (('header', header, HEADER), ('env span', span1, SPAN_1),
                                  ('tests section', tests, baseTest), ('smoke span', span2, SPAN_2),
                                  ('footer', footer, (FAIL_TEST if hasOutput else []) + FOOTER)):
        if not in_order(lines, expected):
            problems.append(f"{name} {what} is\n    {lines}\n  expected in order\n    {expected}")
    if not hasOutput and any(line in tests + footer for line in OUTPUT_WAIT + FAIL_TEST[:1]):
        problems.append(f"{name} waits on an output or declares a fail test, and the block has no counted output")
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


def run_all_tests():
    print("\n" + "=" * 70)
    print("UVM TEST PACKAGE SCAFFOLD")
    print("=" * 70)
    tmp = tempfile.mkdtemp(prefix='uvm_test_pkg_', dir=test_dir)
    ok = True
    try:
        for name, check in (('one test package for two variants, kept across make gen', check_two_variants),
                            ('no fail test without a counted output', check_no_output)):
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
