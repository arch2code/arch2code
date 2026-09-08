#!/usr/bin/env python3
"""Parameter/interface linkage across independently parameterized projects:
the multi-project extension of test_param_const_linkage.py, composing three
projects that each declare their own same-named WIDTH constant, dataIf
interface, and block, wired A -> B -> C.

Pins that parameter identity is the declaring-file qualified constant key,
never the bare name: a same-named declaration elsewhere does not satisfy an
endpoint, and two same-named interfaces from different projects are adapted rather than bound."""

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
from pysrc.intf_gen_utils import cpp_config_struct_name
from pysrc.processYaml import projectOpen

FIXTURE = os.path.join(test_dir, 'fixtures', 'param-cross-project')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

# Context keys are whole paths relative to the assembler project file's
# directory, so each sub-project's declarations qualify to these exact strings.
A_CONTEXT = '../../projA/yaml/aTop.yaml'
B_CONTEXT = '../../projB/yaml/bTop.yaml'
C_CONTEXT = '../../projC/yaml/cTop.yaml'
B_SPLIT_IFACE_CONTEXT = '../../projBSplit/yaml/bSplitIfaces.yaml'
# The assembler's own declarations sit beside the project file it is selected by,
# so they qualify to the bare file name.
COLLISION_CONTEXT = 'collisionTop.yaml'


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

def test_adapted_endpoint_exempt_from_parameter_rule():
    _header("an endpoint on its own project's declaration is adapted, so the "
            "parameterized-endpoint rule does not reach it")
    work = _copy_fixture('param_xproj_adapted_')
    try:
        db, out, rc = _build_db(work, 'adaptedProject.yaml')
        # projA and projC each declare their own WIDTH and their own same-named
        # dataIf, so uC's port is a different declaration from the connection's
        # and carries a different parameter identity. uC is adapted onto its own
        # declaration and never names projA's WIDTH, so requiring it to carry
        # projA's parameter identity rejects a design that is correct. Before the
        # rule was scoped to same-key endpoints this composition failed with
        # "does not declare the required parameter(s): missing WIDTH" against a
        # block that declares a WIDTH.
        if rc != 0:
            print("  FAIL: an adapted endpoint was still required to carry the "
                  "connection interface's parameter identity")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        _prj, ends = _cross_interface_ends(db)
        # uA's port IS the connection's declaration, so it binds directly and
        # must NOT appear. This cell pins the exemption only; that the rule still
        # fires on the endpoints it does reach is pinned by the rejection cell
        # below, which is what a deletion of the rule would fail.
        if sorted(ends) != [('uC', 'in')]:
            print(f"  FAIL: adapted ends {sorted(ends)}, expected uC's end only")
            return False
        end = ends[('uC', 'in')]
        if (end['parentInterfaceKey'], end['childInterfaceKey']) != (
                f'dataIf/{A_CONTEXT}', f'dataIf/{C_CONTEXT}'):
            print(f"  FAIL: fixture no longer states the premise this cell tests; "
                  f"uC binds {end['parentInterfaceKey']} to "
                  f"{end['childInterfaceKey']} rather than two same-named "
                  f"declarations")
            return False
        payloads = [(payload['side'], payload['structureKey'])
                    for payload in end['thunker']['payloads']]
        if payloads != [('parent', f'dataSt/{A_CONTEXT}'),
                        ('child', f'dataSt/{C_CONTEXT}')]:
            print(f"  FAIL: uC adapter payloads {payloads}")
            return False
        print("  PASS: adapted endpoint exempt, same-key endpoint still bound "
              "directly")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_same_key_endpoint_with_foreign_same_named_param_rejected():
    _header("a block's own file redeclaring a name its include chain already "
            "reaches is rejected by rule 2, naming both declaring files")
    work = _copy_fixture('param_xproj_samename_param_')
    try:
        # Give projBShared its own WIDTH beside the included one, so bSharedTop.yaml
        # sees two visible declarations and is rejected before the endpoint check.
        _edit_fixture_yaml(
            work, os.path.join('projBShared', 'yaml', 'bSharedTop.yaml'),
            "include:\n    - ../../projA/yaml/aTop.yaml\n",
            "include:\n    - ../../projA/yaml/aTop.yaml\n"
            "\n"
            "ipParameters:\n"
            "    constants:\n"
            "        WIDTH: { value: 8, maxValue: 32, desc: \"projBShared's own "
            "same-named width\" }\n")
        _db, out, rc = _build_db(work, 'sharedProject.yaml')
        if rc == 0:
            print("  FAIL: expected rule 2 to reject the redeclaration, "
                  "build succeeded")
            return False
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean error")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        missing = [p for p in ('bSharedIp', 'WIDTH', 'more than one visible declaration',
                                'bSharedTop.yaml', 'aTop.yaml')
                   if p not in out]
        if missing:
            print(f"  FAIL: expected patterns not found: {missing}")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        print("  PASS: rule 2 rejected the redeclaration, naming both files")
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


