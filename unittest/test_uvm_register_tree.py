#!/usr/bin/env python3
"""A hasUvm block that owns no registers gets a register model of the
instances its register bus reaches, one level per instance.

When the block hosts a router or passes its register bus through to one
consumer, the registers live in other blocks. `make db` walks from the block
down through each router's slots and each passthrough container's consumer,
and persists that tree in the block's testbench tops. The register model
builds one uvm_reg_block per node and adds each node's map to its parent's at
the node's offset, so a node's absolute address is the sum of the add_submap
offsets on its path. A wrong offset or a passthrough consumer away from offset
0 puts every register behind it at the wrong address; slot order only orders
the generated members and lines.

Slots follow the router's address IDs, so an instance with addressMultiples:
2 leaves the next slot empty. Each instance's rows resolve at that instance's
own variant: one leaf block instanced at two variants has two field widths and
two memory depths. A memory's stride stays the decoder's worst-case row
stride, whatever the variant. The walk takes slots from the host's own
instances only, so an instance carrying the same address group in a container
nothing instantiates never enters the tree.

The fixture is a copy of `fixtures/uvm-blocks`. ubDut loses its own register,
hosts the router uDutRouter (group dut, 0x1000 per slot) and four slots: uA and
uB, one ubLeaf block at variants v0 and v1, uB taking two slots; uBridge, a
nested router host whose router (group bridge, 0x100 per slot) serves uDeep0
and uDeep1; and uWrap, a passthrough container holding uInner. ubSpare, which
nothing instantiates, holds uSpareA in group dut. ubLeaf's cfg register and tbl
memory are UB_W plus 8 bits wide, 48 at worst, so tbl's stride is 8 bytes at
every variant. A second copy makes ubDut a router-less passthrough top whose
one consumer, uInner, owns ctrl, and the tree holds uInner at offset 0.

The model drives the top's registerPorts: bus. Two more copies drop it and
feed ubDut through a connectionMap from its boundary port busIn onto
uDutRouter, and the model drives busIn. One map row gives only name:, as
design-register-decode authors the feed, so the router's upstream port takes
the name busIn; the other names the router's port ubRegs with instancePort:.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import close_db, remove_tree
from pysrc.processYaml import projectOpen


FIXTURE = os.path.join(test_dir, 'fixtures', 'uvm-blocks')
ARCH = os.path.join('yaml', 'uvmBlocks.yaml')
PROJECT = os.path.join('prj', 'yaml', 'uvmBlocksProject.yaml')
DB = 'uvmBlocks.db'


def leaf(name, desc):
    return (f'    {name}:\n'
            f'        desc: "{desc}"\n'
            '        hasMdl: true\n'
            '        hasTb: false\n'
            '        hasRtl: true\n'
            '        hasVl: false\n')


def router(name, group, increment, spaces):
    return (leaf(name, f"Register decoder of group {group}")
            + '        addressBlock:\n'
            f'            addressGroup: {group}\n'
            f'            addressIncrement: {increment}\n'
            f'            maxAddressSpaces: {spaces}\n'
            f'            varType: addr_id_ub_{group}\n'
            f'            enumPrefix: ADDR_ID_UB_{group.upper()}_\n'
            '            upstreamPort: ubRegs\n'
            '            registerDecoderPort: ubRegs\n')


EDITS = [
    ('\ntypes:\n',
     '\nipParameters:\n'
     '    constants:\n'
     '        UB_W: { value: 4, maxValue: 40, desc: "Field width knob" }\n'
     '        UB_D: { value: 16, maxValue: 64, desc: "Memory depth knob" }\n\n'
     'types:\n'
     '    ubPT: { width: UB_W, desc: "Parameter-width field" }\n'
     '    ubIdxT: { width: 6, desc: "Table index" }\n'),
    ('\nstructures:\n',
     '\nstructures:\n'
     '    ubPSt:\n'
     '        hi: { varType: ubDataT, desc: "Fixed high field" }\n'
     '        lo: { varType: ubPT, desc: "Parameter-width low field" }\n'
     '    ubIdxSt:\n'
     '        idx: { varType: ubIdxT, desc: "Table index" }\n'),
    ('        registerPorts:\n            ubRegs: { interface: ubRegs }\n',
     '        registerPorts:\n            ubRegs: { interface: ubRegs }\n'
     + router('ubDutRouter', 'dut', '0x1000', 8)
     + leaf('ubLeaf', "Leaf at two variants") + '        params: [UB_W, UB_D]\n'
     + leaf('ubBridge', "Nested router host")
     + router('ubBridgeRouter', 'bridge', '0x100', 4)
     + leaf('ubDeep', "Leaf behind the nested router")
     + leaf('ubWrap', "Passthrough container")
     + leaf('ubInner', "Leaf inside the passthrough")
     + leaf('ubSpare', "Container nothing instantiates")),
    ('    uRouter: { container: ubTb, instanceType: ubRouter, instGroup: top }\n',
     '    uRouter: { container: ubTb, instanceType: ubRouter, instGroup: top }\n'
     '    uDutRouter: { container: ubDut, instanceType: ubDutRouter }\n'
     '    uA: { container: ubDut, instanceType: ubLeaf, addressGroup: dut, variant: v0 }\n'
     '    uB: { container: ubDut, instanceType: ubLeaf, addressGroup: dut, variant: v1, addressMultiples: 2 }\n'
     '    uBridge: { container: ubDut, instanceType: ubBridge, addressGroup: dut }\n'
     '    uWrap: { container: ubDut, instanceType: ubWrap, addressGroup: dut }\n'
     '    uBridgeRouter: { container: ubBridge, instanceType: ubBridgeRouter }\n'
     '    uDeep0: { container: ubBridge, instanceType: ubDeep, addressGroup: bridge }\n'
     '    uDeep1: { container: ubBridge, instanceType: ubDeep, addressGroup: bridge }\n'
     '    uInner: { container: ubWrap, instanceType: ubInner }\n'
     '    uSpareA: { container: ubSpare, instanceType: ubLeaf, addressGroup: dut, variant: v1 }\n\n'
     'parameters:\n'
     '    ubLeaf:\n'
     '        v0: { UB_W: 4, UB_D: 16 }\n'
     '        v1: { UB_W: 12, UB_D: 32 }\n'),
    ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
     '    - { register: cfg, regType: rw, block: ubLeaf, structure: ubPSt, defaultValue: 5, desc: "Config" }\n'
     '    - { register: stat, regType: ro, block: ubDeep, structure: ubSt, desc: "Status" }\n'
     '    - { register: ctrl, regType: rw, block: ubInner, structure: ubSt, desc: "Control" }\n\n'
     'memories:\n'
     '    - { memory: tbl, block: ubLeaf, structure: ubPSt, wordLines: UB_D, addressStruct: ubIdxSt, '
     'regAccess: ro, desc: "Table" }\n'),
]

# ubDut with no router passes its register bus to its one consumer, uInner.
PASSTHROUGH_EDITS = [
    ('        registerPorts:\n            ubRegs: { interface: ubRegs }\n',
     '        registerPorts:\n            ubRegs: { interface: ubRegs }\n'
     + leaf('ubInner', "Leaf inside the passthrough top")),
    ('    uRouter: { container: ubTb, instanceType: ubRouter, instGroup: top }\n',
     '    uRouter: { container: ubTb, instanceType: ubRouter, instGroup: top }\n'
     '    uInner: { container: ubDut, instanceType: ubInner }\n'),
    ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
     '    - { register: ctrl, regType: rw, block: ubInner, structure: ubSt, desc: "Control" }\n'),
]

# ubDut takes its register bus as busIn, mapped onto its router's upstream
# port, in place of registerPorts: and the testbench's own router. The map row
# gives only name:, so the router's port is busIn too.
CONNECTION_MAP_EDITS = [
    ('        registerPorts:\n            ubRegs: { interface: ubRegs }\n    ubDutRouter:\n',
     '    ubDutRouter:\n'),
    ('instanceType: ubDut,    instGroup: top, addressGroup: top }', 'instanceType: ubDut,    instGroup: top }'),
    ('    uRouter: { container: ubTb, instanceType: ubRouter, instGroup: top }\n', ''),
    ('            addressGroup: top\n            addressIncrement: 0x00010000\n'
     '            maxAddressSpaces: 16\n            varType: addr_id_ub\n            enumPrefix: ADDR_ID_UB_\n'
     '            upstreamPort: ubRegs\n            registerDecoderPort: ubRegs\n', ''),
    ('        addressBlock:\n    ubDut:\n', '    ubDut:\n'),
    ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
     '    - { interface: ubRegs, src: uCpu, dst: uDut, dstport: busIn }\n\n'
     'connectionMaps:\n'
     '    - { interface: ubRegs, block: ubDut, direction: dst, instance: uDutRouter, name: busIn }\n'),
]

# The same feed with the router's port named ubRegs.
INSTANCE_PORT_EDITS = [
    ('instance: uDutRouter, name: busIn }', 'instance: uDutRouter, instancePort: ubRegs, name: busIn }'),
]

UB_W = {'v0': 4, 'v1': 12}
UB_D = {'v0': 16, 'v1': 32}


def leaf_rows(variant):
    return {'cfg': ([8, UB_W[variant]], None), 'tbl': ([8, UB_W[variant]], UB_D[variant])}


# (path, block, variant, offset in its parent, rows or None) in depth-first
# order. rows maps each row name to its field widths and depth.
EXPECTED = [
    (('uA',), 'ubLeaf', 'v0', 0x0, leaf_rows('v0')),
    (('uB',), 'ubLeaf', 'v1', 0x1000, leaf_rows('v1')),
    (('uBridge',), 'ubBridge', '', 0x3000, None),
    (('uBridge', 'uDeep0'), 'ubDeep', '', 0x0, {'stat': ([8], None)}),
    (('uBridge', 'uDeep1'), 'ubDeep', '', 0x100, {'stat': ([8], None)}),
    (('uWrap',), 'ubWrap', '', 0x4000, None),
    (('uWrap', 'uInner'), 'ubInner', '', 0x0, {'ctrl': ([8], None)}),
]

# Each instance's absolute address in the root map.
EXPECTED_ADDRESSES = {
    ('uA',): 0x0, ('uB',): 0x1000, ('uBridge',): 0x3000, ('uBridge', 'uDeep0'): 0x3000,
    ('uBridge', 'uDeep1'): 0x3100, ('uWrap',): 0x4000, ('uWrap', 'uInner'): 0x4000,
}


def make(project, target):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-j8', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           f'A2C_PRJ_YAML={os.path.join(project, PROJECT)}', target]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)


def edit_fixture(project, edits):
    path = os.path.join(project, ARCH)
    with open(path) as f:
        text = f.read()
    for old, new in edits:
        if text.count(old) != 1:
            raise RuntimeError(f"fixture no longer carries the single anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def flatten(node, prj):
    rows = None
    if node['registerWidths']:
        rows = dict()
        for section, nameField in (('registers', 'register'), ('memories', 'memory')):
            for key, entry in node['registerWidths'][section].items():
                rows[prj.data[section][key][nameField]] = ([f['width'] for f in entry['fields']], entry['wordLines'])
    out = [(node['path'], node['block'], node['variant'], node['offset'], rows)] if node['path'] else []
    for child in node['children']:
        out += flatten(child, prj)
    return out


def addresses(uvm):
    """Each instance path's address in the root map, as the sum of the
    add_submap offsets the generated register blocks use on its path."""
    blocks = {block['className']: block for block in uvm['registerBlocks']}
    (root,) = [block for block in uvm['registerBlocks'] if block['isRoot']]
    out = dict()

    def visit(block, path, base):
        for child in block['children']:
            childPath = path + (child['name'],)
            out[childPath] = base + child['offset']
            visit(blocks[child['className']], childPath, out[childPath])
    visit(root, (), 0)
    return out


def check(project, busPort):
    prj = projectOpen(os.path.join(project, DB))
    (qualBlock,) = [key for key, row in prj.data['blocks'].items() if row['block'] == 'ubDut']
    tops = prj.uvmNames[qualBlock]['tops']
    problems = []
    if list(tops) != ['']:
        return [f"ubDut has testbench tops {list(tops)}, expected one variantless top"]
    tree = tops['']['registerTree']
    if tree is None:
        return ["ubDut, which owns no registers, has no register tree"]
    actual = flatten(tree, prj)
    if actual != EXPECTED:
        problems.append("the register tree is\n    " + "\n    ".join(map(str, actual))
                        + "\n  expected\n    " + "\n    ".join(map(str, EXPECTED)))
    if any('uSpareA' in node[0] for node in actual):
        problems.append("uSpareA, in a container nothing instantiates, entered the tree")
    if prj.uvmNames[qualBlock]['registerTreeBusPort'] != busPort:
        return problems + [f"make db chose bus port {prj.uvmNames[qualBlock]['registerTreeBusPort']!r} for the "
                           f"register tree, expected {busPort!r}"]
    uvm = prj.getBlockData(qualBlock)['uvm']
    if addresses(uvm) != EXPECTED_ADDRESSES:
        problems.append(f"the register blocks' submaps put the instances at {addresses(uvm)}, "
                        f"expected {EXPECTED_ADDRESSES}")
    if uvm['registerBus'] is None or uvm['registerBus']['port'] != busPort:
        problems.append(f"the register bus is {uvm['registerBus']}, expected port {busPort}")
    strides = {(block['className'], mem['name']): mem['rowBytes']
               for block in uvm['registerBlocks'] for mem in block['memories']}
    want = {('ubDut_uA_reg_block', 'tbl'): 8, ('ubDut_uB_reg_block', 'tbl'): 8}
    if strides != want:
        problems.append(f"the memories' strides are {strides}, expected the worst-case {want}")
    return problems


def check_passthrough(project):
    prj = projectOpen(os.path.join(project, DB))
    (qualBlock,) = [key for key, row in prj.data['blocks'].items() if row['block'] == 'ubDut']
    tree = prj.uvmNames[qualBlock]['tops']['']['registerTree']
    if tree is None:
        return ["ubDut, a passthrough top, has no register tree"]
    actual = flatten(tree, prj)
    want = [(('uInner',), 'ubInner', '', 0x0, {'ctrl': ([8], None)})]
    if actual != want:
        return [f"the passthrough top's register tree is {actual}, expected {want}"]
    uvm = prj.getBlockData(qualBlock)['uvm']
    if addresses(uvm) != {('uInner',): 0x0}:
        return [f"the passthrough top's submaps put the instances at {addresses(uvm)}, expected uInner at 0x0"]
    if uvm['registerBus'] is None or uvm['registerBus']['port'] != 'ubRegs':
        return [f"the passthrough top's register bus is {uvm['registerBus']}, expected port ubRegs"]
    return []


def run_all_tests():
    print("\n" + "=" * 70)
    print("UVM REGISTER TREE OF A ROUTED TOP")
    print("=" * 70)
    tmp = tempfile.mkdtemp(prefix='uvm_register_tree_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'prj')
        shutil.copytree(FIXTURE, project)
        edit_fixture(project, EDITS)
        result = make(project, 'db')
        if result.returncode != 0:
            print(f"FAIL: make db rejected the fixture (rc={result.returncode})")
            print(result.stdout + result.stderr)
            return 1
        problems = check(project, 'ubRegs')
        close_db()
        for name, edits in (('connectionMap', CONNECTION_MAP_EDITS),
                            ('connectionMapInstancePort', CONNECTION_MAP_EDITS + INSTANCE_PORT_EDITS)):
            project = os.path.join(tmp, name)
            shutil.copytree(FIXTURE, project)
            edit_fixture(project, EDITS + edits)
            result = make(project, 'db')
            if result.returncode != 0:
                print(f"FAIL: make db rejected the {name} fixture (rc={result.returncode})")
                print(result.stdout + result.stderr)
                return 1
            problems += check(project, 'busIn')
            close_db()
        project = os.path.join(tmp, 'passthrough')
        shutil.copytree(FIXTURE, project)
        edit_fixture(project, PASSTHROUGH_EDITS)
        result = make(project, 'db')
        if result.returncode != 0:
            print(f"FAIL: make db rejected the passthrough fixture (rc={result.returncode})")
            print(result.stdout + result.stderr)
            return 1
        problems += check_passthrough(project)
    finally:
        remove_tree(tmp)
    if problems:
        for problem in problems:
            print(f"  FAIL: {problem}")
        print("\nFAIL: the register tree disagrees with the design's routed instances")
        return 1
    print("  PASS: slots in address-ID order at their offsets, addressMultiples: 2 leaving a slot empty")
    print("  PASS: each instance at the sum of the add_submap offsets on its path, a passthrough consumer at offset 0")
    print("  PASS: each instance's widths and depths at its own variant, strides at the worst case")
    print("  PASS: an instance outside the host never enters the tree")
    print("  PASS: a router-less passthrough top holds its consumer at offset 0 on its registerPorts: bus")
    print("  PASS: a top fed through a connectionMap onto its router drives the mapped boundary port, "
          "with and without instancePort:")
    print("\nPASS: a routed top's register tree mirrors its instance hierarchy")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
