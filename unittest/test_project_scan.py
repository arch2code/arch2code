#!/usr/bin/env python3
"""Tier-1 scan-all reconcile proof for the projectOverride ownership engine.

Exercises the standalone pysrc/projectScan.py::ProjectScanner in isolation
(never wired into projectCreate). Three scenarios:

  * MULTI-COPY: an integrator references three sub-projects, each nesting its OWN
    physically distinct copy of a shared types-only project (same projectName),
    reached through normal include: edges, with a ROOT projectOverride selecting
    one copy as master. Asserts every copy's shared files map to the SAME logical
    key, the logical group has all members, master selection follows the
    override, ownership is reattributed to `shared` (not the including projects),
    non-master members alias onto the master's, and identical copies show no
    divergence.

  * DIVERGENCE: edit one copy's shared file; assert the copies still reconcile
    onto one logical key while their contents now differ. The scanner does not
    hash the closure - it compares parsed content only within a multi-copy
    logical group - so this test hashes the fixture files itself.

  * DIVERGENCE WARNING: the scanner warns only when the NON-MASTER copies
    disagree with each other; a difference against the master copy is expected
    development and stays debug-only, and a comment-only difference is not a
    difference at all.

  * SINGLE-COPY: the committed nested-ownership fixture (one copy per project).
    Asserts no spurious multi-copy grouping and that scanner ownership matches
    the live projectCreate attribution (parity for non-redirect cases).
"""

import contextlib
import hashlib
import io
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
from pysrc.projectScan import ProjectScanner
from pysrc.processYaml import projectOpen
import pysrc.yamlReadCache as yamlReadCache

MULTI_COPY = os.path.join(test_dir, 'fixtures', 'multi-copy')
NESTED = os.path.join(test_dir, 'fixtures', 'nested-ownership')
BARE_INCLUDE = os.path.join(test_dir, 'fixtures', 'bare-include')
CROSS_BRANCH = os.path.join(test_dir, 'fixtures', 'cross-branch-override')
CONFLICT = os.path.join(test_dir, 'fixtures', 'conflict-override')
TWO_DECLARERS = os.path.join(test_dir, 'fixtures',
                              'param-variant-two-declarers-legal')
SCAN_TIE = os.path.join(test_dir, 'fixtures', 'scan-ownership-tie')
ADDRGROUP_QUALIFICATION = os.path.join(test_dir, 'fixtures',
                                        'addrgroup-qualification')
PARAM_CROSS_PROJECT = os.path.join(test_dir, 'fixtures', 'param-cross-project')
IP_TEST = os.path.join(base_dir, 'examples', 'ip_test')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

SHARED = 'shared'
SUBA_SHARED_TYPES = '../../subA/shared/yaml/shared_types.yaml'
SUBB_SHARED_TYPES = '../../subB/shared/yaml/shared_types.yaml'
SUBC_SHARED_TYPES = '../../subC/shared/yaml/shared_types.yaml'
SUBA_SHARED_PROJECT = '../../subA/shared/yaml/sharedProject.yaml'
SUBB_SHARED_PROJECT = '../../subB/shared/yaml/sharedProject.yaml'
SUBC_SHARED_PROJECT = '../../subC/shared/yaml/sharedProject.yaml'
# subA's copy is the fixture's projectOverride master, so subB and subC are the
# non-master copies the divergence warning compares against each other.
TYPES_LOGICAL = (SHARED, 'yaml/shared_types.yaml')


def _scan_multi_copy(work):
    shutil.copytree(MULTI_COPY, work, dirs_exist_ok=True)
    proj = os.path.join(work, 'integrator', 'yaml', 'integratorProject.yaml')
    return work, ProjectScanner(proj).scan()


