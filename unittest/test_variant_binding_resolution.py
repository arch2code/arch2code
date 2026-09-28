#!/usr/bin/env python3
"""Variant bindings resolve through the same identities every consumer uses.

Six cells, each a case that once failed beside a control that already worked:

1. A binding value naming an enum member resolves like a literal of the same
   value. Control: the literal.
2. In a composed root, two projects each declare the same variant label of one
   leaf, sourcing its parameter from different container parameters. Each
   instance is checked against the declaration it resolves to. Control: an
   instance whose own declaration names a parameter its container lacks is
   still rejected.
3. An owned container outside the active tree still renders its block view,
   and the child's factory domain is the one a build activating the container
   registers. Control: the same container instantiated under the top.
4. Two children whose parameters are sourced from DIFFERENT container
   parameters of equal value do not bind directly. Control: both sourced from
   the same container parameter do. Every block view renders in both, including
   the leaf's, which meets the connection through its own port.
5. A binding naming an enum member or a constant of an included context is
   spelled by name in the make-generated parent top.sv, which imports that
   context's package and lints. Control: a constant of the parent's own
   context adds no import.
6. In the cell 2 composed root, scopeA's 'v0' of the leaf is container-sourced
   and scopeB's is a literal. Only wrapA's pair is pair-specific. Control:
   wrapA's pair.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import traceback

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectOpen

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')


def _header(name):
    print(f"\n{'='*70}\nTest: {name}\n{'='*70}")


def _project_yaml(name, files, top=None):
    topLine = f"topInstance: {top}\n" if top else ""
    entries = ''.join(f"  - {f}\n" for f in files)
    return (f"projectName: {name}\nyamlFormat: 2\n{topLine}"
            f"dirs:\n  root: .\nfileGeneration:\n  fileCopyrightStatement: \"\"\n"
            f"projectFiles:\n{entries}")


def _write_tree(files):
    """Write {relative path: content} under a fresh work dir inside unittest/."""
    work = tempfile.mkdtemp(prefix='variant_binding_', dir=test_dir)
    for rel, content in files.items():
        path = os.path.join(work, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
    return work


def _build_db(work, project):
    """Build in a subprocess: validation populates process-global state."""
    db = os.path.join(work, 'test.db')
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, ARCH2CODE, '--yaml', os.path.join(work, project), '--db', db],
        capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
    return db, result.stdout + result.stderr, result.returncode


def _close_db():
    if g.db is not None:
        g.db.close()
        g.db = None


def _block_key(prj, name):
    return next(key for key, row in prj.data['blocks'].items() if row['block'] == name)


def _instance(prj, name):
    return next(row for row in prj.data['instances'].values() if row['instance'] == name)


# --- Cell 1: enum-member binding value ---------------------------------------

ENUM_ARCH = """ipParameters:
  constants:
    MODE: {value: 0, maxValue: 7, desc: "Behavioral mode"}
types:
  modeT:
    desc: "Available modes"
    enum:
      - {enumName: SLOW, value: 0, desc: "Slow"}
      - {enumName: FAST, value: 3, desc: "Fast"}
blocks:
  top: {desc: "Root", hasMdl: true, hasRtl: false}
  leaf: {desc: "Parameterized leaf", params: [MODE], hasMdl: true, hasRtl: false}
instances:
  uTop: {container: top, instanceType: top}
  uLeaf: {container: top, instanceType: leaf, variant: fast}
parameters:
  leaf:
    fast:
      MODE: __VALUE__
