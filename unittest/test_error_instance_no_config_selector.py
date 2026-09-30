#!/usr/bin/env python3
"""An instance of a params-declaring block must select a Config, or be rejected.

A block that declares `params:` is typed per instance. There are exactly two
ways an instance names that type: `variant: X`, which binds values or sources
them from the container per parameter, or `inheritContainerParam: true`, which
takes the container's whole Config. An instance naming neither leaves the block
parameterized and the instance untyped, and downstream each language then
guesses differently: C++ falls back to the context default Config while the
SystemVerilog path forwards whichever container symbols happen to match by name.
`_post_validateInstanceParameterBinding` (`pysrc/processYaml.py`, attached to
`instances` in `config/schema.yaml`) rejects that row where it is authored,
naming the instance, the block, the project, the file and the line.

The fixture is that shape and nothing more: `incLeaf` declares `params:
[INC_WIDTH]` and `uLeaf` names no variant and does not inherit. Its container
`incTop` declares the same parameter, so both accepting forms are one edit away.
The suite copies the tree to a temp directory and runs `make db`, because the
rejection has to arrive through the database build a user runs, and because a
rejection delivered as a Python traceback is no better than silence.

Phases two and three guard the accepting side, one per legal form: `variant:
leafV0`, then `inheritContainerParam: true`. Without both, a rule that rejected
every instance of a parameterized block would look identical here.

Each phase also requires the parameterized-top diagnostic to stay absent.
`uLeaf` is contained, not a top, and the two rules share one hook.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'instance-no-config-selector')
ARCH = os.path.join('yaml', 'incTop.yaml')

REQUIRED_SUBSTRINGS = [
    "incTop.yaml",
    "instance 'uLeaf'",
    "block 'incLeaf'",
    "project 'incTest'",
    "names neither variant: nor inheritContainerParam:",
    "params: [INC_WIDTH]",
]

# The other arm of the same hook. It concerns tops, so it must never speak here.
TOP_ARM_MARKER = "A top has no container to source parameters from"

# Fixture edits the accepting phases apply. Each is anchored on text the fixture
# carries verbatim, so a fixture reword fails here loudly rather than silently
# skipping a phase.
NAME_VARIANT = [
    ('instanceType: incLeaf,   instGroup: top }',
     'instanceType: incLeaf,   instGroup: top, variant: leafV0 }'),
]
INHERIT_CONTAINER = [
    ('instanceType: incLeaf,   instGroup: top }',
     'instanceType: incLeaf,   instGroup: top, inheritContainerParam: true }'),
]


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
        print("  FAIL: make db accepted an instance that selects no Config")
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
    if TOP_ARM_MARKER in output:
        print("  FAIL: the parameterized-top arm claimed a contained instance")
        print(output)
        return False
    print("  PASS: the selector-less instance is rejected, naming instance, "
          "block, project and file")
    return True


def check_accepted(project, edits, label):
    edit_arch(project, edits)
    rc, output = make_db(project)
    if rc != 0:
        print(f"  FAIL: make db rejected {label} (rc={rc})")
        print(output)
        return False
    print(f"  PASS: the same instance is accepted with {label}")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='inst_selector_', dir=test_dir)
    try:
        reject = os.path.join(tmp, 'incReject')
        shutil.copytree(FIXTURE, reject)
        ok = check_rejected(reject)
        variant = os.path.join(tmp, 'incVariant')
        shutil.copytree(FIXTURE, variant)
        ok = check_accepted(variant, NAME_VARIANT, 'variant: leafV0') and ok
        inherit = os.path.join(tmp, 'incInherit')
        shutil.copytree(FIXTURE, inherit)
        ok = check_accepted(inherit, INHERIT_CONTAINER,
                            'inheritContainerParam: true') and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: an instance of a params-declaring block must select a Config")
        return 0
    print("\nFAIL: the instance Config-selector rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
