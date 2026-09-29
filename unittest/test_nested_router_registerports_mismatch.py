#!/usr/bin/env python3
"""A container hosting a nested register-bus router must declare a
registerPorts: key that matches the nested router's addressBlock.upstreamPort.

`container` hosts `nestedApbDecode` and is itself a routed leaf of the
primary router `apbDecode`. The boundary connectionMap that feeds the
nested router wires the container's own registerPorts port straight
through, by name, to the nested router's upstreamPort, so a mismatched
key is rejected at `make db`. The fixture's checked-in key ('regBus')
does not match the nested router's upstreamPort ('apbReg'); the test also
asserts the corrected key passes.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'nested-router-registerports-mismatch')
ARCH_YAML = 'yaml/nrpm.yaml'

EXPECTED_PATTERNS = [
    'container',
    'registerPorts',
    'regBus',
    'nestedApbDecode',
    'upstreamPort',
    'apbReg',
]


def copy_fixture(project):
    shutil.copytree(
        FIXTURE, project,
        ignore=shutil.ignore_patterns('*.db', '*.db-*', '.gen', 'build'))


def env():
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    return e


def make(target, project, e):
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           '-j8', target]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=e)


def require_make(target, project, e):
    result = make(target, project, e)
    if result.returncode != 0:
        raise RuntimeError(
            f"make {target} failed:\n{result.stdout}\n{result.stderr}")
    return result


def run_negative(e, tmp):
    project = os.path.join(tmp, 'nrpmMismatch')
    copy_fixture(project)

    require_make('clean', project, e)
    result = make('db', project, e)

    full_output = result.stdout + '\n' + result.stderr
    if result.returncode == 0:
        print("FAIL: make db succeeded; a container's registerPorts: key "
              "must match the nested router's upstreamPort")
        return False

    if 'Traceback (most recent call last):' in full_output:
        print("FAIL: got a Python stack trace instead of a clean error")
        print(full_output)
        return False

    missing = [p for p in EXPECTED_PATTERNS if p.lower() not in full_output.lower()]
    if missing:
        print(f"FAIL: missing expected patterns: {missing}")
        print(full_output)
        return False

    print("PASS: make db rejects the mismatched registerPorts: key, naming "
          "the container, the key, the nested router, and its upstreamPort")
    return True


def run_positive(e, tmp):
    project = os.path.join(tmp, 'nrpmMatched')
    copy_fixture(project)

    arch_path = os.path.join(project, ARCH_YAML)
    with open(arch_path) as f:
        content = f.read()
    fixed = content.replace(
        'regBus: { interface: apbReg }', 'apbReg: { interface: apbReg }')
    if fixed == content:
        print("FAIL: expected registerPorts: key text not found to correct")
        return False
    with open(arch_path, 'w') as f:
        f.write(fixed)

    require_make('clean', project, e)
    result = require_make('db', project, e)
    print("PASS: make db succeeds once the registerPorts: key matches the "
          "nested router's upstreamPort")
    return True


def run_all_tests():
    e = env()
    tmp = tempfile.mkdtemp(prefix='nested_router_registerports_', dir=test_dir)
    try:
        ok = run_negative(e, tmp)
        ok = run_positive(e, tmp) and ok
        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    try:
        sys.exit(0 if run_all_tests() else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
