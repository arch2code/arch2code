#!/usr/bin/env python3
"""A socket shell (hasSkt: true) on a parameterizable block is registered by
the assembler's trampoline registrar, not by the shell itself.

The shell is a `template<typename Config>` class, and the Config an instance
binds is the parent's choice, so the parent-owned registrar
(templates/systemc/blockRegistrar.py) emits one `<block>_socket` registration
per variant next to the `<block>_model` rows. The shell is a C++20 module
unit, `<block>Socket.cppm`, that carries no registration and no explicit
instantiation: the registrar imports it and instantiates it at each Config.

The fixture is parameterized-top under an unparameterized root (the shape
test_error_parameterized_top.py's accepted arm uses), with the harness block
given hasSkt, hasMdl and a second variant. `make db newmodule gen` then yields
the registrar and the shell files this test reads.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'parameterized-top')
ARCH = os.path.join('yaml', 'ptTop.yaml')
PROJECT_YAML = os.path.join('prj', 'yaml', 'ptProject.yaml')

EDITS = [
    ('blocks:\n',
     'blocks:\n'
     '    ptRoot:\n'
     '        desc: "Unparameterized root holding the harness"\n'
     '        hasMdl: true\n'
     '        hasTb: false\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'),
    # Anchored on the harness block's own params: line, so the flags land on
    # the parameterizable block and nowhere else.
    ('        params: [PT_WIDTH]\n'
     '        hasMdl: false\n',
     '        params: [PT_WIDTH]\n'
     '        hasSkt: true\n'
     '        hasMdl: true\n'),
    ('    ptTop_tb: { container: ptTop_tb,',
     '    ptRoot:   { container: ptRoot, instanceType: ptRoot, instGroup: top }\n'
     '    ptTop_tb1: { container: ptRoot, instanceType: ptTop_tb, instGroup: top, variant: ptV1 }\n'
     '    ptTop_tb: { container: ptRoot,'),
    ('        ptV0:\n'
     '            PT_WIDTH: 8\n',
     '        ptV0:\n'
     '            PT_WIDTH: 8\n'
     '        ptV1:\n'
     '            PT_WIDTH: 16\n'),
]
REPOINT_TOP = [('topInstance: ptTop_tb', 'topInstance: ptRoot')]

VARIANTS = ['ptV0', 'ptV1']


def make(project, *targets):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    text = ''
    for target in targets:
        cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
               '-j8', target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                                env=env)
        text += result.stdout + result.stderr
        if result.returncode != 0:
            raise RuntimeError(f"make {target} failed (rc={result.returncode}):\n{text}")
    return text


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


def read(project, relative):
    path = os.path.join(project, relative)
    if not os.path.exists(path):
        raise RuntimeError(f"expected generated file {path}")
    with open(path) as f:
        return f.read()


def registration_variants(text, kind):
    # The variant label is the first string argument after the lambda.
    pattern = re.compile(
        rf'registerBlock\(\s*"ptTop_tb_{kind}",.*?\}},\s*"([^"]*)",\s*"([^"]*)"\);',
        re.S)
    return {(variant, project) for variant, project in pattern.findall(text)}


def check_registrar(project):
    ok = True
    text = read(project, os.path.join('registrar', 'ptTop_tbRegistrar.cppm'))
    if not re.search(r'^import ptTest_ptTop_tb\.socket;', text, re.M):
        print("  FAIL: registrar does not import the socket shell module")
        ok = False
    if 'Socket.h"' in text:
        print("  FAIL: registrar still includes a socket shell header")
        ok = False
    model = registration_variants(text, 'model')
    socket = registration_variants(text, 'socket')
    if not model:
        print("  FAIL: registrar emits no _model registration")
        ok = False
    if socket != model:
        print(f"  FAIL: _socket rows {sorted(socket)} differ from _model rows {sorted(model)}")
        ok = False
    for variant in VARIANTS:
        if not any(v == variant for v, _ in socket):
            print(f"  FAIL: no _socket registration for variant {variant}")
            ok = False
        if f'ptTop_tbSocket<' not in text:
            print("  FAIL: _socket registration does not construct the templated shell")
            ok = False
            break
    if ok:
        print(f"  PASS: registrar emits _socket rows {sorted(socket)} matching the _model rows")
    return ok


def check_shell(project):
    ok = True
    for relative in (os.path.join('base', 'ptTop_tbSocket.h'),
                     os.path.join('base', 'ptTop_tbSocket.cpp'),
                     os.path.join('base', 'ptTop_tbSocket.cppm')):
        if os.path.exists(os.path.join(project, relative)):
            print(f"  FAIL: {relative} was scaffolded; the shell is model/ptTop_tbSocket.cppm only")
            ok = False
    text = read(project, os.path.join('model', 'ptTop_tbSocket.cppm'))
    if not re.search(r'^export module ptTest_ptTop_tb\.socket;', text, re.M):
        print("  FAIL: the shell does not declare its socket module")
        ok = False
    if 'registerBlock' in text:
        print("  FAIL: the shell still registers itself")
        ok = False
    # Every importer sees the member definitions, so no Config is named here.
    if re.search(r'^template ptTop_tbSocket<', text, re.M):
        print("  FAIL: the shell still explicitly instantiates its constructor")
        ok = False
    if not re.search(r'^template<typename Config>\nptTop_tbSocket<Config>::ptTop_tbSocket\(', text, re.M):
        print("  FAIL: the shell does not define its templated constructor in the module unit")
        ok = False
    if ok:
        print("  PASS: the shell is a module unit with its definitions, no registration and no instantiation list")
    return ok


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='socket_param_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'sktParam')
        shutil.copytree(FIXTURE, project)
        edit_yaml(project, ARCH, EDITS)
        edit_yaml(project, PROJECT_YAML, REPOINT_TOP)
        make(project, 'clean', 'db', 'newmodule', 'gen')
        ok = check_registrar(project)
        ok = check_shell(project) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if ok:
        print("\nPASS: a parameterizable socket shell is registered by the trampoline registrar")
        return 0
    print("\nFAIL: parameterizable socket shell registration is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
