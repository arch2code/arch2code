#!/usr/bin/env python3
"""Ownership classifier + absolute-ownership gate proof for the M-split.

Builds the committed `fixtures/nested-ownership` two-project fixture into a
temporary database and asserts that per-context ownership is NON-UNIFORM:

  * the child PROJECT file (reached through the root's projectFiles: slot and
    carrying the projectName/dirs/fileGeneration sentinel set) and everything in
    its transitive closure are owned by the child projectName;
  * everything reached through the root's own closure stays root-owned.

It also proves the strict invariant that a project file may only be reached
through the projectFiles: slot: referencing one via an include: edge is a fatal
authoring error (test_error_child_project_via_include).

It also proves the ownership contract consumed downstream:

  * CONTEXTMODULEIDENTITY is the include stem project-qualified by each
    context's intrinsic owner (with prefix dedup), identical whether the
    context is built standalone or imported, so a context's `export module`
    and a referencing file's `import` spell the same name in every build;
  * resolveFileOwner() maps every generated file (block / registrar-parent /
    context) to the absolute owning projectName from the DB, and None for a
    file that names no owning context;
  * both generators honor the DB-driven ownership gate: a child-owned file is
    SKIPPED when the generator runs under the root projectName and GENERATED
    when it runs under the child projectName, with no `--project` token emitted
    on any scaffold.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectOpen, qualifyModuleIdentity
from pysrc.artifactPaths import expandNewModulePath

FIXTURE = os.path.join(test_dir, 'fixtures', 'nested-ownership')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

ROOT_PROJECT_NAME = 'rootProj'
CHILD_PROJECT_NAME = 'childProj'


def _build_db(work):
    """Copy the committed fixture into a temp tree and build its database
    there, so projectCreate's generated build manifest never lands in the
    committed fixture. Returns the temp db path."""
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
    proj = os.path.join(work, 'root', 'yaml', 'rootProject.yaml')
    db = os.path.join(work, 'nested-ownership.db')
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, ARCH2CODE, '--yaml', proj, '--db', db],
        capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
    assert result.returncode == 0, \
        f"db build failed:\n{result.stdout}\n{result.stderr}"
    return db


def test_error_child_project_via_include():
    """Strict invariant: a project file may only be reached through the
    projectFiles: slot. Copy the fixture, inject an include: edge from
    rootTop.yaml to the sneaky.yaml project file, and assert the db build
    FAILS with the guard diagnostic naming the file and its projectName.
    """
    work = tempfile.mkdtemp(prefix='nested_ownership_neg_', dir=test_dir)
    try:
        shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
        root_top = os.path.join(work, 'root', 'yaml', 'rootTop.yaml')
        with open(root_top) as f:
            body = f.read()
        with open(root_top, 'w') as f:
            f.write("include:\n    - sneaky.yaml\n\n" + body)

        proj = os.path.join(work, 'root', 'yaml', 'rootProject.yaml')
        db = os.path.join(work, 'nested-ownership.db')
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, ARCH2CODE, '--yaml', proj, '--db', db],
            capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
        assert result.returncode != 0, \
            f"expected db build to fail on project-file-via-include:\n{result.stdout}\n{result.stderr}"
        diag = result.stdout + result.stderr
        assert 'sneakyProj' in diag and 'projectFiles:' in diag, \
            f"expected guard diagnostic naming projectName and projectFiles:\n{diag}"
        print("PASS: project-file-via-include: guard fires")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _newmodule_no_token(work):
    """Contract: run from the root project, `--newmodule` scaffolds only
    root-owned blocks AND CONTEXTS and skips child-owned ones (the ownership
    gate). A build scaffolds only the contexts it owns, so child-owned context
    files (childLeafIncludes.cppm/childLeaf_package.sv) are laid down by the
    child's OWN newmodule run, never by this root run.

    Ownership for BLOCK scaffolds is resolved from the DB by the generator gate,
    not from a token, so a block scaffold carries `--block` (never `--project`).
    The project-mode rtl.f carries `--project` directly. Context-mode scaffolds
    (Includes.cppm/VariantConfig.h/_package.sv/IncludesFW.*, identified by their
    `--context` token) carry BOTH `--context` (canonical yamlContext key) and
    `--project` (the context's owning project) — the S3-context dual stamp, so an
    owned file resolves ownership through `--project` and renders through
    `--context`. Build the fixture db, run `--newmodule` in the same temp tree,
    and assert those per-mode stamp shapes.
    """
    db = os.path.join(work, 'nested-ownership.db')
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    made = subprocess.run(
        [sys.executable, ARCH2CODE, '--db', db, '-r', '--newmodule'],
        capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
    assert made.returncode == 0, \
        f"newmodule failed:\n{made.stdout}\n{made.stderr}"

    # Collect every scaffolded GENERATED_CODE_PARAM line keyed by file basename.
    param_lines = dict()
    for root, _dirs, files in os.walk(work):
        for name in files:
            if 'yaml' in os.path.relpath(os.path.join(root, name), work).split(os.sep) \
               and name.endswith(('.yaml',)):
                continue
            full = os.path.join(root, name)
            if name.endswith('.db'):
                continue
            try:
                with open(full) as f:
                    for line in f:
                        if 'GENERATED_CODE_PARAM' in line:
                            param_lines.setdefault(name, line.strip())
                            break
            except (UnicodeDecodeError, IsADirectoryError):
                continue

    # Run from the root project, only root-owned scaffolds are created. Each block
    # model artifact is now a single .cppm module interface unit (blockModule);
    # the legacy .h/.cpp split is retired.
    for name in ('rootLeaf.cppm', 'rootLeafBase.cppm'):
        assert name in param_lines, f"expected root-owned scaffold '{name}' not generated"
    # Child-owned blocks are skipped by the ownership gate, so their files must
    # never be written across the ownership boundary.
    for name in ('childProjBlock.cppm', 'childProjBlockBase.cppm',
                 'childLeafBlock.cppm', 'childLeafBlockBase.cppm'):
        assert name not in param_lines, \
            f"child-owned scaffold '{name}' must be skipped when run from the root project"
    # Child-owned CONTEXT files are skipped by the same ownership gate: a build
    # scaffolds only the contexts it owns, so the root newmodule never lays down
    # a child context file with a parent-relative --context the child's own build
    # could not resolve (the basename fallback is gone).
    for name in ('childLeafIncludes.cppm', 'childLeaf_package.sv'):
        assert name not in param_lines, \
            f"child-owned context scaffold '{name}' must be skipped when run from the root project"
    # The ownership gate reports each skipped child block on stdout.
    assert 'owned by project' in made.stdout, \
        f"expected an ownership-skip message on stdout:\n{made.stdout}"
    # A project-mode artifact (rtl.f) names its owning project directly via
    # --project and owns no context (no --context token).
    assert '--project=' + ROOT_PROJECT_NAME in param_lines.get('rtl.f', ''), \
        f"project-mode rtl.f must carry --project={ROOT_PROJECT_NAME}: {param_lines.get('rtl.f')!r}"
    assert '--context=' not in param_lines.get('rtl.f', ''), \
        f"project-mode rtl.f must carry no --context token: {param_lines.get('rtl.f')!r}"
    for name, line in param_lines.items():
        if name == 'rtl.f':
            continue
        if '--context=' in line:
            # Context-mode scaffold: dual-stamped with --context (render) AND
            # --project (owner), so ownership never needs the context key.
            assert '--project=' in line, \
                f"context-mode scaffold '{name}' must carry a --project token: {line!r}"
        else:
            # Block-mode scaffold: ownership resolves from the DB via --block; no
            # --project token is stamped.
            assert '--project=' not in line, \
                f"block-mode scaffold '{name}' must carry no --project token: {line!r}"
    print("PASS: newModule (root run) skips child-owned blocks AND contexts; "
          "rtl.f carries --project, context scaffolds carry --context + --project, "
          "block scaffolds carry neither")


def _find_generated(work, basename):
    for root, _dirs, files in os.walk(work):
        if basename in files:
            return os.path.join(root, basename)
    raise AssertionError(f"generated file '{basename}' not found under {work}")


def _run_gen(db, flag, filepath):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run(
        [sys.executable, ARCH2CODE, '--db', db, '-r', flag, '--file', filepath],
        capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)


def _gate_skip_proof(work):
    """DB-driven ownership-gate proof for BOTH generators.

    A child-owned generated file must be SKIPPED (left byte-identical) when a
    generator runs under a projectName that does not own it, and GENERATED when
    it runs under the owning projectName. A context file carries --project (its
    owning project), which resolveFileOwner reads directly; the owner is compared
    against the running PROJECTNAME. We flip only the persisted PROJECTNAME in a
    db copy to drive the match case, so the same real generator invocation
    exercises both branches. The child-owned context artifacts
    (childLeafIncludes.cppm for SystemC, childLeaf_package.sv for SystemVerilog)
    scaffold with an empty generated region and are always in scope, so an
    empty->filled change is an unambiguous generate signal and no change is an
    unambiguous skip. A build scaffolds only the contexts it owns, so these
    child-owned files are laid down by a `--newmodule` run under the child
    projectName (the same PROJECTNAME-flipped db copy), not by the root build.
    """
    root_db = os.path.join(work, 'nested-ownership.db')
    child_db = os.path.join(work, 'nested-ownership-childmatch.db')
    shutil.copy(root_db, child_db)
    conn = sqlite3.connect(child_db)
    conn.execute("UPDATE _config SET value=? WHERE item='PROJECTNAME'",
                 (CHILD_PROJECT_NAME,))
    conn.commit()
    conn.close()

    # Scaffold the child-owned context files from the child project: the root
    # newmodule owns only root contexts, so these child artifacts do not exist
    # yet. Running --newmodule against the PROJECTNAME=childProj db lays them down.
    made = subprocess.run(
        [sys.executable, ARCH2CODE, '--db', child_db, '-r', '--newmodule'],
        capture_output=True, text=True, timeout=120, cwd=base_dir,
        env={**os.environ, 'NO_COLOR': '1'})
    assert made.returncode == 0, \
        f"child newmodule failed:\n{made.stdout}\n{made.stderr}"

    cases = [
        ('--systemc',                'childLeafIncludes.cppm'),
        ('--systemVerilogGenerator', 'childLeaf_package.sv'),
    ]
    for flag, basename in cases:
        path = _find_generated(work, basename)
        snapshot = open(path).read()

        # Mismatch: root project does not own the child file, must SKIP it.
        r = _run_gen(root_db, flag, path)
        assert r.returncode == 0, \
            f"{flag} mismatch run failed:\n{r.stdout}\n{r.stderr}"
        assert open(path).read() == snapshot, \
            f"{flag} gate FAILED to skip child-owned file {basename} under root"

        # Match: child project owns the file, must GENERATE (empty region -> filled).
        r = _run_gen(child_db, flag, path)
        assert r.returncode == 0, \
            f"{flag} match run failed:\n{r.stdout}\n{r.stderr}"
        assert open(path).read() != snapshot, \
            f"{flag} gate FAILED to generate child-owned file {basename} under child"
    print("PASS: SC and SV ownership gates skip under root, generate under child")


def _resolve_owner_unit(prj):
    """Unit-level proof of resolveFileOwner over each param shape.

    The gate resolves a file's absolute owner from the params on its
    GENERATED_CODE_PARAM line: a registrar file via its --parent block's
    context (parent wins over --block), a block file via its --block context, a
    context file via its --context directly, and None when no owning context is
    named (hierarchy/scope framework scaffolds).
    """
    def params(block=None, context=None, parent=None, project=None):
        return SimpleNamespace(block=block, context=context, parent=parent,
                               project=project)

    child_ctx = '../../child/yaml/childLeaf.yaml'
    assert prj.resolveFileOwner(params(block='childLeafBlock')) == CHILD_PROJECT_NAME
    assert prj.resolveFileOwner(params(block='rootLeaf')) == ROOT_PROJECT_NAME
    assert prj.resolveFileOwner(params(context=[child_ctx])) == CHILD_PROJECT_NAME
    # A registrar names both --block and --parent; the parent (assembler) owns it.
    assert prj.resolveFileOwner(
        params(block='rootLeaf', parent='childProjBlock')) == CHILD_PROJECT_NAME
    # A project-mode file (rtl.f) names its owning projectName directly. The gate
    # returns it verbatim: the current build owns it (root) or a referenced child
    # owns it (child, so the SC/SV skip gate fires and it is not regenerated).
    assert prj.resolveFileOwner(params(project=ROOT_PROJECT_NAME)) == ROOT_PROJECT_NAME
    assert prj.resolveFileOwner(params(project=CHILD_PROJECT_NAME)) == CHILD_PROJECT_NAME
    # No owning context named -> unowned -> always generate.
    assert prj.resolveFileOwner(params()) is None
    print("PASS: resolveFileOwner maps block/parent/context/project/none correctly")


def _context_by_stem(mapping, stem):
    """Return the value for the context whose file basename stem matches."""
    for context, value in mapping.items():
        if os.path.splitext(os.path.basename(context))[0] == stem:
            return context, value
    raise AssertionError(f"no context with stem '{stem}' in {list(mapping)}")


def _check_per_owner_resolution(prj):
    """PROJECTLAYOUT per-child resolution proof (M-split Phase 2).

    Each owning project gets its own layout rooted under its own $root, and
    expandNewModulePath resolves an object's path through the layout of the
    project that owns the object's defining context. So a child-owned block's
    path lands under the child project's $root and a root-owned block's path
    under the root project's $root.
    """
    layouts = prj.projectLayout
    assert set(layouts) == {ROOT_PROJECT_NAME, CHILD_PROJECT_NAME}, \
        f"PROJECTLAYOUT keys expected both projects, got {set(layouts)}"

    root_prj = layouts[ROOT_PROJECT_NAME]['prj']
    child_prj = layouts[CHILD_PROJECT_NAME]['prj']
    # Distinct per-project segment roots: the child's model segment must not
    # share the root's model segment.
    assert layouts[ROOT_PROJECT_NAME]['segments']['model']['path'] != \
        layouts[CHILD_PROJECT_NAME]['segments']['model']['path'], \
        "root and child layouts must have distinct model segments"

    # block-mode fileMap entry (basePath: model) drives a hasMdl block's path.
    blockDef = prj.config.getConfig('FILEMAP')['blockModule']
    expected_prj = {
        'rootLeaf':       (root_prj,  child_prj),
        'childProjBlock': (child_prj, root_prj),
        'childLeafBlock': (child_prj, root_prj),
    }
    seen = set()
    for row in prj.data['blocks'].values():
        block = row['block']
        if block not in expected_prj:
            continue
        owner = prj.contextOwningProject[row['_context']]
        layout = prj.projectLayout[owner]
        path = expandNewModulePath(blockDef, row['dir'], block, block, layout,
                                   missingDirOk=True)
        owned_root, other_root = expected_prj[block]
        assert path.startswith(owned_root + os.sep), \
            f"block '{block}' path '{path}' not under owner root '{owned_root}'"
        assert not path.startswith(other_root + os.sep), \
            f"block '{block}' path '{path}' must not be under '{other_root}'"
        seen.add(block)
    assert seen == set(expected_prj), \
        f"expected to resolve {set(expected_prj)}, saw {seen}"
    print(f"PASS: per-owner path resolution (root={root_prj}, child={child_prj})")


def run_all_tests():
    work = tempfile.mkdtemp(prefix='nested_ownership_', dir=test_dir)
    try:
        db = _build_db(work)
        prj = projectOpen(db)
        owners = prj.contextOwningProject
        identity = prj.contextModuleIdentity

        # Root-owned closure: the root top file and the root project's own leaf
        # stay root-owned. Identity is the include stem project-qualified by its
        # owning project (dedup inactive here: 'rootTop' does not lead with
        # 'rootProj'), so it resolves to 'rootProj_rootTop'.
        for stem in ('rootTop',):
            _, owner = _context_by_stem(owners, stem)
            assert owner == ROOT_PROJECT_NAME, \
                f"context '{stem}' expected root-owned, got '{owner}'"
            _, ident = _context_by_stem(identity, stem)
            expected = qualifyModuleIdentity(stem, owner)
            assert ident == expected, \
                f"root-owned '{stem}' identity expected '{expected}', got '{ident}'"

        # Child-owned closure: the child project file itself and the leaf reached
        # through the child's own projectFiles: slot are owned by the child.
        # Identity is the include stem project-qualified by the CHILD project
        # (intrinsic owner, build-independent), so 'childProject' ->
        # 'childProj_childProject' and 'childLeaf' -> 'childProj_childLeaf'.
        for stem in ('childProject', 'childLeaf'):
            _, owner = _context_by_stem(owners, stem)
            assert owner == CHILD_PROJECT_NAME, \
                f"context '{stem}' expected child-owned, got '{owner}'"
            _, ident = _context_by_stem(identity, stem)
            expected = qualifyModuleIdentity(stem, owner)
            assert ident == expected, \
                f"child-owned '{stem}' identity expected '{expected}', got '{ident}'"

        # Non-uniformity: at least two distinct owners must appear.
        distinct = set(owners.values())
        assert {ROOT_PROJECT_NAME, CHILD_PROJECT_NAME} <= distinct, \
            f"ownership not non-uniform: {distinct}"

        print(f"PASS: nested ownership non-uniform ({sorted(distinct)})")
        print("PASS: CONTEXTMODULEIDENTITY is owner-qualified for root- and child-owned contexts")

        # Unit-level owner resolution across every param shape.
        _resolve_owner_unit(prj)

        # Phase 2: per-owning-project directory resolution.
        _check_per_owner_resolution(prj)

        # New contract: newModule emits no ownership token.
        _newmodule_no_token(work)
        # The SC and SV generators honor the DB-driven ownership gate.
        _gate_skip_proof(work)
        # Strict invariant: a project file reached via include: is fatal.
        test_error_child_project_via_include()
        return 0
    finally:
        # Close the read-only sqlite handle projectOpen left open so the temp
        # tree (db file included) can be removed cleanly.
        if g.db is not None:
            g.db.close()
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(run_all_tests())