"""


def _fast_descriptor_values(value):
    work = _write_tree({
        'project.yaml': _project_yaml('enumBinding', ['arch.yaml'], 'uTop'),
        'arch.yaml': ENUM_ARCH.replace('__VALUE__', value),
    })
    try:
        db, out, rc = _build_db(work, 'project.yaml')
        if rc != 0:
            print(f"  FAIL: binding MODE to {value} was rejected\n{out[-3000:]}")
            return None
        prj = projectOpen(db)
        (descriptor,) = [d for d in prj.variantConfigDescriptors[_block_key(prj, 'leaf')]
                         if d['variant'] == 'fast']
        _close_db()
        return descriptor['values']
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_enum_member_binding_resolves():
    _header("a variant binding naming an enum member resolves to its value")
    control = _fast_descriptor_values('3')
    if control != {'MODE': 3}:
        print(f"  FAIL: control literal binding resolved to {control}")
        return False
    values = _fast_descriptor_values('FAST')
    if values != control:
        print(f"  FAIL: enum binding resolved to {values}, literal to {control}")
        return False
    print("  PASS")
    return True


# --- Cell 2: container-sourced bindings in a composed root -------------------

SCOPE_LEAF = """ipParameters:
  constants:
    W: {value: 8, maxValue: 32, desc: "Leaf knob"}
types:
  dummyT: {width: 8, desc: "Makes this context include-valid"}
blocks:
  leaf: {desc: "Reusable leaf", params: [W], hasMdl: true, hasRtl: false}
"""

SCOPE_WRAPPER = """include: [../ip/leaf.yaml]
ipParameters:
  constants:
    __P__: {value: 8, maxValue: 32, desc: "Container knob"}
blocks:
  top__P__: {desc: "Standalone root", hasMdl: true, hasRtl: false}
  wrap__P__: {desc: "Wrapper", params: [__P__], hasMdl: true, hasRtl: false}
instances:
  uTop__P__: {container: top__P__, instanceType: top__P__}
  uWrap__P__: {container: top__P__, instanceType: wrap__P__, variant: configured}
  uLeaf__P__: {container: wrap__P__, instanceType: leaf, variant: v0}
parameters:
  wrap__P__:
    configured:
      __P__: 8
  leaf:
    v0:
      W: {containerParam: __SOURCE__}
"""

SCOPE_TOP = """include: [../a/arch.yaml, ../b/arch.yaml]
blocks:
  top: {desc: "Composed root", hasMdl: true, hasRtl: false}
instances:
  uTop: {container: top, instanceType: top}
  uA: {container: top, instanceType: wrapA, variant: configured}
  uB: {container: top, instanceType: wrapB, variant: configured}
"""


def _composed_scope(bSource):
    return _write_tree({
        'ip/project.yaml': _project_yaml('scopeIp', ['leaf.yaml']),
        'ip/leaf.yaml': SCOPE_LEAF,
        'a/project.yaml': _project_yaml('scopeA', ['../ip/project.yaml', 'arch.yaml'], 'uTopA'),
        'a/arch.yaml': SCOPE_WRAPPER.replace('__P__', 'A').replace('__SOURCE__', 'A'),
        'b/project.yaml': _project_yaml('scopeB', ['../ip/project.yaml', 'arch.yaml'], 'uTopB'),
        'b/arch.yaml': SCOPE_WRAPPER.replace('__P__', 'B').replace('__SOURCE__', bSource),
        'top/project.yaml': _project_yaml(
            'scopeTop', ['../a/project.yaml', '../b/project.yaml', 'arch.yaml'], 'uTop'),
        'top/arch.yaml': SCOPE_TOP,
    })


def test_container_sourced_checked_against_own_declaration():
    _header("a composed root checks each instance against its own variant declaration")
    work = _composed_scope('B')
    try:
        db, out, rc = _build_db(work, 'top/project.yaml')
        if rc != 0:
            print(f"  FAIL: two projects' own-scope 'v0' declarations were cross-checked"
                  f"\n{out[-3000:]}")
            return False
        prj = projectOpen(db)
        sourced = {d['declaringProject']: d['containerSourced']
                   for d in prj.variantConfigDescriptors[_block_key(prj, 'leaf')]
                   if d['variant'] == 'v0'}
        _close_db()
        if sourced != {'scopeA': {'W': 'A'}, 'scopeB': {'W': 'B'}}:
            print(f"  FAIL: unexpected per-project container sources {sourced}")
            return False
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)

    # Control: B's own declaration names A, which wrapB does not declare.
    work = _composed_scope('A')
    try:
        _db, out, rc = _build_db(work, 'top/project.yaml')
        if rc == 0:
            print("  FAIL: a container parameter missing from the instance's own "
                  "container was accepted")
            return False
        expected = "instance uLeafB"
        if expected not in out or "container block 'wrapB' declares no such parameter" not in out:
            print(f"  FAIL: rejection did not name uLeafB and wrapB\n{out[-3000:]}")
            return False
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("  PASS")
    return True


# --- Cell 3: owned container outside the active tree -------------------------

INACTIVE_ARCH = """ipParameters:
  constants:
    MODE: {value: 1, maxValue: 7, desc: "Behavioral mode"}