def test_same_named_cross_project_interfaces_are_adapted():
    _header("two same-named interfaces owned by different projects are adapted, "
            "not bound")
    work = _copy_fixture('param_xproj_samename_')
    try:
        # The collision topology at a width both sides agree on. The assembler
        # still declares its OWN interface named dataIf carrying its own payload
        # structure, and both endpoints still carry their own same-named dataIf;
        # only the packed forms now match, so the composition is accepted and the
        # question becomes how the two declarations meet in emitted code.
        _edit_fixture_yaml(
            work, os.path.join('top', 'yaml', 'collisionTop.yaml'),
            'wideT: { width: 32, desc: "assembler-owned 32-bit boundary word" }',
            'wideT: { width: 8, desc: "assembler-owned boundary word, '
            'layout-compatible with both endpoints" }')
        db, out, rc = _build_db(work, 'collisionProject.yaml')
        if rc != 0:
            print("  FAIL: the layout-compatible same-name composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        _prj, ends = _cross_interface_ends(db)
        # Each endpoint's declared interface is a different declaration from the
        # connection's, so each end must be adapted. Sharing the bare name is
        # what makes this cell distinct: an adapter decision taken on names alone
        # cannot see either end.
        expected = {
            ('uA', 'out'): A_CONTEXT,
            ('uC', 'in'):  C_CONTEXT,
        }
        got = {key: end['childInterfaceKey'] for key, end in ends.items()}
        want = {key: f'dataIf/{context}' for key, context in expected.items()}
        if got != want:
            print(f"  FAIL: cross-interface binds {got}, expected {want}")
            return False
        for key, end in ends.items():
            if (end['parentInterface'], end['childInterface']) != ('dataIf', 'dataIf'):
                print(f"  FAIL: fixture no longer states the premise this cell "
                      f"tests; end {key} binds '{end['parentInterface']}' to "
                      f"'{end['childInterface']}' rather than one shared name")
                return False
            if end['parentInterfaceKey'] != f'dataIf/{COLLISION_CONTEXT}':
                print(f"  FAIL: end {key} parent interface resolved to "
                      f"{end['parentInterfaceKey']}, expected the assembler's own")
                return False
            # The adapter must carry the assembler's declaration on the up side
            # and the endpoint's own on the down side; naming one of them twice
            # would emit a cast between a type and itself and drop the other.
            payloads = [(payload['side'], payload['structureKey'])
                        for payload in end['thunker']['payloads']]
            if payloads != [('parent', f'wideSt/{COLLISION_CONTEXT}'),
                            ('child', f'dataSt/{expected[key]}')]:
                print(f"  FAIL: end {key} adapter payloads {payloads}")
                return False
        print("  PASS: both same-named cross-project ends adapted on their own "
              "project's declaration")
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


def test_one_interface_at_differing_configs_is_adapted():
    _header("one shared interface declaration reached at three Configs is "
            "adapted where the Configs differ")
    work = _copy_fixture('param_xproj_config_')
    try:
        # The accepted straight-through chain of the cell above, read for what it
        # emits rather than for what it accepts. All four endpoint ports are the
        # one upstream dataIf declaration, so no interface difference exists at
        # any of them; but each block owns its params and so carries its own
        # Config, which makes the payload a different C++ type per endpoint.
        db, out, rc = _build_db(work, 'sharedProject.yaml')
        if rc != 0:
            print("  FAIL: the shared-include composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        _prj, ends = _cross_interface_ends(db)
        # The channel takes the dst endpoint's Config, so the dst end of each hop
        # binds it unadapted and only the src end is adapted. Adapting both would
        # leave the channel with no end to take its typing from.
        if sorted(ends) != [('uA', 'out'), ('uB', 'out')]:
            print(f"  FAIL: adapted ends {sorted(ends)}, expected the two "
                  f"producer ends only")
            return False
        # Each adapter's up side must spell the Config of the endpoint that types
        # the channel and its down side the adapted endpoint's own, so this pins
        # the emitted C++ names rather than restating the predicate that chose
        # them. Every variant here is declared by the assembler, so each name is
        # owner-qualified with its project.
        expected = {
            ('uA', 'out'): ('sharedTopProj_bSharedIpV0Config',
                            'sharedTopProj_aIpV0Config'),
            ('uB', 'out'): ('sharedTopProj_cSharedIpV0Config',
                            'sharedTopProj_bSharedIpV0Config'),
        }
        for key, end in ends.items():
            if end['parentInterfaceKey'] != f'dataIf/{A_CONTEXT}' \
                    or end['childInterfaceKey'] != f'dataIf/{A_CONTEXT}':
                print(f"  FAIL: fixture no longer states the premise this cell "
                      f"tests; end {key} binds {end['parentInterfaceKey']} to "
                      f"{end['childInterfaceKey']} rather than one declaration")
                return False
            configs = [(cpp_config_struct_name(pair['parent']['configSelection']),
                        cpp_config_struct_name(pair['child']['configSelection']))
                       for pair in end['thunker']['payloadPairs']]
            if configs != [expected[key]]:
                print(f"  FAIL: end {key} adapter Configs {configs}, expected "
                      f"{[expected[key]]}")
                return False
        print("  PASS: one declaration at differing Configs adapted on the "
              "producer end of each hop")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


# ----------------------------------------------------------------------------
# Reconciliation and resolution rules.
# ----------------------------------------------------------------------------

def test_cross_project_width_mismatch_rejected():
    _header("cross-project same-named interfaces with different widths are "
            "rejected")
    work = _copy_fixture('param_xproj_collision_')
    try:
        # Pin the premise from the fixture text rather than the database, because
        # this cell requires a rejected build and a rejected build leaves no
        # database to inspect. Anchors: the assembler declares its own interface
        # under the sub-projects' name, its payload is 32 bits, and both endpoints
        # bind an 8-bit variant.
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
        # aIp belongs to projA but its v0 binding of WIDTH is authored by the
        # assembler, so the side identity must send the reader to the assembler's
        # file. Naming only the block's own project points at a file that does
        # not hold the number.
        attribution = ("    parameter WIDTH = 8 comes from project "
                       "collisionTopProj (file collisionTop.yaml)")
        if attribution not in out:
            print("  FAIL: the rejected width was not attributed to the project "
                  "that declares it")
            print(f"  expected: {attribution}")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        print("  PASS: cross-project width mismatch reported and attributed")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_port_binds_its_own_project_interface():
    _header("a port binds its own project's interface, not the first same-named "
            "one")
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


def test_shared_include_binding_sizing_enforced():
    _header("an oversize variant binding is rejected when the backing constant "
            "is reached by include:")
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


def test_registrar_requirements_exclude_unreachable_child_harnesses():
    _header("registrar requirements contain only the active composition")
    work = _copy_fixture('param_xproj_registrar_reach_')
    try:
        # harness0 rather than v0: uHarnessLeaf sits in aTop.yaml, which cannot
        # see v0's declaration in the downstream adaptedTop.yaml.
        childArch = os.path.join(work, 'projA', 'yaml', 'aTop.yaml')
        with open(childArch, 'a') as f:
            f.write("""
    aHarness:
        desc: "Referenced-project standalone harness outside the active top"

instances:
    uHarnessLeaf: { container: aHarness, instanceType: aIp, variant: harness0 }

parameters:
    aIp:
        harness0:
            WIDTH: 8
""")
        db, out, rc = _build_db(work, 'adaptedProject.yaml')
        if rc != 0:
            print("  FAIL: composition did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        prj = projectOpen(db)
        expected = {
            (row['containerKey'], row['instanceTypeKey'])
            for instanceKey, row in prj.data['instances'].items()
            if instanceKey in prj.reachableInstances
            and row['containerKey'] in prj.data['blocks']
        }
        unreachable = {
            (row['containerKey'], row['instanceTypeKey'])
            for instanceKey, row in prj.data['instances'].items()
            if instanceKey not in prj.reachableInstances
            and row['containerKey'] in prj.data['blocks']
        }
        actual = set(prj.registrarPairs)
        if not unreachable:
            print("  FAIL: fixture no longer contains a referenced-project "
                  "standalone harness")
            return False
        if actual != expected:
            print(f"  FAIL: persisted pairs {sorted(actual)}, expected "
                  f"{sorted(expected)}")
            return False
        if actual & unreachable:
            print(f"  FAIL: unreachable pairs leaked into requirements: "
                  f"{sorted(actual & unreachable)}")
            return False
        print(f"  PASS: excluded {len(unreachable)} unreachable pair(s)")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING: parameterized interface across project boundaries")
    print("="*70)
    tests = [
        test_adapted_endpoint_exempt_from_parameter_rule,
        test_same_key_endpoint_with_foreign_same_named_param_rejected,
        test_deparameterized_boundary_across_three_projects,
        test_same_named_cross_project_interfaces_are_adapted,
        test_shared_ipparameter_include_across_projects,
        test_one_interface_at_differing_configs_is_adapted,
        test_cross_project_width_mismatch_rejected,
        test_port_binds_its_own_project_interface,
        test_shared_include_binding_sizing_enforced,
        test_registrar_requirements_exclude_unreachable_child_harnesses,
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
