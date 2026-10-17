#!/usr/bin/env python3
"""A hasUvm block the UVM testbench cannot drive is rejected at db.

The testbench instantiates the block's HDL verification wrapper, gives every
boundary port an agent of its interface type, and drives every clock and reset
of the block. `validateUvmBlocks` (`pysrc/processYaml.py`) rejects a block
that breaks one of those assumptions, naming the block and, where one is at
fault, the port and its interface type. The boundary covers more than ports:.
A connectionMaps boundary port, a memoryConnections port and a
registerConnections port need no ports: row, and the wrapper still has a pin
group for each.

The uvm-blocks fixture holds ubDut, an accepted hasUvm block with two rdy_vld
ports and an apb register bus. Each negative arm edits one rule's violation
into a copy. A block with params whose only variants another project declares
has no standalone variant, so the testbench would have no top for it.
"""

import os
import shutil
import sys
import subprocess
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree


FIXTURE = os.path.join(test_dir, 'fixtures', 'uvm-blocks')
ARCH = os.path.join('yaml', 'uvmBlocks.yaml')
CHILD_ARCH = os.path.join('child', 'yaml', 'ubChild.yaml')
CHILD_ROOT_ARCH = os.path.join('yaml', 'uvmBlocksChild.yaml')
ROOT_PROJECT = os.path.join('prj', 'yaml', 'uvmBlocksProject.yaml')
CHILD_ROOT_PROJECT = os.path.join('prj', 'yaml', 'uvmBlocksChildProject.yaml')

WHERE = "Block 'ubDut' (file ../../yaml/uvmBlocks.yaml) declares hasUvm: true"
CHILD_WHERE = "Block 'ubChildDut' (file ../../child/yaml/ubChild.yaml) declares hasUvm: true"

# (name, project file, [(yaml file, edits)], required substrings)
REJECTED = [
    ('hasUvm without hasVl', ROOT_PROJECT,
     [(ARCH, [('        hasVl: true\n        hasUvm: true\n',
       '        hasVl: false\n        hasUvm: true\n')])],
     [WHERE, "has hasVl: false", "Set hasVl: true on 'ubDut'"]),
    ('no declared boundary', ROOT_PROJECT,
     [(ARCH, [('        ports:\n'
       '            in:  { interface: ubStream, direction: dst }\n'
       '            out: { interface: ubStream, direction: src }\n', '')])],
     [WHERE, "declares no ports:"]),
    ('port type without an agent', ROOT_PROJECT,
     [(ARCH, [('interfaceType: rdy_vld', 'interfaceType: push_ack')])],
     [WHERE, "its port 'in' has interface 'ubStream' of type 'push_ack'",
      "does not declare uvmAgent: true"]),
    ('output clock', ROOT_PROJECT,
     [(ARCH, [('        hasUvm: true\n',
       '        hasUvm: true\n'
       '        clocks:\n'
       '            clk: { default: true }\n'
       '            clkOut: { direction: output }\n'),
      ('addressGroup: top }', 'addressGroup: top, clocks: { clkOut: ~ } }')])],
     [WHERE, "has output clock 'clkOut'"]),
    ('output reset', ROOT_PROJECT,
     [(ARCH, [('        hasUvm: true\n',
       '        hasUvm: true\n'
       '        clocks:\n'
       '            clk: { default: true }\n'
       '        resets:\n'
       '            rst_n: { clock: clk, default: true }\n'
       '            rstOut_n: { clock: clk, direction: output }\n'),
      ('addressGroup: top }', 'addressGroup: top, resets: { rstOut_n: ~ } }')])],
     [WHERE, "has output reset 'rstOut_n'"]),
    ('a memoryConnections port', ROOT_PROJECT,
     [(ARCH, [('    ubWordT:', '    ubIdxT: { width: 4, desc: "Table index" }\n    ubWordT:'),
              ('    ubAddrSt:', '    ubIdxSt:\n        idx: { varType: ubIdxT, desc: "Table index" }\n    ubAddrSt:'),
              ('registers:\n',
               'memories:\n'
               '    - { memory: tbl, block: ubTb, structure: ubSt, wordLines: 16, '
               'addressStruct: ubIdxSt, ports: [port1], desc: "Table" }\n\n'
               'memoryConnections:\n'
               '    - { memory: tbl, block: ubTb, instance: uDut, port: port1 }\n\n'
               'registers:\n')])],
     [WHERE, "has port 'tbl', which the memoryConnections row giving instance 'uDut' "
             "access to memory 'tbl' creates", "A memory port has no UVM agent"]),
    ('a registerConnections port', ROOT_PROJECT,
     [(ARCH, [('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
               '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top, addressGroup: top }\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n'
               '    - { register: sinkCfg, regType: rw, block: ubSink, structure: ubSt, desc: "Sink config" }\n\n'
               'registerConnections:\n'
               '    - { register: sinkCfg, block: ubSink, instance: uDut }\n')])],
     [WHERE, "has port 'sinkCfg', which the registerConnections row giving instance 'uDut' "
             "access to register 'sinkCfg' creates", "A register connection port has no UVM agent"]),
    ('an undeclared connectionMaps port of a type without an agent', ROOT_PROJECT,
     [(ARCH, [('blocks:\n',
               '    ubSide:\n'
               '        desc: "Side channel"\n'
               '        interfaceType: push_ack\n'
               '        structures:\n'
               '            - { structure: ubSt, structureType: data_t }\n\n'
               'blocks:\n'),
              ('    ubDut:\n',
               '    ubSideSrc:\n'
               '        desc: "Side source"\n'
               '        hasMdl: true\n'
               '        hasRtl: false\n'
               '    ubCore:\n'
               '        desc: "Core"\n'
               '        hasMdl: true\n'
               '        hasRtl: true\n'
               '    ubDut:\n'),
              ('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
               '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n'
               '    uSide:   { container: ubTb, instanceType: ubSideSrc, instGroup: top }\n'
               '    uCore:   { container: ubDut, instanceType: ubCore,  instGroup: top }\n'),
              ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
               '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
               '    - { interface: ubSide, src: uSide, srcport: side, dst: uDut, dstport: side, name: sideLink }\n\n'
               'connectionMaps:\n'
               '    - { interface: ubStream, block: ubDut, port: in, direction: dst, instance: uCore, instancePort: in }\n'
               '    - { interface: ubStream, block: ubDut, port: out, direction: src, instance: uCore, instancePort: out }\n'
               '    - { interface: ubSide, block: ubDut, port: side, direction: dst, instance: uCore, instancePort: side }\n')])],
     [WHERE, "its port 'side' has interface 'ubSide' of type 'push_ack'",
      "does not declare uvmAgent: true"]),
    ('a block module named like the UVM testbench', ROOT_PROJECT,
     [(ARCH, [('    ubDut:\n',
               '    ubDut_uvm_tb:\n'
               '        desc: "Block named like the UVM testbench of ubDut"\n'
               '        hasMdl: true\n'
               '        hasRtl: true\n'
               '    ubDut:\n')])],
     ["ubDut_uvm_tb", "the default UVM testbench of block 'ubDut'",
      "block 'ubDut_uvm_tb'"]),
    ('only variants another project declares', CHILD_ROOT_PROJECT,
     [(CHILD_ARCH,
       [('types:\n',
         'ipParameters:\n'
         '    constants:\n'
         '        UB_W: { value: 8, maxValue: 16, desc: "Width knob" }\n\n'
         'types:\n'),
        ('        hasUvm: true\n', '        hasUvm: true\n        params: [UB_W]\n')]),
      (CHILD_ROOT_ARCH,
       [('instanceType: ubChildDut,  instGroup: top }',
         'instanceType: ubChildDut,  instGroup: top, variant: v0 }'),
        ('connections:\n',
         'parameters:\n    ubChildDut:\n        v0: { UB_W: 8 }\n\nconnections:\n')])],
     [CHILD_WHERE, "has no standalone variant, so it would get no UVM testbench top",
      "Declare a variant of 'ubChildDut' under parameters: in its own project"]),
]