types:
  dummyT: {width: 8, desc: "Makes this context include-valid"}
blocks:
  top: {desc: "Active root", hasMdl: true, hasRtl: false}
  spare: {desc: "Owned container", hasMdl: true, hasRtl: false}
  leaf: {desc: "Parameterized child", params: [MODE], hasMdl: true, hasRtl: false}
instances:
  uTop: {container: top, instanceType: top}
__SPARE__  uLeaf: {container: spare, instanceType: leaf, variant: use}
parameters:
  leaf:
    use:
      MODE: 3
"""


def _spare_leaf_factory(active):
    spare = "  uSpare: {container: top, instanceType: spare}\n" if active else ""
    work = _write_tree({
        'project.yaml': _project_yaml('inactiveProbe', ['arch.yaml'], 'uTop'),
        'arch.yaml': INACTIVE_ARCH.replace('__SPARE__', spare),
    })
    try:
        db, out, rc = _build_db(work, 'project.yaml')
        if rc != 0:
            print(f"  FAIL: db build failed (active={active})\n{out[-3000:]}")
            return None, None
        prj = projectOpen(db)
        spareKey = _block_key(prj, 'spare')
        leafKey = _block_key(prj, 'leaf')
        data = prj.getBlockData(spareKey)
        factory = data['subBlockInstances'][_instance(prj, 'uLeaf')['instanceKey']][
            'createInstanceProjectName']
        pair = prj.registrarPairs.get((spareKey, leafKey))
        _close_db()
        return factory, pair
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_inactive_container_view_renders():
    _header("an owned container outside the active tree renders its block view")
    activeFactory, activePair = _spare_leaf_factory(active=True)
    if activePair is None or activeFactory != activePair['factoryProject']:
        print(f"  FAIL: control view domain {activeFactory} differs from its "
              f"registrar pair {activePair and activePair['factoryProject']}")
        return False
    factory, pair = _spare_leaf_factory(active=False)
    if pair is not None:
        print("  FAIL: an unreachable container gained a registrar pair")
        return False
    if factory != activeFactory:
        print(f"  FAIL: inactive container spells domain {factory}; activating "
              f"it registers {activeFactory}")
        return False
    print("  PASS")
    return True


# --- Cell 4: container-sourced ends compare by supplying parameter -----------

BIND_ARCH = """ipParameters:
  constants:
    W: {value: 8, maxValue: 16, desc: "Leaf data width"}
    A: {value: 8, maxValue: 16, desc: "Container knob A"}
    B: {value: 8, maxValue: 16, desc: "Container knob B"}
  types:
    dataT: {width: W, desc: "Data"}
structures:
  dataSt: {data: {varType: dataT, desc: "Data payload"}}
interfaces:
  dataIf: {interfaceType: rdy_vld, desc: "Data stream", structures: [{structure: dataSt, structureType: data_t}]}
blocks:
  top: {desc: "Root", hasMdl: true, hasRtl: false}
  cont: {desc: "Container", params: [A, B], hasMdl: true, hasRtl: false}
  leaf:
    desc: "Leaf"
    params: [W]
    hasMdl: true
    hasRtl: false
    ports:
      out: {interface: dataIf, direction: src}
      in: {interface: dataIf, direction: dst}
instances:
  uTop: {container: top, instanceType: top}
  uCont: {container: top, instanceType: cont, variant: v}
  uL1: {container: cont, instanceType: leaf, variant: fromA}
  uL2: {container: cont, instanceType: leaf, variant: __SECOND__}
connections:
  - {interface: dataIf, src: uL1, srcport: out, dst: uL2, dstport: in}
