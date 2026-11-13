#!/usr/bin/env python3
"""A routed top's register model has one uvm_reg_block per instance on the
way to its registers, each map added to its parent's at the instance's
offset, and an env identical to a leaf top's.

Each child block builds its own registers and memories at its own offsets and
creates its own default_map. Its parent adds that map with add_submap() at
the instance's slot offset, so UVM gives every register its absolute address.
Only the root calls lock_model(): a child that locked would freeze the model
before its parent added its map. Only the root installs the catcher of the
UVM/RSRC/NOREGEX warning each child block's configure() raises, around
building every block below it. A root map that is an a2c_reg_map then
checks its strided rows for overlaps, since a test may never look anything up
through it. A memory row narrower than the decoder's stride needs
set_mem_stride() on the map of the memory's own block, which must be an
a2c_reg_map. An a2c_reg_map may only be a submap of another one, so
every map above a memory is an a2c_reg_map too, and every other map is a plain
uvm_reg_map. Classes are named <top>_<instance path>_reg_<register> and
<top>_<instance path>_reg_block, so two instances of one block at different
variants get classes of their own widths.

The env reaches the model only through regmodel.default_map, the root map:
the sequencer, the predictor, the Mode B guard and its write subscriber all
take it. The env class of the routed top must therefore be the leaf top's,
line for line.

The fixture is test_uvm_register_tree.py's routed copy of fixtures/uvm-blocks.
Offsets inside each leaf come from the view, which test_uvm_register_view.py
checks against the firmware header for a leaf top. The env is compared with
the env of the unedited fixture, where ubDut owns its own register.
"""

import os
import shutil
import sys
import tempfile

import test_uvm_register_tree as tree
from _addrctl_helpers import test_dir
from _tmp_helpers import close_db, remove_tree
from pysrc.processYaml import projectOpen


PKG = os.path.join('uvm', 'ubDut_uvm_pkg.sv')


def reg_class(cls, name, access, volatile, fields):
    """fields: (name, width, reset) from the most significant down."""
    width = sum(f[1] for f in fields)
    lines = [f'class {cls} extends uvm_reg;']
    lines += [f'rand uvm_reg_field {f[0]};' for f in fields]
    lines += ['', f'`uvm_object_utils({cls})', '', f'function new(string name = "{name}");',
              f'super.new(name, {width}, UVM_NO_COVERAGE);', 'endfunction', '', 'virtual function void build();']
    lsb = width
    for field, w, reset in fields:
        lsb -= w
        lines += [f'{field} = uvm_reg_field::type_id::create("{field}");',
                  f'{field}.configure(this, {w}, {lsb}, "{access}", {volatile}, {w}\'h{reset:x}, 1, '
                  f'{int(access == "RW")}, 0);']
    return lines + ['endfunction', f'endclass : {cls}', '']


def block_class(cls, regs, mems, children, a2c, root):
    """regs: (member, class, offset, access); mems: (name, depth, width,
    access, offset, stride); children: (member, class, offset)."""
    lines = [f'class {cls} extends uvm_reg_block;']
    lines += [f'rand {r[1]} {r[0]};' for r in regs]
    lines += [f'uvm_mem {m[0]};' for m in mems]
    lines += [f'rand {c[1]} {c[0]};' for c in children]
    lines += ['', f'`uvm_object_utils({cls})', '', f'function new(string name = "{cls}");',
              'super.new(name, UVM_NO_COVERAGE);', 'endfunction', '', 'virtual function void build();']
    if a2c:
        lines.append('a2c_uvm_pkg::a2c_reg_map a2c_map;')
    catcher = root and children
    for r in regs:
        lines += [f'{r[0]} = {r[1]}::type_id::create("{r[0]}");', f'{r[0]}.configure(this);', f'{r[0]}.build();']
    for m in mems:
        lines += [f'{m[0]} = new("{m[0]}", {m[1]}, {m[2]}, "{m[3]}", UVM_NO_COVERAGE);', f'{m[0]}.configure(this);']
    if catcher:
        lines += ["// In UVM 1.2, each child block's configure() raises a UVM/RSRC/NOREGEX",
                  "// warning that names it; the catcher demotes those warnings to info.",
                  'a2c_uvm_pkg::a2c_child_block_catcher::install(this);']
    for c in children:
        lines += [f'{c[0]} = {c[1]}::type_id::create("{c[0]}", , get_full_name());', f'{c[0]}.configure(this);',
                  f'{c[0]}.build();']
    if catcher:
        lines.append('a2c_uvm_pkg::a2c_child_block_catcher::remove(this);')
    if a2c:
        if mems:
            lines += ["// UVM would step each memory by its n_bits rounded up to bus words;",
                      "// a2c_reg_map steps it by the decoder's row stride."]
        else:
            lines.append("// A child block's a2c_reg_map may only be a submap of an a2c_reg_map.")
        lines += ['a2c_map = a2c_uvm_pkg::a2c_reg_map::type_id::create("default_map", , get_full_name());',
                  "a2c_map.configure(this, 'h0, 4, UVM_LITTLE_ENDIAN, 1);", 'add_map(a2c_map);']
    else:
        lines.append("default_map = create_map(\"default_map\", 'h0, 4, UVM_LITTLE_ENDIAN, 1);")
    lines += [f'default_map.add_reg({r[0]}, \'h{r[2]:x}, "{r[3]}");' for r in regs]
    for m in mems:
        lines += [f'default_map.add_mem({m[0]}, \'h{m[4]:x}, "{m[3]}");', f'a2c_map.set_mem_stride({m[0]}, {m[5]});']
    lines += [f"default_map.add_submap({c[0]}.default_map, 'h{c[2]:x});" for c in children]
    if root:
        lines.append('lock_model();')
        if a2c:
            lines.append('a2c_map.check_overlaps_once();')
    return lines + ['endfunction', f'endclass : {cls}', '']


