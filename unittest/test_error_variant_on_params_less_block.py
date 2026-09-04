#!/usr/bin/env python3
"""A variant declared on a block that has no `params:` is a database-time error.

A variant exists to bind parameters. On a block that declares none it binds
nothing and can carry no Config, so `_post_validateVariantParameterCompleteness`
(`pysrc/processYaml.py`, attached to `parametersvariants` in
`config/schema.yaml`) rejects the row where it is declared, naming the block,
the variant and the file.

The fixture is that shape and nothing more: `epvLeaf` declares no `params:` and
one variant, `solo`, bound by one instance. The suite copies it to a temp tree
and runs `make db`, because the rejection has to happen through the same
database build a user runs, and a Python traceback is not a rejection.

The second phase guards the other side. It gives `epvLeaf` a `params:` list and
has `solo` bind it, then runs `make db` again and requires it to pass. Without
that, a rule that rejected every variant row outright would look identical here.

The third phase pins the boundary against the missing-parameter arm of the same
hook. It declares the `params:` list but leaves `solo` binding nothing, which is
the shape that would reach `set(None)` if the params-less arm read the variant's
bindings instead of the block's declarations. It must draw the missing-parameter
diagnostic, never the params-less one.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'empty-variant-no-params')
ARCH = os.path.join('yaml', 'epvTop.yaml')

REQUIRED_SUBSTRINGS = [
    "variant 'solo'",
    "block 'epvLeaf'",
    "epvTop.yaml",
    "declares no params:",
    "can carry no Config",
]

# Fixture edits the later phases apply. Each is anchored on text the fixture
# carries verbatim, so a fixture reword fails here loudly rather than silently
# skipping a phase.
DECLARE_PARAM = [
    ('blocks:',
     'ipParameters:\n'
     '    constants:\n'
     '        EPV_ALGO: { value: 1, maxValue: 7, desc: "Algorithm select" }\n'
     '\nblocks:'),
    ('        hasVl: false\n\ninstances:',
     '        hasVl: false\n        params: [EPV_ALGO]\n\ninstances:'),
]
BIND_PARAM = [
    ('        solo: {}', '        solo: { EPV_ALGO: 3 }'),
]

# Phase three: what the missing-parameter arm must say, and what it must not.
MISSING_SUBSTRINGS = [
    "Variant 'solo'",
    "block 'epvLeaf'",
    "missing required parameter(s): EPV_ALGO",
]
NEW_ARM_MARKER = "declares no params:"


def make_db(project):
    """Run `make db` against the temp copy, with both roots overridden."""
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           'db']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                            env=env)
    return result.returncode, result.stdout + result.stderr


def edit_arch(project, edits):
    """Apply anchored substitutions to the temp copy's architecture YAML."""
    path = os.path.join(project, ARCH)
    with open(path) as f:
        text = f.read()
    for old, new in edits:
        if old not in text:
            raise RuntimeError(f"fixture no longer carries the anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def check_rejected(project):
    rc, output = make_db(project)
    if rc == 0:
        print("  FAIL: make db accepted a variant on a block with no params:")
        return False
    if 'Traceback (most recent call last)' in output:
        print("  FAIL: got a Python stack trace instead of a clean rejection")
        print(output)
        return False
    missing = [s for s in REQUIRED_SUBSTRINGS if s not in output]
    if missing:
        print(f"  FAIL: diagnostic missing substrings: {missing}")
        print(output)
        return False
    print("  PASS: the empty variant is rejected, naming block, variant and file")
    return True


def check_accepted(project):
    edit_arch(project, DECLARE_PARAM + BIND_PARAM)
    rc, output = make_db(project)
    if rc != 0:
        print(f"  FAIL: make db rejected the well-formed variant (rc={rc})")
        print(output)
        return False
    print("  PASS: the same variant is accepted once the block declares the param")
    return True


def check_missing_arm(project):
    edit_arch(project, DECLARE_PARAM)
    rc, output = make_db(project)
    if rc == 0:
        print("  FAIL: make db accepted a variant binding none of the block's params")
        return False
    missing = [s for s in MISSING_SUBSTRINGS if s not in output]
    if missing:
        print(f"  FAIL: missing-parameter diagnostic missing substrings: {missing}")
        print(output)
        return False
    if NEW_ARM_MARKER in output:
        print("  FAIL: the params-less arm claimed a block that declares params:")
        print(output)
        return False
    print("  PASS: an empty binding on a params-declaring block draws the "
          "missing-parameter diagnostic")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='empty_variant_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'epv')
        shutil.copytree(FIXTURE, project)
        ok = check_rejected(project)
        ok = check_accepted(project) and ok
        boundary = os.path.join(tmp, 'epvBoundary')
        shutil.copytree(FIXTURE, boundary)
        ok = check_missing_arm(boundary) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: a variant on a params-less block is rejected at db")
        return 0
    print("\nFAIL: the params-less variant rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