parameters:
  cont:
    v: {A: 8, B: 8}
  leaf:
    fromA: {W: {containerParam: A}}
    fromB: {W: {containerParam: B}}
"""


def _binds_directly(secondVariant):
    work = _write_tree({
        'project.yaml': _project_yaml('bindProbe', ['arch.yaml'], 'uTop'),
        'arch.yaml': BIND_ARCH.replace('__SECOND__', secondVariant),
    })
    try:
        db, out, rc = _build_db(work, 'project.yaml')
        if rc != 0:
            print(f"  FAIL: db build failed ({secondVariant})\n{out[-3000:]}")
            return None
        prj = projectOpen(db)
        # Generation renders every block's view. A leaf's own view reaches the
        # connection through its port, with both ends sitting in the leaf's
        # container rather than in the block being rendered.
        for blockKey in prj.data['blocks']:
            prj.getBlockData(blockKey)
        interfaceRow = next(row for row in prj.data['interfaces'].values()
                            if row['interface'] == 'dataIf')
        first = _instance(prj, 'uL1')
        second = _instance(prj, 'uL2')
        direct = prj.bindsDirectly(interfaceRow, interfaceRow['interfaceKey'],
                                   prj._resolveInstanceConfigFields(first),
                                   prj._resolveInstanceConfigFields(second))
        # The rendered container carries an adapter exactly when the ends do
        # not bind directly.
        (conn,) = prj.getBlockData(_block_key(prj, 'cont'))['connectDouble'][
            'connections'].values()
        adapted = bool(conn.get('crossInterfaceEnds'))
        _close_db()
        if adapted == direct:
            print(f"  FAIL: bindsDirectly={direct} but the container view "
                  f"{'has' if adapted else 'lacks'} an adapter ({secondVariant})")
            return None
        return direct
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_container_sourced_ends_compare_by_supplier():
    _header("ends sourced from different container parameters do not bind directly")
    if _binds_directly('fromA') is not True:
        print("  FAIL: control ends sourced from one container parameter did not "
              "bind directly")
        return False
    if _binds_directly('fromB') is not False:
        print("  FAIL: ends sourced from container parameters A and B bound directly")
        return False
    print("  PASS")
    return True


# --- Cell 5: named bindings in the parent's generated SV instantiation ------

# modes.yaml is its own context, so a binding naming FAST or MODE_FAST needs
# the parent to import a package other than its own.
NAMED_RTL_MODES = """constants:
  MODE_FAST: {value: 3, desc: "Fast mode value"}
types:
  modeT:
    desc: "Available modes"
    enum:
      - {enumName: SLOW, value: 0, desc: "Slow"}
      - {enumName: FAST, value: 3, desc: "Fast"}
"""

NAMED_RTL_ARCH = """include: [modes.yaml]
ipParameters:
  constants:
    MODE: {value: 0, maxValue: 7, desc: "Behavioral mode"}
constants:
  MODE_LOCAL: {value: 2, desc: "Declared in the parent's own context"}
types:
  dummyT: {width: 8, desc: "Makes this context include-valid"}
blocks:
  top: {desc: "Root", hasMdl: true, hasRtl: true}
  leaf: {desc: "Parameterized leaf", params: [MODE], hasMdl: true, hasRtl: true}
instances:
  uTop: {container: top, instanceType: top}
  uLeaf: {container: top, instanceType: leaf, variant: fast}
parameters:
  leaf:
    fast:
      MODE: __VALUE__
