#!/usr/bin/env python3
"""Provider-override selection + duplicate-provider diagnostic proof.

Builds the committed `fixtures/provider-override` composition, where projectName
`sharedIp` is reachable by two lexically-distinct projectFiles: paths (the root's
direct reference and the mid child's `mid/ip -> ../provider` symlinked
reference). Two behaviors are locked at db (parse/ownership) time:

  * POSITIVE: with the root `projectOverrides: sharedIp` entry present, the
    composition selects exactly ONE sharedIp provider (the root-selected real
    provider); the db build succeeds and the sharedIp context resolves to the
    real provider path, never the symlinked mid/ip path.
  * NEGATIVE: with that override removed, the db build FAILS with a detailed
    duplicate-provider diagnostic that names projectName sharedIp and BOTH
    conflicting provider paths and points at the projectOverrides recovery.

Provider selection is resolved in readRaw()/_selectProvider() before any code
generation, so this is a pure db-time contract.
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
from pysrc.processYaml import projectOpen

FIXTURE = os.path.join(test_dir, 'fixtures', 'provider-override')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

SHARED_PROJECT_NAME = 'sharedIp'
# Fragments that distinguish the two provider paths in the diagnostic.
REAL_PROVIDER_FRAGMENT = os.path.join('provider', 'yaml', 'sharedProject.yaml')
SYMLINK_PROVIDER_FRAGMENT = os.path.join('mid', 'ip', 'yaml', 'sharedProject.yaml')


def _build_db(project_path, db_path):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run(
        [sys.executable, ARCH2CODE, '--yaml', project_path, '--db', db_path],
        capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)


def _strip_overrides(project_path):
    """Remove the projectOverrides: block (its header plus the indented entries
    that follow) from a copied root project file, leaving both sharedIp
    providers unselected."""
    with open(project_path) as f:
        lines = f.readlines()
    out = []
    skipping = False
    for line in lines:
        if line.startswith('projectOverrides:'):
            skipping = True
            continue
        if skipping:
            # The block ends at the next non-indented, non-blank line.
            if line.strip() == '' or line[:1] in (' ', '\t'):
                continue
            skipping = False
        out.append(line)
    with open(project_path, 'w') as f:
        f.writelines(out)


def _positive(work):
    """Override present: db builds and sharedIp resolves to the real provider."""
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True, symlinks=True)
    project = os.path.join(work, 'root', 'yaml', 'rootProject.yaml')
    db = os.path.join(work, 'provider-override.db')
    result = _build_db(project, db)
    assert result.returncode == 0, \
        f"positive db build failed:\n{result.stdout}\n{result.stderr}"

    prj = projectOpen(db)
    try:
        owners = prj.contextOwningProject
        shared_contexts = {
            ctx: owner for ctx, owner in owners.items()
            if os.path.basename(ctx) == 'sharedProject.yaml'
        }
        assert shared_contexts, \
            f"no sharedProject context in ownership map: {list(owners)}"
        # Exactly one sharedProject context, owned by sharedIp, on the real path.
        assert len(shared_contexts) == 1, \
            f"expected one sharedProject provider context, got {shared_contexts}"
        ctx, owner = next(iter(shared_contexts.items()))
        assert owner == SHARED_PROJECT_NAME, \
            f"sharedProject context owned by '{owner}', expected '{SHARED_PROJECT_NAME}'"
        assert REAL_PROVIDER_FRAGMENT in ctx, \
            f"selected provider '{ctx}' is not the real provider path"
        assert SYMLINK_PROVIDER_FRAGMENT not in ctx, \
            f"selected provider '{ctx}' is the symlinked mid/ip path, not the root selection"
    finally:
        if g.db is not None:
            g.db.close()
            g.db = None
    print("PASS: root override selects the single real sharedIp provider")


def _negative(work):
    """Override removed: db build fails with a detailed duplicate-provider error
    naming projectName sharedIp and both conflicting provider paths."""
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True, symlinks=True)
    project = os.path.join(work, 'root', 'yaml', 'rootProject.yaml')
    db = os.path.join(work, 'provider-override.db')
    _strip_overrides(project)
    result = _build_db(project, db)
    assert result.returncode != 0, \
        f"negative db build unexpectedly succeeded:\n{result.stdout}\n{result.stderr}"
    combined = result.stdout + result.stderr
    for needle in ("Multiple providers declare projectName",
                   f"'{SHARED_PROJECT_NAME}'",
                   REAL_PROVIDER_FRAGMENT,
                   SYMLINK_PROVIDER_FRAGMENT,
                   "projectOverrides"):
        assert needle in combined, \
            f"duplicate-provider diagnostic missing '{needle}':\n{combined}"
    print("PASS: removing the override yields a duplicate-provider error naming both paths")


def run_all_tests():
    work = tempfile.mkdtemp(prefix='provider_override_', dir=test_dir)
    try:
        _positive(os.path.join(work, 'pos'))
        _negative(os.path.join(work, 'neg'))
        return 0
    finally:
        if g.db is not None:
            g.db.close()
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(run_all_tests())
