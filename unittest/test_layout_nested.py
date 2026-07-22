#!/usr/bin/env python3
"""Hierarchical layout sign-off vehicle: migrated `examples/nested`
(plan-decomp-functional-layout.md T4.6 sign-off).

`nested` is the real build+run example converted in place from functional to
hierarchical (via `make migrate-hierarchical`): its project file lives in the
`prj/` container, its single authored block YAML in `yaml/`, and its build
config `include/` stays at the project root (Q-L3 amended). Unlike the
green-field `hier-layout` fixture (generate-only, decomposition-outer nodes),
nested is flat (one root node) but exercises the full model build/run, so it is
the vehicle that proves the migration end-to-end on a committed example.

This test copies nested's authored input (prj/ + yaml/) into a temp tree, builds
the database and runs --newmodule (the same arch2code invocation the fixture
test uses), then asserts the generated file set matches a committed structural
golden. It guards the hierarchical placement (functional segments beside the
node, fw flattened, project file under prj/) against regression without needing
a full build. The build+run itself is covered by `make run` from nested/rundir.

Regenerate the golden intentionally with GOLDEN=1.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(base_dir, 'examples', 'nested')
GOLDEN = os.path.join(FIXTURE, 'expected_tree.golden')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')


def _arch2code(*args, cwd):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run(
        [sys.executable, ARCH2CODE, *args],
        capture_output=True, text=True, timeout=120, cwd=cwd, env=env)


def _generate_tree():
    """Copy nested's authored input to a temp tree, build the db, run
    --newmodule, and return the sorted set of generated file paths relative to
    the temp root (authored yaml/db/.gen excluded)."""
    tmp = tempfile.mkdtemp(prefix='nested_layout_', dir=test_dir)
    try:
        # Copy only the authored input (the project container + the node yaml/),
        # never the golden or any stale generated output / build tree.
        for node in ('prj', 'yaml'):
            shutil.copytree(os.path.join(FIXTURE, node),
                            os.path.join(tmp, node))
        proj = os.path.join(tmp, 'prj', 'yaml', 'nestedProject.yaml')
        db = os.path.join(tmp, 'nested.db')

        # Run the generator with cwd inside the temp project copy so that any
        # relative path resolution stays sandboxed in tmp. Snapshot the repo
        # root before/after: a hierarchical node-relative segment resolved
        # against cwd used to leak a stray tree (e.g. rtl/rtl.f) to the process
        # cwd, so assert generation creates nothing outside tmp.
        before = set(os.listdir(base_dir))
        built = _arch2code('--yaml', proj, '--db', db, cwd=tmp)
        assert built.returncode == 0, \
            f"db build failed:\n{built.stdout}\n{built.stderr}"
        made = _arch2code('--db', db, '-r', '--newmodule', cwd=tmp)
        assert made.returncode == 0, \
            f"newmodule failed:\n{made.stdout}\n{made.stderr}"
        after = set(os.listdir(base_dir))
        leaked = after - before
        assert not leaked, \
            f"generation created entries outside tmp at {base_dir}: {sorted(leaked)}"

        generated = []
        for root, _dirs, files in os.walk(tmp):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, tmp)
                parts = rel.split(os.sep)
                # Skip authored YAML (in a yaml/ dir), the db, and the .gen tree.
                if 'yaml' in parts or parts[0] == '.gen':
                    continue
                if name.endswith('.db'):
                    continue
                generated.append(rel)
        return sorted(generated), tmp
    finally:
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
        print(f"PASS: nested hierarchical tree matches golden ({len(expected)} paths)")
        return 0

    exp = set(expected)
    got = set(generated)
    print("FAIL: nested hierarchical generated tree differs from golden")
    for missing in sorted(exp - got):
        print(f"  - missing (in golden, not generated): {missing}")
    for extra in sorted(got - exp):
        print(f"  + extra (generated, not in golden):    {extra}")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