"""

NAMED_RTL_MAKEFILE = """PROJECTNAME = namedSvBinding
TB_TOP_MODULE = top
HDL_TOP_MODULE = top
A2C_PRJ_YAML = $(REPO_ROOT)/project.yaml
include $(A2C_ROOT)/include/make/a2c-common.mk
.PHONY: clean
clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)
"""


def _run_checked(cmd, work):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(cmd, cwd=work, capture_output=True, text=True,
                            timeout=600, env=env)
    return result.returncode, result.stdout + result.stderr


def _generated_top_sv(value, lintFlags):
    """Generate the fixture with make and lint it; return (top.sv, failure)."""
    if shutil.which('verilator') is None:
        raise RuntimeError("verilator is not on PATH")
    work = _write_tree({
        'project.yaml': _project_yaml('namedSvBinding', ['arch.yaml'], 'uTop'),
        'arch.yaml': NAMED_RTL_ARCH.replace('__VALUE__', value),
        'modes.yaml': NAMED_RTL_MODES,
        'Makefile': NAMED_RTL_MAKEFILE,
    })
    try:
        make = ['make', '-j4', f'REPO_ROOT={work}', f'A2C_ROOT={base_dir}']
        for target in ('clean', 'db', 'newmodule', 'gen'):
            rc, out = _run_checked(make + [target], work)
            if rc != 0:
                return None, f"make {target} failed for MODE: {value}\n{out[-3000:]}"
        with open(os.path.join(work, 'rtl', 'top.sv')) as f:
            top = f.read()
        rtl = [os.path.join('rtl', name) for name in
               ('modes_package.sv', 'arch_package.sv', 'leaf.sv', 'top.sv')]
        rc, out = _run_checked(['verilator', '--lint-only', '--top-module', 'top',
                                *lintFlags, *rtl], work)
        if rc != 0:
            return top, f"verilator --lint-only failed for MODE: {value}\n{out[-3000:]}"
        return top, None
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _generated_imports(top):
    return [line for line in top.splitlines() if line.startswith('import ')]


def test_named_binding_sv_instantiation():
    _header("a named binding is spelled by name in a parent that imports its package")
    # modeT is two bits wide, so FAST widens into the int-typed MODE parameter.
    cases = [
        ('FAST', ['-Wno-WIDTHEXPAND'], ['import arch_package::*;', 'import modes_package::*;']),
        ('MODE_FAST', [], ['import arch_package::*;', 'import modes_package::*;']),
        ('MODE_LOCAL', [], ['import arch_package::*;']),
    ]
    ok = True
    for value, lintFlags, imports in cases:
        top, failure = _generated_top_sv(value, lintFlags)
        failures = [failure] if failure else []
        if top is not None and f'leaf #(.MODE({value})) uLeaf' not in top:
            failures.append(f"top.sv does not spell .MODE({value})")
        if top is not None and _generated_imports(top) != imports:
            failures.append(f"top.sv imports {_generated_imports(top)}, expected {imports}")
        for failure in failures:
            print(f"  FAIL: {failure}")
        if failures:
            print(top)
            ok = False
    if ok:
        print("  PASS")
    return ok


# --- Cell 6: pair-specific registration follows the declaring project -------

def test_pair_specific_follows_declaring_project():
    _header("a pair is pair-specific only when its own declaration is container-sourced")
    work = _composed_scope('B')
    bArch = os.path.join(work, 'b', 'arch.yaml')
    with open(bArch) as f:
        text = f.read()
    with open(bArch, 'w') as f:
        f.write(text.replace('W: {containerParam: B}', 'W: 4'))
    try:
        db, out, rc = _build_db(work, 'top/project.yaml')
        if rc != 0:
            print(f"  FAIL: db build failed\n{out[-3000:]}")
            return False
        prj = projectOpen(db)
        leafKey = _block_key(prj, 'leaf')
        specific = {name: prj.registrarPairs[(_block_key(prj, name), leafKey)]['ownerPairSpecific']
                    for name in ('wrapA', 'wrapB')}
        _close_db()
        if specific != {'wrapA': True, 'wrapB': False}:
            print(f"  FAIL: ownerPairSpecific is {specific}; only scopeA's 'v0' is "
                  f"container-sourced")
            return False
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)
    print("  PASS")
    return True


def _run_cell(cell):
    try:
        return cell()
    except Exception as exc:
        print(f"  FAIL: {cell.__name__} raised {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return False


def run_all_tests():
    cells = [
        test_enum_member_binding_resolves,
        test_container_sourced_checked_against_own_declaration,
        test_inactive_container_view_renders,
        test_container_sourced_ends_compare_by_supplier,
        test_named_binding_sv_instantiation,
        test_pair_specific_follows_declaring_project,
    ]
    results = [_run_cell(cell) for cell in cells]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
