#!/usr/bin/env python3
"""Which project's binding of a variant label a consumer resolves to when two
projects declare the same label for the same block.

A block's config context can be owned DOWNSTREAM of the project that declares the
block. Route a leaf's boundary port through a wrapper's connectionMap and the
leaf's parameterizable surface is reached through the wrapper's own interface, so
the wrapper's file is where the leaf's per-variant Config struct is emitted. The
leaf's author can still write a `parameters:` binding of the same label in its own
file, which puts two candidate bindings of one label on the table.

Precedence has three tiers: the consumer's own project, then the project owning
the config context, then the project declaring the block. This suite pins the
second against the third, which nothing else in the corpus does. Every other
two-project composition has one candidate, so reordering those two tiers changes
no generated artifact anywhere else and would land silently.

Fixture: `fixtures/param-variant-two-declarers`, three projects over one label.
- projIp declares the leaf and binds v0 at LEAF_W 12.
- projWrap owns the leaf's config context and binds v0 at LEAF_W 8.
- twoDeclarersProj consumes the leaf and binds nothing, so the consumer tier
  cannot answer.
projWrap must win, because it is the project that emits the struct.
"""

import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.intf_gen_utils import cpp_descriptor_config_name
from pysrc.processYaml import projectOpen

FIXTURE = os.path.join(test_dir, 'fixtures', 'param-variant-two-declarers')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

# The leaf's block key: context keys are whole paths relative to the assembler
# project file's directory, so the leaf qualifies to its declaring file's path.
LEAF_KEY = 'leafIp/../../projIp/yaml/ipTop.yaml'


def _copy_fixture(prefix):
    """Copy the committed fixture into a fresh temp tree under unittest/ and
    return its path. Inside unittest/ so any scaffold path resolves the repo root
    the way a real project does."""
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
    return work


def _build_db(work):
    """Build the composition from its assembler project file. Returns
    (db_path, combined output, returncode)."""
    db = os.path.join(work, 'param-variant-two-declarers.db')
    project = os.path.join(work, 'top', 'yaml', 'twoDeclarersProject.yaml')
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, ARCH2CODE, '--yaml', project, '--db', db],
        capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
    return db, result.stdout + result.stderr, result.returncode


def _close_db():
    if g.db is not None:
        g.db.close()
        g.db = None


def _declared_bindings(prj):
    """Return {projectName: value} for every declared binding of the leaf's v0
    LEAF_W. Each declaring file contributes its own row, so this reads the flat
    table. The nested per-block view keeps one row per (block, variant, param)
    and would drop a declarer."""
    return {row['projectName']: row['value']
            for row in prj.data['parametersvariantsparams'].values()
            if row['blockKey'] == LEAF_KEY and row['variant'] == 'v0'
            and row['param'] == 'LEAF_W'}


def _header(name):
    print(f"\n{'='*70}\nTest: {name}\n{'='*70}")