def expected_regmodel(offsets):
    lines = list()
    for inst, v in (('uA', 'v0'), ('uB', 'v1')):
        w, d = tree.UB_W[v], tree.UB_D[v]
        lines += reg_class(f'ubDut_{inst}_reg_cfg', 'cfg', 'RW', 0, [('hi', 8, 0), ('lo', w, 5)])
        lines += block_class(f'ubDut_{inst}_reg_block', [('cfg', f'ubDut_{inst}_reg_cfg', offsets['cfg'], 'RW')],
                             [('tbl', d, 8 + w, 'RO', offsets['tbl'], 8)], [], True, False)
    for inst in ('uDeep0', 'uDeep1'):
        lines += reg_class(f'ubDut_uBridge_{inst}_reg_stat', 'stat', 'RO', 1, [('data', 8, 0)])
        lines += block_class(f'ubDut_uBridge_{inst}_reg_block',
                             [('stat', f'ubDut_uBridge_{inst}_reg_stat', offsets['stat'], 'RO')], [], [], False, False)
    lines += block_class('ubDut_uBridge_reg_block', [], [],
                         [('uDeep0', 'ubDut_uBridge_uDeep0_reg_block', 0x0),
                          ('uDeep1', 'ubDut_uBridge_uDeep1_reg_block', 0x100)], False, False)
    lines += reg_class('ubDut_uWrap_uInner_reg_ctrl', 'ctrl', 'RW', 0, [('data', 8, 0)])
    lines += block_class('ubDut_uWrap_uInner_reg_block',
                         [('ctrl', 'ubDut_uWrap_uInner_reg_ctrl', offsets['ctrl'], 'RW')], [], [], False, False)
    lines += block_class('ubDut_uWrap_reg_block', [], [], [('uInner', 'ubDut_uWrap_uInner_reg_block', 0x0)],
                         False, False)
    lines += block_class('ubDut_reg_block', [], [],
                         [('uA', 'ubDut_uA_reg_block', 0x0), ('uB', 'ubDut_uB_reg_block', 0x1000),
                          ('uBridge', 'ubDut_uBridge_reg_block', 0x3000),
                          ('uWrap', 'ubDut_uWrap_reg_block', 0x4000)], True, True)
    return lines


def section(lines, first, last):
    return lines[lines.index(first):lines.index(last) + 1]


def read_lines(project):
    with open(os.path.join(project, PKG)) as f:
        return [line.strip() for line in f]


def build(project, edits):
    shutil.copytree(tree.FIXTURE, project)
    if edits:
        tree.edit_fixture(project, edits)
    for target in ('db', 'newmodule', 'gen'):
        result = tree.make(project, target)
        if result.returncode != 0:
            return f"make {target} rejected the fixture (rc={result.returncode})\n{result.stdout + result.stderr}"
    return None


def check(routed, leaf):
    prj = projectOpen(os.path.join(routed, tree.DB))
    offsets = dict()
    for section_, nameField in (('registers', 'register'), ('memories', 'memory')):
        for row in prj.data[section_].values():
            offsets[row[nameField]] = int(row['offset'])
    close_db()
    lines = read_lines(routed)
    problems = []
    want = expected_regmodel(offsets)
    got = section(lines, 'class ubDut_uA_reg_cfg extends uvm_reg;', 'endclass : ubDut_reg_block')
    if got != want[:-1]:
        diff = [f"line {i}: {g!r} expected {w!r}" for i, (g, w) in enumerate(zip(got, want)) if g != w][:5]
        problems.append(f"the register model has {len(got)} lines, expected {len(want) - 1}; first differences {diff}")
    if sum(line == 'lock_model();' for line in lines) != 1:
        problems.append("lock_model() is called other than once, by the root block")
    if sum(line == 'a2c_uvm_pkg::a2c_child_block_catcher::install(this);' for line in lines) != 1:
        problems.append("the child block catcher is installed other than once, by the root block")
    env = ('class ubDut_env extends uvm_env;', 'endclass : ubDut_env')
    leafEnv = section(read_lines(leaf), *env)
    if section(lines, *env) != leafEnv:
        problems.append("the routed top's env class differs from the leaf top's")
    return problems


def run_all_tests():
    print("\n" + "=" * 70)
    print("UVM REGISTER MODEL OF A ROUTED TOP")
    print("=" * 70)
    tmp = tempfile.mkdtemp(prefix='uvm_pkg_routed_', dir=test_dir)
    try:
        routed = os.path.join(tmp, 'routed')
        leaf = os.path.join(tmp, 'leaf')
        for project, edits in ((routed, tree.EDITS), (leaf, None)):
            error = build(project, edits)
            if error:
                print(f"FAIL: {error}")
                return 1
        problems = check(routed, leaf)
    finally:
        remove_tree(tmp)
    if problems:
        for problem in problems:
            print(f"  FAIL: {problem}")
        print("\nFAIL: the routed register model disagrees with the instance tree")
        return 1
    print("  PASS: one class per instance and register, named by the instance path, at each instance's variant")
    print("  PASS: child maps added at their slot offsets, the root alone locking the model and checking overlaps")
    print("  PASS: the root alone catching its child blocks' resource warnings, around building them")
    print("  PASS: a2c_reg_maps on the blocks with a memory and on every map above them, plain maps elsewhere")
    print("  PASS: set_mem_stride() on each memory's own map, at the worst-case stride")
    print("  PASS: the env is the leaf top's env, line for line")
    print("\nPASS: a routed top's register model mirrors its instance hierarchy")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
