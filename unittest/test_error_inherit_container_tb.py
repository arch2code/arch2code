#!/usr/bin/env python3
"""A testbench on a block whose Config comes from its container is a db error.

A testbench builds one DUT at one named variant. A parameterizable block reached
only through `inheritContainerParam` declares no variant of its own, so the only
labels in reach belong to the container and none of them names a Config of the
block. `validateContainerSourcedTestbench` (`pysrc/processYaml.py`, run right
after `calcVariantSourceBlocks`) rejects the pairing, naming the block, the
testbench artifacts it selected, and the blocks its Config comes from.

The fixture is that shape and nothing more: `itrLeaf` declares `params:`, is
instantiated once with `inheritContainerParam: true`, and carries `hasTb: true`.
The suite copies it to a temp tree and runs `make db`, because the rejection has
to happen through the same database build a user runs.

The second phase is the remedy from the diagnostic: give `itrLeaf` a variant of
its own and leave everything else alone. `make db` must then pass. Without that
phase a rule that rejected every parameterizable block would look identical
here.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'inherit-tb-request')
ARCH = os.path.join('yaml', 'itrTop.yaml')

REQUIRED_SUBSTRINGS = [
    "'itrLeaf'",
    "testBench",
    "declares no variant of its own",
    "itrCont",
    "Declare a variant on 'itrLeaf'",
]

# The remedy the diagnostic states, anchored on text the fixture carries
# verbatim so a fixture reword fails here loudly rather than skipping the phase.
DECLARE_LEAF_VARIANT = [
    ("    itrCont:\n        contA:\n            ITR_ALGO: ITR_ALGO\n",
     "    itrCont:\n        contA:\n            ITR_ALGO: ITR_ALGO\n"
     "    itrLeaf:\n        tb:\n            ITR_ALGO: ITR_ALGO\n"),
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
        print("  FAIL: make db accepted a testbench on a container-sourced block")
        print(output)
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
    print("  PASS: the testbench is rejected, naming the block, the artifact "
          "and the variant source")
    return True


def check_accepted(project):
    edit_arch(project, DECLARE_LEAF_VARIANT)
    rc, output = make_db(project)
    if rc != 0:
        print(f"  FAIL: make db rejected the block once it declared a variant (rc={rc})")
        print(output)
        return False
    print("  PASS: the same testbench is accepted once the block declares its "
          "own variant")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='inherit_tb_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'itrReject')
        shutil.copytree(FIXTURE, project)
        ok = check_rejected(project)
        accept = os.path.join(tmp, 'itrAccept')
        shutil.copytree(FIXTURE, accept)
        ok = check_accepted(accept) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: a testbench needs a variant declared on its own block")
        return 0
    print("\nFAIL: the container-sourced testbench rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
