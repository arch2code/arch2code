#!/usr/bin/env python3
"""A socket shell (hasSkt: true) on a parameterizable block is rejected at db.

A parameterizable block's factory registration is owned by the per-assembler
trampoline registrar (templates/systemc/blockRegistrar.py), which registers the
model and verif kinds only. The socket shell templates still self-register
through one explicit instantiation per variant, the scheme the trampoline
replaced, so a parameterizable block's socket shell would register under a
Config the assembler never binds. `validateSocketOnParameterizedBlock`
(`pysrc/processYaml.py`) rejects the combination at `make db`, naming the
block, instead of letting it fail in generated C++.

The fixture is the parameterized-top one, placed under an unparameterized root
exactly as test_error_parameterized_top.py's accepted arm does, so the only
rule that can reject it here is the socket rule. Two arms: hasSkt on the
parameterizable harness block is rejected; hasSkt on the unparameterized root
is accepted.
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

# Anchored on the harness block's own params: line, so the flag lands on the
# parameterizable block and nowhere else.
SOCKET_ON_PARAMETERIZED = [
    ('        params: [PT_WIDTH]\n',
     '        params: [PT_WIDTH]\n'
     '        hasSkt: true\n'),
]
SOCKET_ON_ROOT = [
    ('        desc: "Unparameterized root holding the harness"\n',
     '        desc: "Unparameterized root holding the harness"\n'
     '        hasSkt: true\n'),
]

REQUIRED_SUBSTRINGS = [
    "Block 'ptTop_tb' declares hasSkt: true but is parameterizable",
    "trampoline registrar",
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
    edit_yaml(project, ARCH, SOCKET_ON_PARAMETERIZED)
    rc, output = make_db(project)
    if rc == 0:
        print("  FAIL: make db accepted hasSkt on a parameterizable block")
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
    print("  PASS: hasSkt on a parameterizable block is rejected, naming the block")
    return True


def check_accepted(project):
    prepare(project)
    edit_yaml(project, ARCH, SOCKET_ON_ROOT)
    rc, output = make_db(project)
    if rc != 0:
        print(f"  FAIL: make db rejected hasSkt on an unparameterized block (rc={rc})")
        print(output)
        return False
    print("  PASS: hasSkt on an unparameterized block is accepted")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='socket_param_', dir=test_dir)
    try:
        ok = check_rejected(os.path.join(tmp, 'sktReject'))
        ok = check_accepted(os.path.join(tmp, 'sktAccept')) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if ok:
        print("\nPASS: a socket shell on a parameterizable block is rejected at db")
        return 0
    print("\nFAIL: the socket-on-parameterizable rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
