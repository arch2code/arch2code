#!/usr/bin/env python3
"""Parameterized interface across INDEPENDENTLY PARAMETERIZED PROJECT boundaries.

The multi-project extension of `test_param_const_linkage.py`. That suite covers
parameter/interface linkage within one project, where every declaration shares
one file scope; this one composes three separately authored projects that each
declare their OWN same-named `WIDTH` ipParameters constant, their OWN same-named
parameterized interface `dataIf`, and their OWN parameterized block, plus an
assembler project that instantiates all three and wires A -> B -> C.

Fixture: `fixtures/param-cross-project`, copied into a temp tree per cell so the
generated build manifest never lands in the committed fixture. Five assembler
project files select five compositions over the same sub-projects.

Correct-by-design behavior (these cells must pass):
- Three same-named `WIDTH` constants are three distinct parameter identities
  (identity is the declaring-file qualified constant key), so wiring the
  parameterized interface straight through is REJECTED by the
  parameterized-endpoint validator. The exact diagnostic sentence is asserted, so
  any change to its wording - including fixing the fact that it reports a
  "missing" parameter the block demonstrably declares - is a deliberate, visible
  test change.
- The sanctioned de-parameterized boundary works across all three projects: the
  assembler owns a literal-width interface, each endpoint keeps its own
  parameterized interface, every leg is a cross-interface bind, and each bind
  resolves the endpoint's OWN project's interface.
- One shared declaration works across all three projects: the two downstream
  projects reach the upstream project's `WIDTH` and `dataIf` through a YAML
  `include:` instead of declaring their own, so all endpoints share one qualified
  constant key and the straight-through wiring is accepted.

Known-gap cells. Each asserts the DESIRED behavior and currently FAILS; the
failure is the record of the gap. No generator code is changed to make them pass.
- Two same-named interfaces owned by different projects with different payload
  forms are never reconciled, because cross-interface checking is entered only
  when the interface NAMES differ.
- A block port whose interface is declared in another file of its own project
  falls back to a whole-database bare-name interface scan, so first-match-wins
  binds the wrong project's interface - both in the declared-port resolution and
  in the cross-interface thunker payload it feeds.
- On the one working cross-project parameterized path (the shared `include:`), a
  variant binding that exceeds the backing constant's `maxValue` is accepted,
  because the sizing check reaches the backing constant through the block param's
  own file qualification rather than the resolved declaring file.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectOpen

FIXTURE = os.path.join(test_dir, 'fixtures', 'param-cross-project')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

# Context keys are whole paths relative to the assembler project file's
# directory, so each sub-project's declarations qualify to these exact strings.
A_CONTEXT = '../../projA/yaml/aTop.yaml'
B_CONTEXT = '../../projB/yaml/bTop.yaml'
C_CONTEXT = '../../projC/yaml/cTop.yaml'
B_SPLIT_IFACE_CONTEXT = '../../projBSplit/yaml/bSplitIfaces.yaml'


def _copy_fixture(prefix):
    """Copy the committed fixture into a fresh temp tree under unittest/ and
    return its path. Inside unittest/ so any scaffold path resolves the repo root
    the way a real project does."""
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
    return work


def _build_db(work, assemblerProject):
    """Build one composition from its assembler project file. Returns
    (db_path, combined output, returncode)."""
    db = os.path.join(work, 'param-cross-project.db')
    project = os.path.join(work, 'top', 'yaml', assemblerProject)
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, ARCH2CODE, '--yaml', project, '--db', db],
        capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
    return db, result.stdout + result.stderr, result.returncode


def _edit_fixture_yaml(work, relPath, old, new):
    """Apply one anchored replacement to a copied fixture file. Fails loudly if
    the anchor is absent, so a fixture edit can never silently no-op and leave a
    cell asserting against the unmodified topology."""
    path = os.path.join(work, relPath)
    with open(path) as f:
        text = f.read()
    if old not in text:
        raise AssertionError(f"fixture edit anchor not found in {relPath}: {old!r}")
    with open(path, 'w') as f:
        f.write(text.replace(old, new, 1))


def _close_db():
    if g.db is not None:
        g.db.close()
        g.db = None


def _cross_interface_ends(db):
    """Return {(instance, portName): end} for every cross-interface bind on the
    assembler top block."""
    prj = projectOpen(db)
    topKey = next(key for key, row in prj.data['blocks'].items()
                  if row['block'] == 'top')
    blockData = prj.getBlockData(topKey)
    ends = dict()
    for conn in blockData['connectDouble']['connections'].values():
        # The annotation is attached only to a connection that has at least one
        # cross-interface bind, so its absence means "no bind on this connection".
        for end in conn.get('crossInterfaceEnds', []):
            ends[(end['instance'], end['portName'])] = end
    return prj, ends


def _header(name):
    print(f"\n{'='*70}\nTest: {name}\n{'='*70}")


# ----------------------------------------------------------------------------
# Correct-by-design behavior.
# ----------------------------------------------------------------------------

def test_three_project_param_connection_rejected():
    _header("three same-named WIDTH identities reject the straight-through chain")
    work = _copy_fixture('param_xproj_chain_')
    try:
        _db, out, rc = _build_db(work, 'chainProject.yaml')
        if rc == 0:
            print("  FAIL: expected the three-project parameterized chain to be rejected")
            return False
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean error")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        # The exact current diagnostic. It reports 'missing WIDTH' for a block
        # that declares WIDTH: the mismatch is one of declaring-file/project
        # identity, which the message does not convey. Asserted verbatim so any
        # rewording is a deliberate change to this expectation.
        expected = (
            "Parameterized interface 'dataIf' on the connection 'uA' -> 'uB' connects "
            "endpoint instance 'uB' (block 'bIp'), which does not declare the required "
            "parameter(s): missing WIDTH. A block reached through a parameterized "
            "interface must itself carry the backing parameter(s) so the payload is "
            "sized in its own module scope.")
        if expected not in out:
            print("  FAIL: endpoint diagnostic text changed")
            print(f"  expected: {expected}")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        print("  PASS: chain rejected with the recorded endpoint diagnostic")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_deparameterized_boundary_across_three_projects():
    _header("assembler-owned literal boundary binds all three projects")
    work = _copy_fixture('param_xproj_boundary_')
    try:
        db, out, rc = _build_db(work, 'boundaryProject.yaml')
        if rc != 0:
            print("  FAIL: the de-parameterized boundary composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        # Every leg is a cross-interface bind onto the endpoint's OWN project's
        # interface, which is what lets three separately parameterized IPs meet.
        expected = {
            ('uA', 'out'): f'dataIf/{A_CONTEXT}',
            ('uB', 'in'):  f'dataIf/{B_CONTEXT}',
            ('uB', 'out'): f'dataIf/{B_CONTEXT}',
            ('uC', 'in'):  f'dataIf/{C_CONTEXT}',
        }
        _prj, ends = _cross_interface_ends(db)
        got = {key: end['childInterfaceKey'] for key, end in ends.items()}
        if got != expected:
            print(f"  FAIL: cross-interface binds {got}, expected {expected}")
            return False
        for key, end in ends.items():
            if end['parentInterface'] != 'boundaryIf':
                print(f"  FAIL: end {key} parent interface "
                      f"'{end['parentInterface']}', expected 'boundaryIf'")
                return False
            if not end['thunker']['payloads']:
                print(f"  FAIL: end {key} took the bind path with no thunker payload")
                return False
        print("  PASS: four cross-interface thunked ends, each on its own project's interface")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_shared_ipparameter_include_across_projects():
    _header("one shared WIDTH declaration reached by include: across three projects")
    work = _copy_fixture('param_xproj_shared_')
    try:
        db, out, rc = _build_db(work, 'sharedProject.yaml')
        if rc != 0:
            print("  FAIL: the shared-include composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        try:
            widths = [row['constantKey'] for row in conn.execute(
                "SELECT constantKey FROM constants WHERE constant = 'WIDTH'")]
            interfaces = [row['interfaceKey'] for row in conn.execute(
                "SELECT interfaceKey FROM interfaces WHERE interface = 'dataIf'")]
            blocks = sorted(row['block'] for row in conn.execute(
                "SELECT b.block AS block FROM blocksparams bp "
                "JOIN blocks b ON b.blockKey = bp.blockKey "
                "WHERE bp.param = 'WIDTH'"))
            chain = sorted((row['interfaceKey'], row['isParameterizable'])
                           for row in conn.execute(
                               "SELECT interfaceKey, isParameterizable "
                               "FROM connections"))
        finally:
            conn.close()
        # One declaration, so one parameter identity and one interface identity
        # for all three projects' endpoints - the reason this wiring is accepted
        # where the same wiring over three own-WIDTH projects is not.
        if widths != [f'WIDTH/{A_CONTEXT}']:
            print(f"  FAIL: expected the single upstream WIDTH declaration, got {widths}")
            return False
        if interfaces != [f'dataIf/{A_CONTEXT}']:
            print(f"  FAIL: expected the single upstream dataIf declaration, got {interfaces}")
            return False
        if blocks != ['aIp', 'bSharedIp', 'cSharedIp']:
            print(f"  FAIL: expected all three blocks to carry WIDTH, got {blocks}")
            return False
        # What is accepted here is the PARAMETERIZED straight-through chain. If
        # these connections stopped being classified parameterizable the cell
        # would still pass on the identity assertions above while no longer
        # exercising the path it exists to cover.
        if chain != [(f'dataIf/{A_CONTEXT}', 1), (f'dataIf/{A_CONTEXT}', 1)]:
            print(f"  FAIL: expected both chain connections to be classified "
                  f"parameterizable on the shared dataIf, got {chain}")
            return False
        print("  PASS: three projects, one shared parameter identity, chain accepted")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ----------------------------------------------------------------------------
# Known gaps: each cell asserts the DESIRED behavior.
# ----------------------------------------------------------------------------

def test_gap_cross_project_width_mismatch_detected():
    _header("GAP: cross-project same-named interfaces with different widths "
            "must be reconciled")
    work = _copy_fixture('param_xproj_collision_')
    try:
        # Pin the premise the way the bare-name cell pins its own, so fixture
        # drift can never be misread as the gap. Read from the fixture text
        # rather than the database, because the DESIRED outcome of this cell is
        # a rejected build, which leaves no database to inspect. Anchors: the
        # assembler declares its own interface under the sub-projects' name, its
        # payload is 32 bits, and both endpoints bind an 8-bit variant.
        premisePath = os.path.join(work, 'top', 'yaml', 'collisionTop.yaml')
        with open(premisePath) as f:
            premiseText = f.read()
        for anchor in ("wideT: { width: 32",
                       "interfaces:\n    dataIf:",
                       "structure: wideSt, structureType: data_t",
                       "    aIp:\n        v0:\n            WIDTH: 8",
                       "    cIp:\n        v0:\n            WIDTH: 8"):
            if anchor not in premiseText:
                print(f"  FAIL: collisionTop.yaml no longer states the premise "
                      f"this cell tests; missing anchor {anchor!r}")
                return False

        _db, out, rc = _build_db(work, 'collisionProject.yaml')
        # The assembler's own 32-bit dataIf is bound to two sub-project ports
        # whose same-named dataIf carries an 8-bit payload. The packed forms
        # disagree, so the composition must be rejected naming the bit widths.
        if rc == 0:
            print("  FAIL: a 32-bit assembler interface bound to 8-bit "
                  "sub-project ports of the same name built cleanly; the "
                  "cross-project packed-form mismatch was never checked")
            return False
        # The reconciliation diagnostic spells the schema field, '_bitWidth'.
        if '_bitWidth' not in out:
            print("  FAIL: build failed but not with the per-field _bitWidth "
                  "reconciliation diagnostic")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        print("  PASS: cross-project width mismatch reported")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_gap_bare_name_interface_binds_owning_project():
    _header("GAP: a port must bind its own project's interface, not the first "
            "same-named one")
    work = _copy_fixture('param_xproj_barename_')
    try:
        db, out, rc = _build_db(work, 'bareNameProject.yaml')
        if rc != 0:
            print("  FAIL: the bare-name composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        prj, ends = _cross_interface_ends(db)
        # Truth: the port row's foreign key was resolved in the block's own
        # scope at parse time, so the persisted interfaceKey names projBSplit's
        # interface. Every later resolution of the same port must agree with it.
        blockRow = next(row for row in prj.data['blocks'].values()
                        if row['block'] == 'bSplitIp')
        stored = blockRow['ports']['in']['interfaceKey']
        if stored != f'dataIf/{B_SPLIT_IFACE_CONTEXT}':
            print(f"  FAIL: fixture no longer resolves the port to projBSplit's "
                  f"interface at parse time (stored {stored})")
            return False

        # Two independent resolutions of that one port. Both are reported, so a
        # single run records the state of each.
        failures = []
        instanceKey = next(key for key, row in prj.data['instances'].items()
                           if row['instance'] == 'uB')
        resolved = prj.getBDDeclaredPortInterfaceKey(instanceKey, 'in')
        if resolved != stored:
            failures.append(f"declared-port resolution returned '{resolved}', "
                            f"expected the parse-time key '{stored}'")
        # The same resolution feeds the cross-interface thunker, so a wrong bind
        # spells the wrong project's payload structure in generated code.
        end = ends[('uB', 'in')]
        if end['childInterfaceKey'] != stored:
            failures.append(
                f"cross-interface bind used '{end['childInterfaceKey']}', "
                f"expected '{stored}'; the thunker payload is "
                f"{end['childStructures']}")
        if failures:
            for failure in failures:
                print(f"  FAIL: {failure}")
            return False
        print("  PASS: both resolutions bind the port's own project interface")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_gap_shared_include_binding_sizing_enforced():
    _header("GAP: an oversize variant binding must be rejected when the backing "
            "constant is reached by include:")
    work = _copy_fixture('param_xproj_sizing_')
    try:
        # WIDTH's maxValue is 32 and worst-case sizing is taken from it, so
        # binding 64 must be rejected exactly as it is for a same-file backing
        # constant (test_param_const_linkage.test_variant_binding_exceeds_maxvalue).
        _edit_fixture_yaml(
            work, os.path.join('top', 'yaml', 'sharedTop.yaml'),
            "    bSharedIp:\n        v0:\n            WIDTH: 8",
            "    bSharedIp:\n        v0:\n            WIDTH: 64")
        _db, out, rc = _build_db(work, 'sharedProject.yaml')
        if rc == 0:
            print("  FAIL: a variant binding of 64 against maxValue 32 built "
                  "cleanly; the sizing check is skipped whenever a block param's "
                  "backing ipParameters constant lives in an included file")
            return False
        if 'maxValue' not in out:
            print("  FAIL: build failed but not with the sizing diagnostic")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        print("  PASS: oversize binding rejected on the shared-include path")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING: parameterized interface across project boundaries")
    print("="*70)
    tests = [
        test_three_project_param_connection_rejected,
        test_deparameterized_boundary_across_three_projects,
        test_shared_ipparameter_include_across_projects,
        test_gap_cross_project_width_mismatch_detected,
        test_gap_bare_name_interface_binds_owning_project,
        test_gap_shared_include_binding_sizing_enforced,
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
