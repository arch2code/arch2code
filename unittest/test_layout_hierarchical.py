#!/usr/bin/env python3
"""Hierarchical layout structural golden (plan-decomp-functional-layout.md
T1.5/T1.6).

The green-field fixture under fixtures/hier-layout/ declares
fileGeneration.layout: hierarchical with two decomposition nodes (core, leaf).
This test copies the authored YAML into a temp tree, builds the database and
runs --newmodule (the same arch2code invocation the unit-test suite uses
everywhere), then asserts the generated file set matches a committed structural
golden. A layout regression (segments no longer created beside each node's
yaml/, or re-rooted under shared functional roots) shows up as a golden diff
rather than only when a later build breaks.

The golden is the find-sorted set of generated file paths relative to the
fixture root. Regenerate it intentionally with GOLDEN=1.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'hier-layout')
GOLDEN = os.path.join(FIXTURE, 'expected_tree.golden')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')


def _arch2code(*args):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run(
        [sys.executable, ARCH2CODE, *args],
        capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)


def _generate_tree():
    """Copy the authored fixture YAML to a temp tree, build the db, run
    --newmodule, and return the sorted set of generated file paths relative to
    the temp root (authored yaml/db/.gen excluded)."""
    tmp = tempfile.mkdtemp(prefix='hier_layout_', dir=test_dir)
    try:
        # Copy only the authored input (the node yaml/ dirs + prj/), never the
        # golden or any stale generated output.
        for node in ('prj', 'core', 'leaf'):
            shutil.copytree(os.path.join(FIXTURE, node),
                            os.path.join(tmp, node))
        proj = os.path.join(tmp, 'prj', 'yaml', 'hierProject.yaml')
        db = os.path.join(tmp, 'hier.db')

        built = _arch2code('--yaml', proj, '--db', db)
        assert built.returncode == 0, \
            f"db build failed:\n{built.stdout}\n{built.stderr}"
        made = _arch2code('--db', db, '-r', '--newmodule')
        assert made.returncode == 0, \
            f"newmodule failed:\n{made.stdout}\n{made.stderr}"

        generated = []
        for root, _dirs, files in os.walk(tmp):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, tmp)
                parts = rel.split(os.sep)
                # Skip authored YAML (in a yaml/ dir), the db, and the .gen tree.
                if 'yaml' in parts or rel == 'hier.db' or parts[0] == '.gen':
                    continue
                if name.endswith('.db'):
                    continue
                # Skip the committed build harness (include/make/shared.mk): it
                # is user-owned build config at the project root (Q-L3 amended),
                # not generated output, so it must not appear in the
                # generated-only golden. Only prj/, core/, leaf/ are copied into
                # the temp tree, so the root include/, Makefile, and rundir/ never
                # reach here; the guard stays as a belt-and-braces exclusion.
                if parts[0] == 'include':
                    continue
                generated.append(rel)
        return sorted(generated), tmp
    finally:
        # tmp retained only on assertion failure for inspection is unnecessary;
        # always clean.
        shutil.rmtree(tmp, ignore_errors=True)


def run_all_tests():
    generated, _tmp = _generate_tree()

    if os.environ.get('GOLDEN') == '1' or not os.path.exists(GOLDEN):
        with open(GOLDEN, 'w') as f:
            f.write('\n'.join(generated) + '\n')
        print(f"wrote golden ({len(generated)} paths) to {GOLDEN}")
        if os.environ.get('GOLDEN') != '1':
            print("NOTE: golden did not exist; captured it. Re-run to compare.")
        return 0

    with open(GOLDEN) as f:
        expected = [ln for ln in f.read().splitlines() if ln]

    if generated == expected:
        print(f"PASS: hierarchical tree matches golden ({len(expected)} paths)")
        return 0

    exp = set(expected)
    got = set(generated)
    print("FAIL: hierarchical generated tree differs from golden")
    for missing in sorted(exp - got):
        print(f"  - missing (in golden, not generated): {missing}")
    for extra in sorted(got - exp):
        print(f"  + extra (generated, not in golden):    {extra}")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