def _content_hash(work, physicalKey):
    """sha256 of the on-disk bytes of a scan physical key. Physical keys are
    relative to the root project file's directory, so the test resolves them
    itself rather than asking the scanner to hash every closure file on every
    build."""
    path = os.path.join(work, 'integrator', 'yaml', physicalKey)
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_multi_copy_reconcile():
    """Every distinct copy of `shared` reconciles onto one logical identity."""
    work = tempfile.mkdtemp(prefix='project_scan_mc_', dir=test_dir)
    try:
        work, result = _scan_multi_copy(work)

        # Every copy of shared_types maps to the SAME logical key (shared, <relpath>).
        keyA = result.logicalKey[SUBA_SHARED_TYPES]
        keyB = result.logicalKey[SUBB_SHARED_TYPES]
        keyC = result.logicalKey[SUBC_SHARED_TYPES]
        assert keyA == keyB == keyC == TYPES_LOGICAL, \
            f"copies did not share one logical key: {keyA}, {keyB}, {keyC}"

        # logicalGroups shows the 3-member group for that logical key.
        group = result.logicalGroups[TYPES_LOGICAL]
        assert sorted(group) == sorted([SUBA_SHARED_TYPES, SUBB_SHARED_TYPES,
                                        SUBC_SHARED_TYPES]), \
            f"unexpected logical group members: {group}"

        # The shared project file itself is also a 3-member group.
        projGroup = result.logicalGroups[(SHARED, 'yaml/sharedProject.yaml')]
        assert sorted(projGroup) == sorted(
            [SUBA_SHARED_PROJECT, SUBB_SHARED_PROJECT, SUBC_SHARED_PROJECT]), \
            f"unexpected shared-project group: {projGroup}"

        # masterByProject picks the ROOT-override-declared copy (subA's).
        expected_master = os.path.realpath(
            os.path.join(work, 'subA', 'shared'))
        assert os.path.realpath(result.masterByProject[SHARED]) == expected_master, \
            f"master root {result.masterByProject[SHARED]} != {expected_master}"

        # Ownership is REATTRIBUTED: EVERY copy's members are owned by `shared`,
        # never by the including subA / subB / subC projects.
        for member in (SUBA_SHARED_TYPES, SUBB_SHARED_TYPES, SUBC_SHARED_TYPES,
                       SUBA_SHARED_PROJECT, SUBB_SHARED_PROJECT,
                       SUBC_SHARED_PROJECT):
            assert result.ownership[member] == SHARED, \
                f"{member} owned by '{result.ownership[member]}', expected 'shared'"
        # The including projects still own their own non-shared members.
        assert result.ownership['../../subA/yaml/subALeaf.yaml'] == 'subA'
        assert result.ownership['../../subB/yaml/subBLeaf.yaml'] == 'subB'
        assert result.ownership['../../subC/yaml/subCLeaf.yaml'] == 'subC'
        assert result.ownership['integratorTop.yaml'] == 'integrator'

        # aliasMemberToMaster maps every NON-master (subB, subC) member onto the
        # master (subA) member, member-level (not just the provider project file).
        for member, master in ((SUBB_SHARED_TYPES, SUBA_SHARED_TYPES),
                               (SUBC_SHARED_TYPES, SUBA_SHARED_TYPES),
                               (SUBB_SHARED_PROJECT, SUBA_SHARED_PROJECT),
                               (SUBC_SHARED_PROJECT, SUBA_SHARED_PROJECT)):
            assert result.aliasMemberToMaster[member] == master, \
                f"alias wrong for {member}: {result.aliasMemberToMaster.get(member)}"
        # Master members are never aliased (they ARE the master).
        assert SUBA_SHARED_TYPES not in result.aliasMemberToMaster
        assert SUBA_SHARED_PROJECT not in result.aliasMemberToMaster

        # Identical content -> every member of each logical key agrees.
        for member in (SUBB_SHARED_TYPES, SUBC_SHARED_TYPES):
            assert _content_hash(work, SUBA_SHARED_TYPES) \
                == _content_hash(work, member), \
                f"byte-identical shared_types copies should hash equal: {member}"
        for member in (SUBB_SHARED_PROJECT, SUBC_SHARED_PROJECT):
            assert _content_hash(work, SUBA_SHARED_PROJECT) \
                == _content_hash(work, member), \
                f"byte-identical sharedProject copies should hash equal: {member}"

        print("PASS: multi-copy reconcile (logical key, group, master, "
              "ownership reattribution, member alias, no divergence)")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_divergence_detected():
    """After editing one copy, the logical key's members hash differently."""
    work = tempfile.mkdtemp(prefix='project_scan_div_', dir=test_dir)
    try:
        _scan_multi_copy(work)  # populate the temp tree
        # Diverge subB's copy of the shared types file.
        divergent = os.path.join(work, 'subB', 'shared', 'yaml', 'shared_types.yaml')
        with open(divergent, 'a') as f:
            f.write('\n    sharedExtra: { width: 4, desc: "skew introduced by subB copy" }\n')

        # The first scan cached the pre-edit bytes; drop the read-through cache so
        # the re-scan reads the now-divergent file fresh from disk.
        yamlReadCache.clear()
        proj = os.path.join(work, 'integrator', 'yaml', 'integratorProject.yaml')
        # Editing subB makes the two non-master copies disagree, so the scan
        # warns; captured here to keep the suite output clean (the warning itself
        # is asserted by test_divergence_warning_excludes_master).
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            result = ProjectScanner(proj).scan()
        assert 'differ from each other' in captured.getvalue(), \
            f"divergent non-master copies must warn: {captured.getvalue()}"

        # Still one logical group holding every copy...
        group = result.logicalGroups[TYPES_LOGICAL]
        assert sorted(group) == sorted([SUBA_SHARED_TYPES, SUBB_SHARED_TYPES,
                                        SUBC_SHARED_TYPES]), \
            f"divergent copies must still share one logical key: {group}"
        # ...but their content hashes now differ (the WARN signal).
        assert _content_hash(work, SUBA_SHARED_TYPES) \
            != _content_hash(work, SUBB_SHARED_TYPES), \
            "divergent copies of one logical key must hash differently"
        # The untouched sharedProject copies still agree.
        assert _content_hash(work, SUBA_SHARED_PROJECT) \
            == _content_hash(work, SUBB_SHARED_PROJECT), \
            "untouched copies should still agree"
        print("PASS: divergence detected (differing content hashes for one logical key)")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _scan_with_edit(prefix, sub, appended):
    """Scan a fresh copy of the multi-copy fixture after appending `appended` to
    `sub`'s copy of shared_types.yaml (no edit when `sub` is None), returning the
    scanner's captured output. Each case gets its own tree so the read-through
    byte cache never serves a pre-edit copy of an edited path."""
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    try:
        shutil.copytree(MULTI_COPY, work, dirs_exist_ok=True)
        if sub is not None:
            edited = os.path.join(work, sub, 'shared', 'yaml', 'shared_types.yaml')
            with open(edited, 'a') as f:
                f.write(appended)
        proj = os.path.join(work, 'integrator', 'yaml', 'integratorProject.yaml')
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            ProjectScanner(proj).scan()
        return captured.getvalue()
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_divergence_warning_excludes_master():
    """The scanner warns when the NON-MASTER copies of one logical file disagree
    with each other - each sub-project was then developed against different
    content of the same shared file, and the single master silently replaces all
    of them. A copy that differs only from the MASTER is expected (development
    happens in the master copy) and must NOT warn, and a comment-only difference
    is not a content difference at all."""
    typeDecl = '    sharedExtra: { width: 4, desc: "skew" }\n'

    clean = _scan_with_edit('project_scan_warn_clean_', None, '')
    assert 'differ from each other' not in clean, \
        f"identical copies must not warn: {clean}"

    # subB and subC are both non-master, so editing one makes them disagree.
    nonMaster = _scan_with_edit('project_scan_warn_copy_', 'subB', typeDecl)
    assert 'differ from each other' in nonMaster, \
        f"disagreeing non-master copies must warn: {nonMaster}"
    assert SUBB_SHARED_TYPES in nonMaster and SUBC_SHARED_TYPES in nonMaster, \
        f"warning must name the divergent copies: {nonMaster}"
    assert SUBA_SHARED_TYPES in nonMaster, \
        f"warning must name the master that replaces them: {nonMaster}"

    # subA is the master; the copies still agree with each other.
    master = _scan_with_edit('project_scan_warn_master_', 'subA', typeDecl)
    assert 'differ from each other' not in master, \
        f"a difference against the master copy must not warn: {master}"

    comment = _scan_with_edit('project_scan_warn_comment_', 'subB',
                              '# a copy-local comment\n')
    assert 'differ from each other' not in comment, \
        f"a comment-only difference must not warn: {comment}"

    print("PASS: divergence warns only when non-master copies disagree "
          "(master difference and comment-only difference stay quiet)")


