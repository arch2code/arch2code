#!/usr/bin/env python3
"""Ownership classifier proof for the M-split parsing change.

Builds the committed `fixtures/nested-ownership` two-project fixture into a
temporary database and asserts that per-context ownership is NON-UNIFORM:

  * the child PROJECT file (reached through the root's projectFiles: slot and
    carrying the projectName/dirs/fileGeneration sentinel set) and everything in
    its transitive closure are owned by the child projectName;
  * everything reached through the root's own closure stays root-owned;
  * a file that carries the sentinel keys but arrives via the include: slot is
    NOT misclassified and stays root-owned.

It also checks the downstream CONTEXTMODULEIDENTITY consumer: a child-owned
context gets the qualified `<childProject>.<stem>` spelling, root-owned contexts
keep the bare stem.
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
from pysrc.processYaml import projectOpen, expandNewModulePath

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
    blockDef = prj.config.getConfig('FILEMAP')['block']
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

        # Root-owned closure: the root top file, the root project's own leaf,
        # and the sentinel-bearing included file all stay root-owned.
        for stem in ('rootTop', 'sneaky'):
            _, owner = _context_by_stem(owners, stem)
            assert owner == ROOT_PROJECT_NAME, \
                f"context '{stem}' expected root-owned, got '{owner}'"
            _, ident = _context_by_stem(identity, stem)
            assert ident == stem, \
                f"root-owned '{stem}' identity expected bare stem, got '{ident}'"

        # Child-owned closure: the child project file itself and the leaf reached
        # through the child's own projectFiles: slot are owned by the child.
        for stem in ('childProject', 'childLeaf'):
            _, owner = _context_by_stem(owners, stem)
            assert owner == CHILD_PROJECT_NAME, \
                f"context '{stem}' expected child-owned, got '{owner}'"
            _, ident = _context_by_stem(identity, stem)
            assert ident == f'{CHILD_PROJECT_NAME}.{stem}', \
                f"child-owned '{stem}' identity expected qualified, got '{ident}'"

        # Non-uniformity: at least two distinct owners must appear.
        distinct = set(owners.values())
        assert {ROOT_PROJECT_NAME, CHILD_PROJECT_NAME} <= distinct, \
            f"ownership not non-uniform: {distinct}"

        print(f"PASS: nested ownership non-uniform ({sorted(distinct)})")

        # Phase 2: per-owning-project directory resolution.
        _check_per_owner_resolution(prj)
        return 0
    finally:
        # Close the read-only sqlite handle projectOpen left open so the temp
        # tree (db file included) can be removed cleanly.
        if g.db is not None:
            g.db.close()
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(run_all_tests())
