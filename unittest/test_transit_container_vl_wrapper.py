#!/usr/bin/env python3
"""A hasRtl container with no own params: cannot transit a parameterized
channel between contained children.

`top` is hasVl/hasRtl and declares no params: of its own; it hosts two
parameterized children (leafA, leafB) joined by a parameter-typed channel,
each frozen at variant v0. Its generated SystemVerilog module would have to
instantiate that channel as `<if> #(.data_t(<paramStruct>))` with no typedef
in scope, so `make db` must reject this shape.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'transit-vl-wrapper')

EXPECTED_PATTERNS = [
    'top',
    'hasRtl',
    'xferIf',
    'uLeafA',
    'uLeafB',
    'params:',
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


def run_all_tests():
    e = env()
    tmp = tempfile.mkdtemp(prefix='transit_vl_wrapper_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'transitVl')
        copy_fixture(project)

        require_make('clean', project, e)
        result = make('db', project, e)

        full_output = result.stdout + '\n' + result.stderr
        if result.returncode == 0:
            print("FAIL: make db succeeded; a hasRtl container with no "
                  "params: must reject a parameterized channel between its "
                  "contained children")
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

        print("PASS: make db rejects the hasRtl transit container with no "
              "params:, naming the block, channel, interface, both ends, "
              "and file")
        return True
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
