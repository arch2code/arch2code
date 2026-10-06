#!/usr/bin/env python3
"""A socket shell (hasSkt: true) on a parameterizable block without a model is
rejected at db.

The assembler's registrar (templates/systemc/blockRegistrar.py) registers a
parameterizable block's socket shell, and that registrar is generated only for
a block with a model. `validateParameterizedSocketHasModel`
(`pysrc/processYaml.py`) rejects the combination at `make db`, naming the
block, instead of letting the factory lookup fail at run time.

The fixture is parameterized-top under an unparameterized root, the shape
test_error_parameterized_top.py's accepted arm uses. Two arms: hasSkt with
hasMdl false on the parameterizable harness block is rejected; the same block
with hasMdl true is accepted.
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

# Anchored on the harness block's own params: and hasMdl: lines, so the flags
# land on the parameterizable block and nowhere else.
SOCKET_WITHOUT_MODEL = [
    ('        params: [PT_WIDTH]\n'
     '        hasMdl: false\n',
     '        params: [PT_WIDTH]\n'
     '        hasSkt: true\n'
     '        hasMdl: false\n'),
]
SOCKET_WITH_MODEL = [
    ('        params: [PT_WIDTH]\n'
     '        hasMdl: false\n',
     '        params: [PT_WIDTH]\n'
     '        hasSkt: true\n'
     '        hasMdl: true\n'),
]

REQUIRED_SUBSTRINGS = [
    "Block 'ptTop_tb'",
    "hasSkt: true and is parameterizable, but has hasMdl: false",
    "Set hasMdl: true",
]


def make_db(project):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           'db']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                            env=env)
    return result.returncode, result.stdout + result.stderr


def edit_yaml(project, relative, edits):
    path = os.path.join(project, relative)
    with open(path) as f:
        text = f.read()
    for old, new in edits:
        if old not in text:
            raise RuntimeError(f"fixture no longer carries the anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def prepare(project):
    shutil.copytree(FIXTURE, project)
    edit_yaml(project, ARCH, ADD_ROOT)
    edit_yaml(project, PROJECT_YAML, REPOINT_TOP)


def check_rejected(project):
    prepare(project)
    edit_yaml(project, ARCH, SOCKET_WITHOUT_MODEL)
    rc, output = make_db(project)
    if rc == 0:
        print("  FAIL: make db accepted hasSkt on a parameterizable block without a model")
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
    print("  PASS: hasSkt without hasMdl on a parameterizable block is rejected, naming the block")
    return True


def check_accepted(project):
    prepare(project)
    edit_yaml(project, ARCH, SOCKET_WITH_MODEL)
    rc, output = make_db(project)
    if rc != 0:
        print(f"  FAIL: make db rejected hasSkt with hasMdl on a parameterizable block (rc={rc})")
        print(output)
        return False
    print("  PASS: hasSkt with hasMdl on a parameterizable block is accepted")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='socket_nomodel_', dir=test_dir)
    try:
        ok = check_rejected(os.path.join(tmp, 'sktReject'))
        ok = check_accepted(os.path.join(tmp, 'sktAccept')) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if ok:
        print("\nPASS: a parameterizable socket shell without a model is rejected at db")
        return 0
    print("\nFAIL: the socket-without-model rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
