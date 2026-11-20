#!/usr/bin/env python3
"""A composed root reuses each hasUvm child's variant package, and its env
watches the RTL's connections between its children (SIMULATOR_INTEGRATION.md
section 9.15).

deriveUvmReuse walks each UVM top's instance tree with each instance's
parameter values. An instance reuses the standalone variant of its block whose
values equal its own: a variant the parent declares with equal values reuses
that standalone variant, and one with values no standalone variant has reuses
nothing and prints an info line. A block without params has one variantless
package, and an instance naming no variant takes its block's default values.
A child's own reuse precedes it, two instances at one variant give one entry,
and every top of a block compiles the union of all its tops' lists.

A reused instance in the register tree is named by the child package's
register block class, emits no class of its own for anything below it, and
keeps its offset. A memory below it still makes its parent's map an
a2c_reg_map.

An internal monitor is a passive agent on the RTL's own interface instance,
which a variant top reaches through u_wrapper. It samples on the connection's
clock: clock:, else the clock the source instance binds to its source port's
domain. A payload local to the module, a clock that is not a clock port of
the block, or a boundary port's name keeps a connection unwatched, with the
reason. Its transfers are not progress for the joint stall rule.

The end-to-end part copies examples/uvmReuse, whose chain holds the child
project's leaf twice: uLeafA at w8, and uLeafB bound to the chain's width, so
w8 in v8 and w4 in v4. It checks the persisted reuse lists, the register
model's agreement across variants, the internal monitors, the manifest's
A2C_UVM_REUSED_SV_<top>, and that make db stops on a reused package file the
child has not generated.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import close_db, remove_tree
import pysrc.intf_gen_utils as intf_gen_utils
import pysrc.processYaml as processYaml
from pysrc.processYaml import projectCreate, projectOpen
from templates.systemVerilog import uvmPkg


EXAMPLE = os.path.join(base_dir, 'examples', 'uvmReuse')


class FakeConfig:
    def __init__(self, values):
        self.values = values

    def getConfig(self, key):
        return self.values[key]

    def setConfig(self, key, value, bin=False):
        self.values[key] = value


def descriptor(variant, values, isForeign=False, containerSourced=None):
    return {'variant': variant, 'values': values, 'isForeign': isForeign,
            'containerSourced': containerSourced or {}, 'declaringProject': 'prj'}


def instance(key, container, block, variant=''):
    return {'instanceKey': key, 'instance': key, 'containerKey': container, 'instanceTypeKey': block,
            'variant': variant, 'inheritContainerParam': False}


def reuse_model():
    """P (variants a: W=1, b: W=4) holds:
    i1  L at x, W=1: equal values
    i2  L bound to P's W: x in a, w in b, so w only from b
    i3  L at odd, W=9, declared by P: no standalone variant
    i4  N, a block without params
    i5  L naming no variant: L's default W=2, so y
    i6  M, without params, holding m1, L at z (W=3): nesting
    i7  L at same, declared by P with W=3: equal to z
    """
    L = [descriptor('x', {'W': 1}), descriptor('y', {'W': 2}), descriptor('z', {'W': 3}), descriptor('w', {'W': 4}),
         descriptor('fromP', {'W': 0}, isForeign=True, containerSourced={'W': 'W'}),
         descriptor('odd', {'W': 9}, isForeign=True), descriptor('same', {'W': 3}, isForeign=True)]
    instances = [instance('i1', 'P', 'L', 'x'), instance('i2', 'P', 'L', 'fromP'), instance('i3', 'P', 'L', 'odd'),
                 instance('i4', 'P', 'N'), instance('i5', 'P', 'L'), instance('i6', 'P', 'M'),
                 instance('m1', 'M', 'L', 'z'), instance('i7', 'P', 'L', 'same')]
    fake = projectCreate.__new__(projectCreate)
    fake.config = FakeConfig({
        'VARIANTCONFIGDESCRIPTORS': {'P': [descriptor('a', {'W': 1}), descriptor('b', {'W': 4})], 'L': L},
        'DEFAULTCONFIGDESCRIPTORS': {'P': {'values': {'W': 1}}, 'L': {'values': {'W': 2}}},
        'INSTANCEVARIANTDECLARERS': {inst['instanceKey']: 'prj' for inst in instances},
        'VARIANTSOURCEBLOCKS': {'P': ['P'], 'L': ['L'], 'N': ['N'], 'M': ['M']},
    })
    fake.config.values['VARIANTCONFIGDESCRIPTORS'].update({'N': [], 'M': []})
    fake.flatData = {
        'blocks': {key: {'block': key, 'hasUvm': True} for key in ('P', 'L', 'N', 'M')},
        'blocksparams': {0: {'blockKey': 'P', 'param': 'W'}, 1: {'blockKey': 'L', 'param': 'W'}},
        'instances': {inst['instanceKey']: inst for inst in instances},
    }

    def tops(block, variants):
        return {'tops': {v: {'stem': f"{block}_{v}" if v else block, 'pkgName': f"{block}_{v}_uvm_pkg" if v
                             else f"{block}_uvm_pkg", 'reuse': []} for v in variants}}
    fake.uvmNames = {'P': tops('P', ['a', 'b']), 'L': tops('L', ['w', 'x', 'y', 'z']),
                     'N': tops('N', ['']), 'M': tops('M', [''])}
    return fake


def check_derive_reuse():
    fake = reuse_model()
    import io
    import contextlib
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        projectCreate.deriveUvmReuse(fake)
    problems = []
    want = [('L', 'x'), ('N', ''), ('L', 'y'), ('L', 'z'), ('M', ''), ('L', 'w')]
    for variant, top in fake.uvmNames['P']['tops'].items():
        got = [(entry['blockKey'], entry['variant']) for entry in top['reuse']]
        if got != want:
            problems.append(f"P's top {variant} reuses {got}, expected {want}: equal values match, a parent's "
                            f"variant with unmatched values does not, a block without params reuses '', an "
                            f"instance naming no variant takes its default, a child precedes its container, "
                            f"each (block, variant) once, and every top the union")
    if [(e['blockKey'], e['variant']) for e in fake.uvmNames['M']['tops']['']['reuse']] != [('L', 'z')]:
        problems.append(f"M reuses {fake.uvmNames['M']['tops']['']['reuse']}, expected L at z")
    pkg = [e['pkgName'] for e in fake.uvmNames['P']['tops']['a']['reuse']]
    if pkg[0] != 'L_x_uvm_pkg' or pkg[1] != 'N_uvm_pkg':
        problems.append(f"the reuse rows name packages {pkg}, expected each block's own variant package names")
    infos = [line for line in out.getvalue().splitlines() if line.startswith('Info:')]
    wantInfos = [f"Info: UVM top P_{v} reuses nothing of instance i3: its parameter values match none of L's "
                 f"standalone variants, so its library cannot be named there." for v in ('a', 'b')]
    if infos != wantInfos:
        problems.append(f"deriveUvmReuse printed {infos}, expected one info line per top for i3")
    return problems


def check_register_tree():
    """A root with a reused child, which has a memory, and a sibling of its own."""
    fake = projectOpen.__new__(projectOpen)
    fake.uvmNames = {'leafKey': {'tops': {'w8': {'pkgName': 'leaf_w8_uvm_pkg'}}, 'regBlockClass': 'leaf_reg_block'}}

    def model(blockKey, widths, prefix):
        if blockKey == 'leafKey':
            return [], [{'name': 'tbl'}]
        return [{'name': 'ctrl'}], []
    fake.getUvmRegisterModel = model

    def node(path, blockKey, reuse, children, offset=0):
        return {'path': path, 'instance': path[-1] if path else None, 'blockKey': blockKey, 'reuse': reuse,
                'registerWidths': {'registers': {}, 'memories': {}}, 'children': children, 'offset': offset}
    tree = node((), 'rootKey', None, [node(('uA',), 'leafKey', 'w8', [], 0x2000),
                                      node(('uB',), 'otherKey', None, [], 0x3000)])
    blocks = projectOpen.getUvmRegisterTree(fake, {'v': {'registerTree': tree}}, 'chain', 'chain_reg_block')
    problems = []
    names = [block['className'] for block in blocks]
    if names != ['chain_uB_reg_block', 'chain_reg_block']:
        problems.append(f"the register tree emits classes {names}, expected uB's and the root's, none for reused uA")
    root = blocks[-1]
    children = [(c['name'], c['className'], c['offset']) for c in root['children']]
    if children != [('uA', 'leaf_w8_uvm_pkg::leaf_reg_block', 0x2000), ('uB', 'chain_uB_reg_block', 0x3000)]:
        problems.append(f"the root's children are {children}, expected uA as the child package's class at its offset")
    if not root['a2cMap']:
        problems.append("the root's map is a plain uvm_reg_map, but a memory sits below reused uA")
    return problems


def check_internal_monitors():
    """Six connections: mid watched on clk, ticks on clkAux through uTick's
    clock binding, bus a register bus, raw a type without an agent, and
    three unwatched with their reasons."""
    conns = {
        'mid': {'clock': None, 'srcKey': 'uA', 'srcport': 'out', 'type': 'rdy_vld', 'param': False},
        'ticks': {'clock': None, 'srcKey': 'uTick', 'srcport': 'out', 'type': 'push_ack', 'param': False},
        'bus': {'clock': 'clk', 'type': 'apb', 'param': False},
        'raw': {'clock': 'clk', 'type': 'raw', 'param': False},
        'wide': {'clock': 'clk', 'type': 'rdy_vld', 'param': True},
        'slow': {'clock': 'clkTb', 'type': 'rdy_vld', 'param': False},
        'out': {'clock': 'clk', 'type': 'rdy_vld', 'param': False},
    }
    for name, conn in conns.items():
        conn['name'] = name
    defs = {'rdy_vld': {'uvmAgent': True, 'addressBus': False}, 'push_ack': {'uvmAgent': True, 'addressBus': False},
            'apb': {'uvmAgent': True, 'addressBus': True}, 'raw': {'uvmAgent': False, 'addressBus': False}}
    saved = (intf_gen_utils.get_intf_data, intf_gen_utils.get_intf_type, intf_gen_utils.get_channel_name)
    intf_gen_utils.get_intf_data = lambda conn, prj: {'interfaceType': conn['type'], 'structures': conn}
    intf_gen_utils.get_intf_type = lambda intfType, ret: intfType
    intf_gen_utils.get_channel_name = lambda conn: conn['name']
    try:
        fake = projectOpen.__new__(projectOpen)
        fake.data = {'instances': {'uA': {'instanceTypeKey': 'leaf'}, 'uTick': {'instanceTypeKey': 'tick'}}}
        fake.getIntfParamBindings = lambda intfDef, conn: [{'isNull': False, 'kind': 'structures',
                                                            'structureKey': conn['param']}]
        fake.datatypeRef = lambda kind, param: {'isParameterizable': param}
        fake.portDomainClock = lambda blockKey, port: {'leaf': 'clk', 'tick': 'clkTick'}[blockKey]
        binds = {'uA': [{'port': 'clk', 'signal': 'clk'}], 'uTick': [{'port': 'clkTick', 'signal': 'clkAux'}]}
        fake.getBDInstanceClockResetBinds = lambda instKey: binds[instKey]
        ret = {'connectDouble': {'connections': conns}, 'interface_defs': defs}
        clocks = [{'clock': 'clk', 'vif': 'clk_vif'}, {'clock': 'clkAux', 'vif': 'clkAux_vif'}]
        monitors, unmonitored = projectOpen.getUvmInternalMonitors(fake, ret, clocks, {'in', 'out'})
    finally:
        intf_gen_utils.get_intf_data, intf_gen_utils.get_intf_type, intf_gen_utils.get_channel_name = saved
    problems = []
    got = [(m['name'], m['interfaceType'], m['clockVif']) for m in monitors]
    if got != [('mid', 'rdy_vld', 'clk_vif'), ('ticks', 'push_ack', 'clkAux_vif')]:
        problems.append(f"the watched connections are {got}, expected mid on clk_vif and ticks on clkAux_vif, "
                        f"the clock uTick binds to its port's domain")
    want = [{'name': 'wide', 'reason': 'its payload is local to the module'},
            {'name': 'slow', 'reason': 'its clock is not a clock port of the block'},
            {'name': 'out', 'reason': 'a boundary port has its name'}]
    if unmonitored != want:
        problems.append(f"the unwatched connections are {unmonitored}, expected {want}")
    if monitors:
        lines = uvmPkg.internal_monitor_build(monitors[1])
        for want in ('ticks_cfg.clk_vif = clkAux_vif;', 'ticks_cfg.is_active = UVM_PASSIVE;',
                     'ticks_cfg.joint_watch = 0;'):
            if want not in lines:
                problems.append(f"the env's build of the ticks agent lacks {want!r}")
    return problems


def make(project, prjYaml, target):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-j8', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           f'A2C_PRJ_YAML={os.path.join(project, prjYaml)}', target]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)


LEAF_PRJ = os.path.join('prj', 'yaml', 'uvmReuseLeafProject.yaml')
ROOT_PRJ = os.path.join('prj', 'yaml', 'uvmReuseProject.yaml')


def check_example(tmp):
    copy = os.path.join(tmp, 'uvmReuse')
    shutil.copytree(EXAMPLE, copy, ignore=shutil.ignore_patterns('build', 'build_xrun', 'regr', '*.db', '.gen',
                                                                 'compile_commands.json', 'obj_dir'))
    leaf = os.path.join(copy, 'leaf')
    result = make(leaf, LEAF_PRJ, 'db')
    if result.returncode != 0:
        return [f"make db rejected the leaf project:\n{result.stdout}{result.stderr}"]
    close_db()
    result = make(copy, ROOT_PRJ, 'db')
    if result.returncode != 0:
        return [f"make db rejected the root project:\n{result.stdout}{result.stderr}"]
    problems = []
    log = result.stdout
    if "reuses nothing of instance" in log:
        problems.append("make db printed a 'reuses nothing' line, but uLeafB matches w8 in v8 and w4 in v4")
    if "Info: the register model of uvmReuseChain generates its own classes for instance uLeafB" not in log:
        problems.append("make db printed no info line for uLeafB, whose variants reuse different leaf packages")
    prj = projectOpen(os.path.join(copy, 'uvmReuse.db'))
    (chain,) = [key for key, row in prj.data['blocks'].items() if row['block'] == 'uvmReuseChain']
    tops = prj.uvmNames[chain]['tops']
    for variant in ('v4', 'v8'):
        got = [entry['pkgName'] for entry in tops[variant]['reuse']]
        if got != ['uvmReuseLeaf_w8_uvm_pkg', 'uvmReuseLeaf_w4_uvm_pkg']:
            problems.append(f"top {variant} reuses {got}, expected the union over both tops, w8 then w4")
        if tops[variant]['rtlScope'] != 'dut.u_wrapper.dut':
            problems.append(f"top {variant}'s RTL scope is {tops[variant]['rtlScope']!r}, expected the wrapper body")
    uvm = prj.getBlockData(chain)['uvm']
    children = {c['name']: c['className'] for block in uvm['registerBlocks'] if block['isRoot']
                for c in block['children']}
    if children != {'uLeafA': 'uvmReuseLeaf_w8_uvm_pkg::uvmReuseLeaf_reg_block',
                    'uLeafB': 'uvmReuseChain_uLeafB_reg_block'}:
        problems.append(f"the chain's register model holds {children}, expected uLeafA as the w8 leaf class and "
                        f"uLeafB as the chain's own")
    monitors = [(m['name'], m['clockVif']) for m in uvm['internalMonitors']]
    if monitors != [('mid', 'clk_vif'), ('ticks', 'clkAux_vif')]:
        problems.append(f"the chain watches {monitors}, expected mid on clk and ticks on clkAux")
    close_db()
    with open(os.path.join(copy, '.gen', 'build.mk')) as f:
        manifest = f.read()
    leafUvm = os.path.join(leaf, 'uvm')
    want = (f"A2C_UVM_REUSED_SV_uvmReuseChain_v8_uvm_tb := {leafUvm}/uvmReuseLeaf_w8_uvm_pkg.sv "
            f"{leafUvm}/uvmReuseLeaf_w4_uvm_pkg.sv")
    if want not in manifest:
        problems.append(f"the manifest lacks {want!r}")

    os.remove(os.path.join(leafUvm, 'uvmReuseLeaf_w4_uvm_pkg.sv'))
    os.remove(os.path.join(copy, 'uvmReuse.db'))
    result = make(copy, ROOT_PRJ, 'db')
    out = result.stdout + result.stderr
    if result.returncode == 0 or 'uvmReuseLeaf_w4_uvm_pkg.sv' not in out or 'make gen in project uvmReuseLeaf' not in out:
        problems.append(f"make db with the leaf's w4 package missing returned {result.returncode}; expected an error "
                        f"naming the file and telling to run make gen in project uvmReuseLeaf:\n{out}")
    return problems


def run_all_tests():
    print("\n" + "=" * 70)
    print("UVM REUSE IN A COMPOSED ROOT")
    print("=" * 70)
    problems = check_derive_reuse() + check_register_tree() + check_internal_monitors()
    tmp = tempfile.mkdtemp(prefix='uvm_reuse_', dir=test_dir)
    try:
        problems += check_example(tmp)
    finally:
        remove_tree(tmp)
    if problems:
        for problem in problems:
            print(f"  FAIL: {problem}")
        print("\nFAIL: a composed root's UVM reuse disagrees with section 9.15")
        return 1
    print("  PASS: equal values reuse the standalone variant, unmatched ones reuse nothing with an info line")
    print("  PASS: a block without params reuses its variantless package; no variant takes the default values")
    print("  PASS: a child precedes its container, one entry per (block, variant), every top the union")
    print("  PASS: a reused register node emits no class, keeps its offset, and a memory below it needs a2c_reg_map")
    print("  PASS: internal monitors on fixed types, on the source instance's clock, with each skip reason")
    print("  PASS: internal agents do not count toward the joint stall rule")
    print("  PASS: examples/uvmReuse: union reuse lists, wrapper RTL scope, register reuse dropped where variants "
          "differ, A2C_UVM_REUSED_SV_<top>, and an error for a child package not generated")
    print("\nPASS: a composed root reuses its children's UVM packages as section 9.15 says")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
