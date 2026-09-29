#!/usr/bin/env python3
"""A block param backed by an eval-derived constant is a database-time error.

Fixture: `bpeLeaf` binds a plain `BASE_WIDTH` and an eval `DERIVED_WIDTH =
$BASE_WIDTH * 2` in one variant; `make db` must reject it. A second phase makes
`DERIVED_WIDTH` a plain constant with the same value and requires the build to
pass, so the check is shown to key on eval, not on every binding."""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'block-param-eval-backing')
ARCH = os.path.join('yaml', 'bpeTop.yaml')

REQUIRED_SUBSTRINGS = [
    "bpeTop.yaml",
    "block param 'DERIVED_WIDTH'",
    "'DERIVED_WIDTH' (declared in",
    "computed with eval:",
    "a plain (non-eval) ipParameters constant",
]

# Moves the eval-derived constant into ipParameters as a plain one bound at
# the same value, so the second phase changes only the fact under test.
MAKE_PLAIN = [
    ('    constants:\n        BASE_WIDTH: { value: 4, maxValue: 16, desc: "Base width" }\n'
     '\nconstants:\n'
     '    DERIVED_WIDTH: { eval: "$BASE_WIDTH * 2", desc: "Derived width, 2x base" }\n',
     '    constants:\n        BASE_WIDTH: { value: 4, maxValue: 16, desc: "Base width" }\n'
     '        DERIVED_WIDTH: { value: 8, maxValue: 32, desc: "Derived width, 2x base" }\n'),
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
        print("  FAIL: make db accepted a block param backed by an eval-derived "
              "constant")
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
    print("  PASS: the eval-backed block param is rejected, naming file, "
          "param and constant")
    return True


def check_accepted(project):
    edit_arch(project, MAKE_PLAIN)
    rc, output = make_db(project)
    if rc != 0:
        print(f"  FAIL: make db rejected the same binding once the backing "
              f"constant is plain (rc={rc})")
        print(output)
        return False
    print("  PASS: the same binding is accepted once the backing constant is "
          "non-eval")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='bpe_eval_backing_', dir=test_dir)
    try:
        reject = os.path.join(tmp, 'bpeReject')
        shutil.copytree(FIXTURE, reject)
        ok = check_rejected(reject)
        accept = os.path.join(tmp, 'bpeAccept')
        shutil.copytree(FIXTURE, accept)
        ok = check_accepted(accept) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: a block param backed by an eval-derived constant is "
              "rejected at db")
        return 0
    print("\nFAIL: the eval-backed block param rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