def test_config_context_owner_outranks_block_declarer():
    _header("two projects declare one variant label: the config context owner's "
            "binding wins over the block declarer's")
    work = _copy_fixture('param_two_declarers_')
    try:
        db, out, rc = _build_db(work)
        if rc != 0:
            print("  FAIL: the two-declarer composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        prj = projectOpen(db)
        # Premise. Both candidates must be on the table, at values that tell them
        # apart, or the selection below has nothing to choose between and the
        # cell passes vacuously.
        bindings = _declared_bindings(prj)
        if bindings != {'projWrap': 8, 'projIp': 12}:
            print(f"  FAIL: fixture no longer states the premise this cell tests; "
                  f"declared v0 LEAF_W bindings are {bindings} rather than one "
                  f"from each of projWrap and projIp at differing values")
            return False

        leafRow = prj.data['blocks'][LEAF_KEY]
        if prj.contextOwningProject[leafRow['configContext']] != 'projWrap' \
                or prj.contextOwningProject[leafRow['_context']] != 'projIp':
            print(f"  FAIL: fixture no longer states the premise this cell tests; "
                  f"the leaf's config context is owned by "
                  f"{prj.contextOwningProject[leafRow['configContext']]} and the "
                  f"leaf is declared by "
                  f"{prj.contextOwningProject[leafRow['_context']]}, which must "
                  f"be two different projects")
            return False

        # The wrapper's trampoline registers the leaf, so this is the selection a
        # real emission makes. The consumer here is projWrap, which declares no
        # FOREIGN binding of the label, so the consumer tier cannot answer and
        # the contest is between the remaining two.
        view = prj.getRegistrarConfigView(LEAF_KEY, 'wrapBlk')
        descriptor = view['variantDescriptors']['v0']
        if descriptor is None:
            print("  FAIL: no descriptor selected for v0")
            return False
        if (descriptor['declaringProject'], descriptor['isForeign']) != ('projWrap', False):
            print(f"  FAIL: selected {descriptor['declaringProject']}'s binding "
                  f"(isForeign={descriptor['isForeign']}); the config context "
                  f"owner projWrap must win over the block declarer projIp")
            return False
        if descriptor['values']['LEAF_W'] != 8:
            print(f"  FAIL: selected binding resolves LEAF_W to "
                  f"{descriptor['values']['LEAF_W']}, expected projWrap's 8")
            return False
        # The emitted spelling, so the cell fails on the artifact and not only on
        # the view row. The config context owner's binding is the one that project
        # emits in its own context config header, hence a bare struct name; the
        # block declarer's would be owner-qualified into a foreign Config module
        # and would drag an import of that module into the trampoline.
        spelling = cpp_descriptor_config_name(descriptor, view['defaultConfig'])
        if spelling != 'leafIpV0Config':
            print(f"  FAIL: trampoline spells {spelling}, expected leafIpV0Config")
            return False
        if view['foreignConfigModules']:
            print(f"  FAIL: trampoline imports foreign Config modules "
                  f"{view['foreignConfigModules']}, expected none")
            return False
        print("  PASS: config context owner's binding selected, at its own value, "
              "spelled as its own struct")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_registrar_requirement_uses_config_owner_precedence():
    _header("registrar classification uses the selected project's container binding")
    work = _copy_fixture('param_two_declarers_container_')
    try:
        path = os.path.join(work, 'projWrap', 'yaml', 'wrapTop.yaml')
        with open(path) as f:
            text = f.read()
        old = "            LEAF_W: 8"
        new = "            LEAF_W: { containerParam: WRAP_W }"
        if old not in text:
            raise AssertionError("wrapper binding anchor is missing")
        with open(path, 'w') as f:
            f.write(text.replace(old, new, 1))
        db, out, rc = _build_db(work)
        if rc != 0:
            print("  FAIL: container-sourced two-declarer composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        prj = projectOpen(db)
        parentKey = prj.getQualBlock('wrapBlk')
        pair = (parentKey, LEAF_KEY)
        view = prj.getRegistrarConfigView(LEAF_KEY, parentKey)
        descriptor = view['variantDescriptors']['v0']
        if descriptor['declaringProject'] != 'projWrap' \
                or not descriptor['containerSourced']:
            print(f"  FAIL: selected descriptor is {descriptor}")
            return False
        if prj.registrarPairs[pair]['hasModelRegistrations'] or view['hasRegistrations']:
            print("  FAIL: registrar classification ignored the selected "
                  "container-sourced descriptor")
            return False
        print("  PASS: config-context owner wins and suppresses the registrar")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_assembler_binding_outranks_other_projects():
    _header("assembler-owned container binding outranks config and block owners")
    work = _copy_fixture('param_two_declarers_assembler_')
    try:
        path = os.path.join(work, 'top', 'yaml', 'twoDeclarersTop.yaml')
        with open(path) as f:
            text = f.read()
        replacements = (
            (
                '    drv:\n'
                '        desc: "stimulus source on the wrapper\'s boundary interface"\n',
                '    consumerBlk:\n'
                '        desc: "assembler-owned direct consumer of the reused leaf"\n'
                '        params: [WRAP_W]\n'
                '    drv:\n'
                '        desc: "stimulus source on the wrapper\'s boundary interface"\n',
            ),
            (
                '    uWrap: { container: top, instanceType: wrapBlk, variant: v0 }\n',
                '    uWrap: { container: top, instanceType: wrapBlk, variant: v0 }\n'
                '    uConsumer: { container: top, instanceType: consumerBlk, variant: v0 }\n'
                '    uDirectLeaf: { container: consumerBlk, instanceType: leafIp, variant: v0 }\n',
            ),
            (
                '    drv:\n'
                '        v0:\n'
                '            WRAP_W: 8\n',
                '    drv:\n'
                '        v0:\n'
                '            WRAP_W: 8\n'
                '    consumerBlk:\n'
                '        v0:\n'
                '            WRAP_W: 8\n'
                '    leafIp:\n'
                '        v0:\n'
                '            LEAF_W: { containerParam: WRAP_W }\n',
            ),
        )
        for old, new in replacements:
            if old not in text:
                raise AssertionError(f"assembler fixture anchor is missing: {old!r}")
            text = text.replace(old, new, 1)
        with open(path, 'w') as f:
            f.write(text)
        db, out, rc = _build_db(work)
        if rc != 0:
            print("  FAIL: assembler-owned binding composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        prj = projectOpen(db)
        parentKey = prj.getQualBlock('consumerBlk')
        pair = (parentKey, LEAF_KEY)
        view = prj.getRegistrarConfigView(LEAF_KEY, parentKey)
        descriptor = view['variantDescriptors']['v0']
        if descriptor['declaringProject'] != 'twoDeclarersProj' \
                or not descriptor['containerSourced']:
            print(f"  FAIL: selected descriptor is {descriptor}")
            return False
        if prj.registrarPairs[pair]['hasModelRegistrations'] or view['hasRegistrations']:
            print("  FAIL: registrar classification ignored the assembler-owned "
                  "container binding")
            return False
        print("  PASS: assembler-owned descriptor wins and suppresses the registrar")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    print("\n" + "="*70)
    print("VARIANT DECLARER PRECEDENCE TESTS")
    print("="*70)

    tests = [
        test_config_context_owner_outranks_block_declarer,
        test_registrar_requirement_uses_config_owner_precedence,
        test_assembler_binding_outranks_other_projects,
    ]
    results = []
    for test_func in tests:
        try:
            results.append((test_func.__name__, test_func()))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    print("\n" + "="*70 + "\nTEST SUMMARY\n" + "="*70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    if passed == len(results):
        print("\n  ALL TESTS PASSED!")
        return 0
    print("\n  SOME TESTS FAILED")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