def test_mistargeted_override_diagnostic():
    """A projectOverride pointing at a path that is not a discovered provider
    fails with a clear diagnostic naming the projectName and target, not a bare
    KeyError."""
    work = tempfile.mkdtemp(prefix='project_scan_bad_', dir=test_dir)
    try:
        shutil.copytree(MULTI_COPY, work, dirs_exist_ok=True)
        root = os.path.join(work, 'integrator', 'yaml', 'integratorProject.yaml')
        with open(root) as f:
            text = f.read()
        # Repoint the override at a path no projectFiles: slot reaches.
        text = text.replace(
            'shared: ../../subA/shared/yaml/sharedProject.yaml',
            'shared: ../../subA/shared/yaml/doesNotExist.yaml')
        with open(root, 'w') as f:
            f.write(text)

        try:
            ProjectScanner(root).scan()
        except ValueError as e:
            msg = str(e)
            assert 'shared' in msg and 'doesNotExist.yaml' in msg, \
                f"diagnostic did not name projectName and target: {msg}"
            print("PASS: mis-targeted override raises a clear diagnostic")
            return
        assert False, "mis-targeted override did not raise a diagnostic"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_single_copy_parity():
    """Single-copy composition: no spurious grouping; scanner ownership matches
    the live projectCreate attribution for every context it enumerates."""
    work = tempfile.mkdtemp(prefix='project_scan_sc_', dir=test_dir)
    try:
        shutil.copytree(NESTED, work, dirs_exist_ok=True)
        proj = os.path.join(work, 'root', 'yaml', 'rootProject.yaml')

        result = ProjectScanner(proj).scan()

        # No logical key groups more than one physical copy.
        multi = {lk: members for lk, members in result.logicalGroups.items()
                 if len(members) > 1}
        assert not multi, f"single-copy composition produced spurious groups: {multi}"
        # No member aliases (nothing to unify).
        assert not result.aliasMemberToMaster, \
            f"single-copy composition produced aliases: {result.aliasMemberToMaster}"

        # Build the live DB and compare ownership for every context the scanner
        # enumerated (the DB additionally owns system contexts the scan skips).
        db = os.path.join(work, 'nested-ownership.db')
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        build = subprocess.run(
            [sys.executable, ARCH2CODE, '--yaml', proj, '--db', db],
            capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
        assert build.returncode == 0, \
            f"nested-ownership db build failed:\n{build.stdout}\n{build.stderr}"

        prj = projectOpen(db)
        try:
            live = prj.contextOwningProject
            for ctx, owner in result.ownership.items():
                assert ctx in live, \
                    f"scanner context '{ctx}' absent from live ownership map"
                assert live[ctx] == owner, \
                    f"ownership parity mismatch for '{ctx}': scanner={owner}, live={live[ctx]}"
        finally:
            if g.db is not None:
                g.db.close()
                g.db = None
        print("PASS: single-copy parity (no spurious grouping; ownership matches live attribution)")
    finally:
        if g.db is not None:
            g.db.close()
            g.db = None
        shutil.rmtree(work, ignore_errors=True)


def test_bare_basename_include_key_parity():
    """A subdirectory file includes a root-level shared file by BARE basename,
    relying on getFileList's bare-basename retention (the file is already a known
    include dependency). Assert the scanner - which accumulates its own
    include-dependency map - keeps the same bare `shared.yaml` context key the
    live projectCreate parse does, rather than normalizing it to a sub/ relpath."""
    work = tempfile.mkdtemp(prefix='project_scan_bare_', dir=test_dir)
    try:
        shutil.copytree(BARE_INCLUDE, work, dirs_exist_ok=True)
        proj = os.path.join(work, 'prj', 'bareProject.yaml')

        result = ProjectScanner(proj).scan()

        # The scanner retained the bare key (bare-retention fired) and did NOT
        # emit the misresolved sub/ relpath key.
        assert 'shared.yaml' in result.ownership, \
            f"scanner did not key the bare include as 'shared.yaml': {sorted(result.ownership)}"
        assert 'sub/shared.yaml' not in result.ownership, \
            f"scanner misresolved the bare include to a sub/ relpath: {sorted(result.ownership)}"

        # Build the live DB and confirm identical keying for every context the
        # scanner enumerated (the DB additionally owns system contexts).
        db = os.path.join(work, 'bare-include.db')
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        build = subprocess.run(
            [sys.executable, ARCH2CODE, '--yaml', proj, '--db', db],
            capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
        assert build.returncode == 0, \
            f"bare-include db build failed:\n{build.stdout}\n{build.stderr}"

        prj = projectOpen(db)
        try:
            live = prj.contextOwningProject
            assert 'shared.yaml' in live, \
                f"live parse did not key the bare include as 'shared.yaml': {sorted(live)}"
            for ctx, owner in result.ownership.items():
                assert ctx in live, \
                    f"scanner context '{ctx}' absent from live ownership map"
                assert live[ctx] == owner, \
                    f"key/ownership parity mismatch for '{ctx}': scanner={owner}, live={live[ctx]}"
        finally:
            if g.db is not None:
                g.db.close()
                g.db = None
        print("PASS: bare-basename include key parity (scanner retains the same "
              "bare context key as the live parse)")
    finally:
        if g.db is not None:
            g.db.close()
            g.db = None
        shutil.rmtree(work, ignore_errors=True)


def test_cross_branch_override_master_discovered():
    """Fix 1: a master selected via the GLOBAL effective override map that the
    branch-local walk never reaches must still be discovered as a provider - the
    scan returns a valid ScanResult (no KeyError) with that target as master and
    every other copy aliased onto it."""
    work = tempfile.mkdtemp(prefix='project_scan_xbranch_', dir=test_dir)
    try:
        shutil.copytree(CROSS_BRANCH, work, dirs_exist_ok=True)
        proj = os.path.join(work, 'integrator', 'yaml', 'integratorProject.yaml')

        # Must not raise (pre-Fix-1 this KeyError'd on the undiscovered master).
        result = ProjectScanner(proj).scan()

        vendor_types = '../../vendor/shared/yaml/shared_types.yaml'
        vendor_project = '../../vendor/shared/yaml/sharedProject.yaml'
        subb_types = '../../subB/shared/yaml/shared_types.yaml'
        subb_project = '../../subB/shared/yaml/sharedProject.yaml'

        # The globally-selected vendor copy is the master for `shared`.
        expected_master = os.path.realpath(
            os.path.join(work, 'vendor', 'shared'))
        assert os.path.realpath(result.masterByProject[SHARED]) == expected_master, \
            f"master root {result.masterByProject[SHARED]} != {expected_master}"

        # Both physical copies of each shared file reconcile onto one logical key.
        assert result.logicalKey[vendor_types] == result.logicalKey[subb_types] \
            == (SHARED, 'yaml/shared_types.yaml'), \
            "vendor and subB shared_types did not share one logical key"
        assert result.logicalKey[vendor_project] == result.logicalKey[subb_project] \
            == (SHARED, 'yaml/sharedProject.yaml'), \
            "vendor and subB sharedProject did not share one logical key"

        # The branch-local (subB) copies alias onto the vendor master's members;
        # the master members are never aliased.
        assert result.aliasMemberToMaster[subb_types] == vendor_types, \
            f"subB shared_types alias wrong: {result.aliasMemberToMaster.get(subb_types)}"
        assert result.aliasMemberToMaster[subb_project] == vendor_project, \
            f"subB sharedProject alias wrong: {result.aliasMemberToMaster.get(subb_project)}"
        assert vendor_types not in result.aliasMemberToMaster
        assert vendor_project not in result.aliasMemberToMaster

        # Both copies' members are reattributed to `shared`.
        for member in (vendor_types, vendor_project, subb_types, subb_project):
            assert result.ownership[member] == SHARED, \
                f"{member} owned by '{result.ownership[member]}', expected 'shared'"

        print("PASS: cross-branch override master discovered (global-effective "
              "master scanned, copies aliased, no KeyError)")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_conflicting_sibling_overrides_fail_loud():
    """Fix 2: two non-dominating sibling projects at the same nesting depth that
    redirect one projectName to DIFFERENT targets is contradictory and must raise
    a clear conflict diagnostic naming the projectName and both targets, not
    silently keep the first-folded one."""
    work = tempfile.mkdtemp(prefix='project_scan_conflict_', dir=test_dir)
    try:
        shutil.copytree(CONFLICT, work, dirs_exist_ok=True)
        proj = os.path.join(work, 'integrator', 'yaml', 'integratorProject.yaml')

        try:
            ProjectScanner(proj).scan()
        except ValueError as e:
            msg = str(e)
            assert 'shared' in msg, f"conflict diagnostic omits projectName: {msg}"
            assert 'subA' in msg and 'subB' in msg, \
                f"conflict diagnostic did not name both conflicting targets: {msg}"
            print("PASS: conflicting sibling overrides fail loud (clear conflict "
                  "diagnostic, no silent first-win)")
            return
        assert False, "conflicting sibling overrides did not raise a diagnostic"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_two_declarers_longest_path_ownership():
    """A root that lists both a wrapper project and the IP project the
    wrapper itself lists is a diamond: the IP's leaf is reachable directly
    from the root AND, one level deeper, through the wrapper. Ownership must
    follow the LONGEST path, so the leaf's own author (projIp) owns it, not
    whichever provider the walk reaches first."""
    result = ProjectScanner(
        os.path.join(TWO_DECLARERS, 'top', 'yaml',
                     'twoDeclarersLegalProject.yaml')).scan()
    leaf = '../../projIp/yaml/leafIp.yaml'
    assert result.ownership[leaf] == 'projIp', \
        f"leafIp.yaml owned by '{result.ownership[leaf]}', expected 'projIp'"
    wrapTop = '../../projWrap/yaml/wrapTop.yaml'
    assert result.ownership[wrapTop] == 'projWrap', \
        f"wrapTop.yaml owned by '{result.ownership[wrapTop]}', expected 'projWrap'"
    print("PASS: two-declarers longest-path ownership (leaf owned by its "
          "deeper author, not the shallower co-declarer)")


def test_addrgroup_qualification_shared_types_direct_listing():
    """Shipped shape: the root lists `common` and its sibling consumers
    (childA, childB) directly; common lists sharedTypes.yaml directly in its
    own projectFiles:, so rule 1 gives it to common outright even though the
    consumers reach it only through include:."""
    result = ProjectScanner(
        os.path.join(ADDRGROUP_QUALIFICATION, 'root', 'yaml',
                     'rootProject.yaml')).scan()
    sharedTypes = '../../common/yaml/sharedTypes.yaml'
    assert result.ownership[sharedTypes] == 'commonProj', \
        (f"sharedTypes.yaml owned by '{result.ownership[sharedTypes]}', "
         f"expected 'commonProj'")
    print("PASS: addrgroup-qualification shared types ownership (direct "
          "projectFiles: listing wins over include:-only siblings)")


def test_param_cross_project_shared_owner_direct_listing():
    """Shipped shape: the root lists projA and its sibling consumers
    (projBShared, projCShared) directly; projA lists aTop.yaml directly in
    its own projectFiles:, so rule 1 gives it to projA outright even though
    the consumers reach it only through include:."""
    result = ProjectScanner(
        os.path.join(PARAM_CROSS_PROJECT, 'top', 'yaml',
                     'sharedProject.yaml')).scan()
    aTop = '../../projA/yaml/aTop.yaml'
    assert result.ownership[aTop] == 'projA', \
        f"aTop.yaml owned by '{result.ownership[aTop]}', expected 'projA'"
    print("PASS: param-cross-project shared owner ownership (direct "
          "projectFiles: listing wins over include:-only siblings)")


def test_ownership_tie_fails_loud():
    """Two unrelated projects (projA, projB) both include one shared
    definitions file that neither owns and neither lists the other: both
    reach it at the same depth, so there is no way to rank one above the
    other. Must raise, naming the file, both providers, and projectFiles: as
    the way to resolve it."""
    try:
        ProjectScanner(
            os.path.join(SCAN_TIE, 'top', 'yaml', 'tieProject.yaml')).scan()
    except ValueError as e:
        msg = str(e)
        assert 'sharedDefs.yaml' in msg, \
            f"tie diagnostic omits the shared file: {msg}"
        assert 'projAProject.yaml' in msg and 'projBProject.yaml' in msg, \
            f"tie diagnostic did not name both tied providers: {msg}"
        assert 'projectFiles' in msg, \
            f"tie diagnostic omits the projectFiles: resolution: {msg}"
        print("PASS: ownership tie fails loud (names the file, both "
              "providers, and the projectFiles: resolution)")
        return
    assert False, "ownership tie did not raise a diagnostic"


def test_ownership_tie_resolved_by_direct_listing():
    """Rule 1's own resolution: projA lists the shared file directly in its
    own projectFiles: (no dependency on projB, no separate shared project
    needed). The file then belongs to projA outright and the scan
    succeeds."""
    work = tempfile.mkdtemp(prefix='project_scan_tie_resolved_', dir=test_dir)
    try:
        shutil.copytree(SCAN_TIE, work, dirs_exist_ok=True)
        projA = os.path.join(work, 'projA', 'yaml', 'projAProject.yaml')
        with open(projA) as f:
            text = f.read()
        text = text.replace(
            'projectFiles:\n    - projALeaf.yaml',
            'projectFiles:\n    - projALeaf.yaml\n'
            '    - ../../shared/yaml/sharedDefs.yaml')
        with open(projA, 'w') as f:
            f.write(text)

        proj = os.path.join(work, 'top', 'yaml', 'tieProject.yaml')
        result = ProjectScanner(proj).scan()

        sharedDefs = '../../shared/yaml/sharedDefs.yaml'
        assert result.ownership[sharedDefs] == 'projA', \
            (f"sharedDefs.yaml owned by '{result.ownership[sharedDefs]}', "
             f"expected 'projA'")
        print("PASS: ownership tie resolved (direct projectFiles: listing "
              "gives the file one owner outright)")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_ownership_direct_listing_conflict_fails_loud():
    """Rule 1's own conflict: BOTH projA and projB list the shared file
    directly in their own projectFiles:. Two owners claiming one file
    directly is unresolvable and must raise, naming the file and both
    provider files."""
    work = tempfile.mkdtemp(prefix='project_scan_direct_conflict_',
                             dir=test_dir)
    try:
        shutil.copytree(SCAN_TIE, work, dirs_exist_ok=True)
        for leaf in ('projAProject.yaml', 'projBProject.yaml'):
            path = os.path.join(work, leaf.replace('Project.yaml', ''),
                                 'yaml', leaf)
            with open(path) as f:
                text = f.read()
            text = text.replace(
                'projectFiles:\n    -',
                'projectFiles:\n    - ../../shared/yaml/sharedDefs.yaml\n    -',
                1)
            with open(path, 'w') as f:
                f.write(text)

        proj = os.path.join(work, 'top', 'yaml', 'tieProject.yaml')
        try:
            ProjectScanner(proj).scan()
        except ValueError as e:
            msg = str(e)
            assert 'sharedDefs.yaml' in msg, \
                f"direct-listing conflict omits the shared file: {msg}"
            assert 'projAProject.yaml' in msg and 'projBProject.yaml' in msg, \
                f"direct-listing conflict did not name both providers: {msg}"
            print("PASS: direct-listing conflict fails loud (names the "
                  "file and both providers)")
            return
        assert False, "direct-listing conflict did not raise a diagnostic"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_ownership_cycle_fails_loud():
    """projA listing projB's project file and projB listing projA's back is a
    projectFiles: reference cycle, an authoring error. Must raise, naming
    both provider files and the word 'cycle'."""
    work = tempfile.mkdtemp(prefix='project_scan_cycle_', dir=test_dir)
    try:
        shutil.copytree(SCAN_TIE, work, dirs_exist_ok=True)
        projA = os.path.join(work, 'projA', 'yaml', 'projAProject.yaml')
        projB = os.path.join(work, 'projB', 'yaml', 'projBProject.yaml')
        with open(projA) as f:
            text = f.read()
        text = text.replace(
            'projectFiles:\n    - projALeaf.yaml',
            'projectFiles:\n    - projALeaf.yaml\n'
            '    - ../../projB/yaml/projBProject.yaml')
        with open(projA, 'w') as f:
            f.write(text)
        with open(projB) as f:
            text = f.read()
        text = text.replace(
            'projectFiles:\n    - projBLeaf.yaml',
            'projectFiles:\n    - projBLeaf.yaml\n'
            '    - ../../projA/yaml/projAProject.yaml')
        with open(projB, 'w') as f:
            f.write(text)

        proj = os.path.join(work, 'top', 'yaml', 'tieProject.yaml')
        try:
            ProjectScanner(proj).scan()
        except ValueError as e:
            msg = str(e)
            assert 'cycle' in msg, f"cycle diagnostic omits 'cycle': {msg}"
            assert 'projAProject.yaml' in msg and 'projBProject.yaml' in msg, \
                f"cycle diagnostic did not name both provider files: {msg}"
            print("PASS: projectFiles: reference cycle fails loud (names "
                  "both provider files)")
            return
        assert False, "projectFiles: reference cycle did not raise a diagnostic"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_ip_test_composed_scan():
    """The remaining tie, ruled 2026-09-14: the composed ip_test root reaches
    real ip.yaml/ipVariants.yaml both directly (root's own ip provider) and
    through ipBridge's vendored ip' copy, redirected onto the root's
    projectOverride master. Ranking a dependency on ip' as a dependency on
    its master too gives ip depth 2 through ipBridge, so ip ranks below
    ipBridge and owns its own files instead of tying with it. The two
    standalone sub-project roots must still scan cleanly on their own."""
    result = ProjectScanner(
        os.path.join(IP_TEST, 'prj', 'yaml', 'ip_testProject.yaml')).scan()
    ip = '../../ip/yaml/ip.yaml'
    ipVariants = '../../ip/yaml/ipVariants.yaml'
    cpu = '../../common/cpu/yaml/cpu.yaml'
    assert result.ownership[ip] == 'ip', \
        f"ip.yaml owned by '{result.ownership[ip]}', expected 'ip'"
    assert result.ownership[ipVariants] == 'ip', \
        (f"ipVariants.yaml owned by '{result.ownership[ipVariants]}', "
         f"expected 'ip'")
    assert result.ownership[cpu] == 'common', \
        f"cpu.yaml owned by '{result.ownership[cpu]}', expected 'common'"

    ProjectScanner(
        os.path.join(IP_TEST, 'ip', 'prj', 'yaml', 'ipProject.yaml')).scan()
    ProjectScanner(
        os.path.join(IP_TEST, 'bridge', 'prj', 'yaml',
                     'ipBridgeProject.yaml')).scan()
    print("PASS: composed ip_test scan succeeds (ip ranks below ipBridge "
          "through the master edge, both standalone roots scan too)")


def test_master_edge_ranking_cycle_fails_loud():
    """A dependency on any copy of a project also ranks that project's
    override-selected master, so relax() walks that rank-augmented edge too.
    A master edge can close a cycle the reference graph alone did not have:
    projA lists projB, projB lists a second copy of projA, and the root's
    projectOverrides selects the real projA as that copy's master, so the
    master edge redirects back onto projA itself. Must raise, naming
    'cycle', not hang. The second copy is a plain file rather than a symlink
    onto projA (as ip_test vendors ip): symlinking the whole projA directory
    would share projA's real content, including the new projA -> projB
    entry, which would then resolve from the copy's nested depth and 404."""
    work = tempfile.mkdtemp(prefix='project_scan_rankcycle_', dir=test_dir)
    try:
        shutil.copytree(SCAN_TIE, work, dirs_exist_ok=True)
        top = os.path.join(work, 'top', 'yaml', 'tieProject.yaml')
        with open(top, 'a') as f:
            f.write('\nprojectOverrides:\n'
                    '    projA: ../../projA/yaml/projAProject.yaml\n')

        projA = os.path.join(work, 'projA', 'yaml', 'projAProject.yaml')
        with open(projA) as f:
            text = f.read()
        text = text.replace(
            'projectFiles:\n    - projALeaf.yaml',
            'projectFiles:\n    - projALeaf.yaml\n'
            '    - ../../projB/yaml/projBProject.yaml')
        with open(projA, 'w') as f:
            f.write(text)

        projB = os.path.join(work, 'projB', 'yaml', 'projBProject.yaml')
        with open(projB) as f:
            text = f.read()
        text = text.replace(
            'projectFiles:\n    - projBLeaf.yaml',
            'projectFiles:\n    - projBLeaf.yaml\n'
            '    - ../vendored/yaml/projAProject.yaml')
        with open(projB, 'w') as f:
            f.write(text)

        vendoredDir = os.path.join(work, 'projB', 'vendored', 'yaml')
        os.makedirs(vendoredDir)
        with open(os.path.join(vendoredDir, 'projAProject.yaml'), 'w') as f:
            f.write('projectName: projA\n'
                    'dirs:\n    root: ..\n'
                    'fileGeneration:\n    template: none\n')

        proj = os.path.join(work, 'top', 'yaml', 'tieProject.yaml')
        try:
            ProjectScanner(proj).scan()
        except ValueError as e:
            msg = str(e)
            assert 'cycle' in msg, \
                f"rank-cycle diagnostic omits 'cycle': {msg}"
            print("PASS: master-edge ranking cycle fails loud (names "
                  "'cycle', does not hang)")
            return
        assert False, "master-edge ranking cycle did not raise a diagnostic"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    test_multi_copy_reconcile()
    test_divergence_detected()
    test_divergence_warning_excludes_master()
    test_mistargeted_override_diagnostic()
    test_single_copy_parity()
    test_bare_basename_include_key_parity()
    test_cross_branch_override_master_discovered()
    test_conflicting_sibling_overrides_fail_loud()
    test_two_declarers_longest_path_ownership()
    test_addrgroup_qualification_shared_types_direct_listing()
    test_param_cross_project_shared_owner_direct_listing()
    test_ownership_tie_fails_loud()
    test_ownership_tie_resolved_by_direct_listing()
    test_ownership_direct_listing_conflict_fails_loud()
    test_ownership_cycle_fails_loud()
    test_ip_test_composed_scan()
    test_master_edge_ranking_cycle_fails_loud()
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