ACCEPTED = [
    ('rdy_vld ports and an apb register bus', ROOT_PROJECT),
    ('a child-owned block with rdy_vld ports', CHILD_ROOT_PROJECT),
]


def make_db(project, projectYaml):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           f'A2C_PRJ_YAML={os.path.join(project, projectYaml)}', 'db']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                            env=env)
    return result.returncode, result.stdout + result.stderr


def edit_yaml(project, relative, edits):
    path = os.path.join(project, relative)
    with open(path) as f:
        text = f.read()
    for old, new in edits:
        if old not in text:
            raise RuntimeError(f"fixture no longer carries the anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def check_rejected(project, name, projectYaml, fileEdits, required):
    shutil.copytree(FIXTURE, project)
    for yamlFile, edits in fileEdits:
        edit_yaml(project, yamlFile, edits)
    rc, output = make_db(project, projectYaml)
    if rc == 0:
        print(f"  FAIL: {name}: make db accepted the block")
        return False
    if 'Traceback (most recent call last)' in output:
        print(f"  FAIL: {name}: got a Python stack trace instead of a clean rejection")
        print(output)
        return False
    missing = [s for s in required if s not in output]
    if missing:
        print(f"  FAIL: {name}: diagnostic missing substrings: {missing}")
        print(output)
        return False
    print(f"  PASS: {name} is rejected")
    return True


def check_accepted(project, name, projectYaml):
    shutil.copytree(FIXTURE, project)
    rc, output = make_db(project, projectYaml)
    if rc != 0:
        print(f"  FAIL: {name}: make db rejected the block (rc={rc})")
        print(output)
        return False
    print(f"  PASS: {name} is accepted")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='uvm_blocks_', dir=test_dir)
    ok = True
    try:
        for index, (name, projectYaml) in enumerate(ACCEPTED):
            ok = check_accepted(os.path.join(tmp, f'accept{index}'), name, projectYaml) and ok
        for index, (name, projectYaml, fileEdits, required) in enumerate(REJECTED):
            ok = check_rejected(os.path.join(tmp, f'reject{index}'), name, projectYaml,
                                fileEdits, required) and ok
    finally:
        remove_tree(tmp)
    if ok:
        print("\nPASS: hasUvm blocks the UVM testbench cannot drive are rejected at db")
        return 0
    print("\nFAIL: a hasUvm validation rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
