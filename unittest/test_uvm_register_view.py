#!/usr/bin/env python3
"""The UVM view gives each port its clock domain and backpressure, and the
register model its rows, at every variant.

The generated environment picks each agent's clock interface and its
backpressure setting from the port entries, and builds the register model from
the registers and memories entries. A register model whose offsets or fields
disagree with the RTL decoder reads the wrong bits. Each offset must be the
one fw/<block>RegAddresses.h defines and the address map allocates, each memory
must step by the decoder's row stride, and each field must sit at its packed
position: the first declared member is the most significant, as in an SV
`typedef struct packed`. A padding member that alignment adds is marked
reserved. A parameter can size a field or a memory depth, so widths and depths
are checked at each variant.

A copy of `fixtures/uvm-blocks` gains params UB_W and UB_D on ubDut and two
variants that bind them differently. ubDut gets a register whose low field is
UB_W wide, a 40-bit register, a register over a specialStructures entry whose
second member is aligned to bit 16, a regType memory register, a memory UB_D
deep with regAccess: ro, and one without regAccess, which the view leaves out.
The expected values, offsets included, are worked out here from the edited YAML
and the fixture's address policy: memories first, sized by their worst-case
rows, then registers in 8-byte slots.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree
from pysrc.processYaml import projectOpen


FIXTURE = os.path.join(test_dir, 'fixtures', 'uvm-blocks')
ARCH = os.path.join('yaml', 'uvmBlocks.yaml')
PROJECT = os.path.join('prj', 'yaml', 'uvmBlocksProject.yaml')
DB = 'uvmBlocks.db'

EDITS = [
    ('\ntypes:\n',
     '\nipParameters:\n'
     '    constants:\n'
     '        UB_W: { value: 4, maxValue: 16, desc: "Field width knob" }\n'
     '        UB_D: { value: 16, maxValue: 64, desc: "Memory depth knob" }\n\n'
     'types:\n'
     '    ubPT: { width: UB_W, desc: "Parameter-width field" }\n'
     '    ubIdxT: { width: 6, desc: "Table index" }\n'),
    ('\nstructures:\n',
     '\nstructures:\n'
     '    ubPSt:\n'
     '        hi: { varType: ubDataT, desc: "Fixed high field" }\n'
     '        lo: { varType: ubPT, desc: "Parameter-width low field" }\n'
     '    ubWideSt:\n'
     '        word: { varType: ubWordT, desc: "Low word" }\n'
     '        tag: { varType: ubDataT, desc: "Tag above the word" }\n'
     '    ubIdxSt:\n'
     '        idx: { varType: ubIdxT, desc: "Table index" }\n'
     '    ubAlignBaseSt:\n'
     '        a: { varType: ubDataT, desc: "First member" }\n'
     '        b: { varType: ubDataT, align: 16, desc: "Member aligned to bit 16" }\n'),
    ('\ninterfaces:\n',
     '\nspecialStructures:\n'
     '    ubAlignSt: { baseStruct: ubAlignBaseSt }\n\n'
     'interfaces:\n'),
    ('        hasUvm: true\n', '        hasUvm: true\n        params: [UB_W, UB_D]\n'),
    ('instanceType: ubDut,    instGroup: top, addressGroup: top }',
     'instanceType: ubDut,    instGroup: top, addressGroup: top, variant: v0 }'),
    ('\nconnections:\n',
     '\nparameters:\n'
     '    ubDut:\n'
     '        v0: { UB_W: 4, UB_D: 16 }\n'
     '        v1: { UB_W: 12, UB_D: 32 }\n\n'
     'connections:\n'),
    ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
     '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n'
     '    - { register: cfg, regType: rw, block: ubDut, structure: ubPSt, defaultValue: 5, desc: "Config" }\n'
     '    - { register: wide, regType: ro, block: ubDut, structure: ubWideSt, desc: "Wide status" }\n'
     '    - { register: aligned, regType: rw, block: ubDut, structure: ubAlignSt, desc: "Padded" }\n'
     '    - { register: lut, regType: memory, block: ubDut, structure: ubSt, addressStruct: ubIdxSt, '
     'wordLines: 8, desc: "Register memory" }\n\n'
     'memories:\n'
     '    - { memory: tbl, block: ubDut, structure: ubPSt, wordLines: UB_D, addressStruct: ubIdxSt, '
     'regAccess: ro, desc: "Table" }\n'
     '    - { memory: hidden, block: ubDut, structure: ubSt, wordLines: 4, addressStruct: ubIdxSt, '
     'desc: "Not on the bus" }\n'),
]

PKG = {'v0': 'ubDut_v0_uvm_pkg', 'v1': 'ubDut_v1_uvm_pkg'}
FILE_PKG = 'uvmBlocks_package'
UB_W = {'v0': 4, 'v1': 12}
UB_D = {'v0': 16, 'v1': 32}

PORTS = [
    {'name': 'in', 'interfaceType': 'rdy_vld', 'role': 'dst', 'clock': 'clk', 'reset': 'rst_n', 'backpressure': True},
    {'name': 'out', 'interfaceType': 'rdy_vld', 'role': 'src', 'clock': 'clk', 'reset': 'rst_n', 'backpressure': True},
    {'name': 'ubRegs', 'interfaceType': 'apb', 'role': 'dst', 'clock': 'clk', 'reset': 'rst_n', 'backpressure': True},
]


def each(value):
    return {variant: value(variant) for variant in PKG}


def field(name, width, lsb, reserved=False):
    return {'name': name, 'width': width, 'reserved': reserved, 'lsb': lsb}


def expected_registers():
    return [
        {'name': 'ctrl', 'offset': 0x120, 'bytes': 1, 'regType': 'rw', 'defaultValue': 0,
         'type': each(lambda v: {'name': 'ubSt', 'pkg': FILE_PKG}),
         'fields': each(lambda v: [field('data', 8, 0)])},
        {'name': 'cfg', 'offset': 0x128, 'bytes': 2, 'regType': 'rw', 'defaultValue': 5,
         'type': each(lambda v: {'name': 'ubPSt', 'pkg': PKG[v]}),
         'fields': each(lambda v: [field('hi', 8, UB_W[v]), field('lo', UB_W[v], 0)])},
        {'name': 'wide', 'offset': 0x130, 'bytes': 5, 'regType': 'ro', 'defaultValue': 0,
         'type': each(lambda v: {'name': 'ubWideSt', 'pkg': FILE_PKG}),
         'fields': each(lambda v: [field('word', 32, 8), field('tag', 8, 0)])},
        {'name': 'aligned', 'offset': 0x138, 'bytes': 3, 'regType': 'rw', 'defaultValue': 0,
         'type': each(lambda v: {'name': 'ubAlignSt', 'pkg': FILE_PKG}),
         'fields': each(lambda v: [field('a', 8, 16), field('reserved0', 8, 8, True), field('b', 8, 0)])},
    ]


def expected_memories():
    # tbl's worst-case row is 8 + 16 bits, so 4 bytes, and its 64 worst-case
    # rows fill 0x0-0xff; lut follows at 0x100 with 8 rows of 4 bytes.
    return [
        {'name': 'lut', 'offset': 0x100, 'rowBytes': 4, 'access': 'rw',
         'count': each(lambda v: 8), 'width': each(lambda v: 8),
         'type': each(lambda v: {'name': 'ubSt', 'pkg': FILE_PKG})},
        {'name': 'tbl', 'offset': 0x0, 'rowBytes': 4, 'access': 'ro',
         'count': each(lambda v: UB_D[v]), 'width': each(lambda v: 8 + UB_W[v]),
         'type': each(lambda v: {'name': 'ubPSt', 'pkg': PKG[v]})},
    ]


def make_db(project):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           f'A2C_PRJ_YAML={os.path.join(project, PROJECT)}', 'db']
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)


def edit_fixture(project):
    path = os.path.join(project, ARCH)
    with open(path) as f:
        text = f.read()
    for old, new in EDITS:
        if text.count(old) != 1:
            raise RuntimeError(f"fixture no longer carries the single anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def reg_addresses(prj):
    """The REG_UBDUT_* defines fw/<block>RegAddresses.h would carry, read
    through the includes template the header is rendered by."""
    from templates.systemc.includes import includeRegAddresses
    text = includeRegAddresses(None, prj, None)
    return {m.group(1).lower(): int(m.group(2), 16)
            for m in re.finditer(r'#define REG_UBDUT_(\w+)\s+0x([0-9a-f]+)', text)}


def compare(what, actual, expected):
    if actual == expected:
        return []
    return [f"{what} is\n    {actual}\n  expected\n    {expected}"]


def check(project):
    prj = projectOpen(os.path.join(project, DB))
    (qualBlock,) = [key for key, row in prj.data['blocks'].items() if row['block'] == 'ubDut']
    uvm = prj.getBlockData(qualBlock)['uvm']
    problems = []
    keys = ('name', 'interfaceType', 'role', 'clock', 'reset', 'backpressure')
    problems += compare('ports', [{k: port[k] for k in keys} for port in uvm['ports']], PORTS)

    offsets = reg_addresses(prj)
    for row in uvm['registers'] + uvm['memories']:
        if row['offset'] != offsets.get(row['name'].lower()):
            problems.append(f"{row['name']} is at offset {row['offset']:#x}, the firmware header "
                            f"says {offsets.get(row['name'].lower())}")
    problems += compare('registers', uvm['registers'], expected_registers())
    problems += compare('memories', uvm['memories'], expected_memories())
    if 'hidden' in offsets or any(mem['name'] == 'hidden' for mem in uvm['memories']):
        problems.append("the memory without regAccess reached the firmware header or the view")
    return problems


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='uvm_register_view_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'prj')
        shutil.copytree(FIXTURE, project)
        edit_fixture(project)
        result = make_db(project)
        if result.returncode != 0:
            print(f"FAIL: make db rejected the fixture (rc={result.returncode})")
            print(result.stdout + result.stderr)
            return 1
        problems = check(project)
    finally:
        remove_tree(tmp)
    if problems:
        for problem in problems:
            print(f"  FAIL: {problem}")
        print("\nFAIL: the UVM view disagrees with the block's ports or address rows")
        return 1
    print("  PASS: ports carry their clock, reset and backpressure")
    print("  PASS: registers and memories sit at the allocated offsets and strides, with the packed fields at v0 and v1")
    print("\nPASS: the UVM view carries port domains and the register model")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
