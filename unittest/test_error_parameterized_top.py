#!/usr/bin/env python3
"""A top instance whose block declares `params:` is rejected at database time.

A top has no container, so nothing can source its parameters, and a project
declares one top, so only one variant of literals could ever bind them. That
buys nothing a plain constant does not, and everything downstream that types a
child from its container reaches a block whose own Config came from nowhere.
`_post_validateInstanceParameterBinding` (`pysrc/processYaml.py`, attached to
`instances` in `config/schema.yaml`) rejects the row, naming the instance, the
block, the project, the file and the line, and states the restructure.

The fixture's top instance names `variant: ptV0`, so it is well formed by every
other rule; the sibling missing-selector arm of the same hook has nothing to
fire on. That isolation is the point. A suite whose fixture merely omitted the
variant would pass against either arm.

The second phase performs the restructure the diagnostic asks for. It adds an
unparameterized `ptRoot` above the harness, moves the harness into it, and
repoints `topInstance:`, then requires `make db` to pass. The parameterized
harness survives one level down, which is what `examples/xif` now does.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'parameterized-top')
ARCH = os.path.join('yaml', 'ptTop.yaml')
PROJECT_YAML = os.path.join('prj', 'yaml', 'ptProject.yaml')

REQUIRED_SUBSTRINGS = [
    "ptTop.yaml",
    "top instance 'ptTop_tb'",
    "block 'ptTop_tb'",
    "project 'ptTest'",
    "params: [PT_WIDTH]",
    "A top has no container to source parameters from",
]

# The other arm of the same hook. The fixture names a variant, so it must be
# silent; if it speaks, this suite is proving the wrong rule.
SELECTOR_ARM_MARKER = "names neither variant: nor inheritContainerParam:"

# Phase two: put an unparameterized root above the parameterized harness. Each
# edit is anchored on text the fixture carries verbatim, so a fixture reword
# fails loudly rather than silently skipping the phase.
ADD_ROOT = [
    ('blocks:\n',
     'blocks:\n'
     '    ptRoot:\n'
     '        desc: "Unparameterized root holding the harness"\n'
     '        hasMdl: false\n'
     '        hasTb: false\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'),
    ('    ptTop_tb: { container: ptTop_tb,',
     '    ptRoot:   { container: ptRoot, instanceType: ptRoot, instGroup: top }\n'
     '    ptTop_tb: { container: ptRoot,'),
]
REPOINT_TOP = [('topInstance: ptTop_tb', 'topInstance: ptRoot')]


def make_db(project):
    """Run `make db` against the temp copy, with both roots overridden."""
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           'db']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                            env=env)
    return result.returncode, result.stdout + result.stderr


def edit_yaml(project, relative, edits):
    """Apply anchored substitutions to one YAML file of the temp copy."""
    path = os.path.join(project, relative)
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
        print("  FAIL: make db accepted a parameterized top instance")
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
    if SELECTOR_ARM_MARKER in output:
        print("  FAIL: the missing-selector arm claimed a top that names a variant")
        print(output)
        return False
    print("  PASS: the parameterized top is rejected, naming instance, block, "
          "project and file")
    return True


def check_accepted(project):
    edit_yaml(project, ARCH, ADD_ROOT)
    edit_yaml(project, PROJECT_YAML, REPOINT_TOP)
    rc, output = make_db(project)
    if rc != 0:
        print(f"  FAIL: make db rejected the harness under an unparameterized "
              f"root (rc={rc})")
        print(output)
        return False
    print("  PASS: the same parameterized harness is accepted one level down")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='param_top_', dir=test_dir)
    try:
        reject = os.path.join(tmp, 'ptReject')
        shutil.copytree(FIXTURE, reject)
        ok = check_rejected(reject)
        accept = os.path.join(tmp, 'ptAccept')
        shutil.copytree(FIXTURE, accept)
        ok = check_accepted(accept) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: a parameterized top instance is rejected at db")
        return 0
    print("\nFAIL: the parameterized-top rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
