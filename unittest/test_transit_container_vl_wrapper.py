#!/usr/bin/env python3
"""A hasVl block with no own params: still gets a buildable wrapper body.

`top` is isParameterizable only because it transits a parameter-typed channel
between two contained, parameterized children (leafA, leafB) frozen at
variant `v0`. Its own SystemVerilog module has no #(parameter...) port list,
so the canonical wrapper body (the --section=body .svh) must take the same
non-parameterizable shape an ordinary block's body does, not the templated
shape that assumes a param_names() list to spell against.

Db and generation only: this is a template-dispatch regression guard, not an
end-to-end build.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'transit-vl-wrapper')
WRAPPER_SVH = 'top_hdl_sv_wrapper.svh'


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
        require_make('db', project, e)
        require_make('newmodule', project, e)
        require_make('gen', project, e)

        wrapperPath = os.path.join(project, 'verif', WRAPPER_SVH)
        if not os.path.exists(wrapperPath):
            print(f"FAIL: {WRAPPER_SVH} was not scaffolded; the transit "
                  f"container lost its isParameterizable flag")
            return False
        with open(wrapperPath) as f:
            body = f.read()
        if re.search(r'^\s*#\(\s*$', body, re.MULTILINE):
            print(f"FAIL: {WRAPPER_SVH} carries a #(parameter...) list, but "
                  f"'top' declares no params: of its own:\n{body}")
            return False
        print(f"PASS: make gen completes and {WRAPPER_SVH} carries no "
              f"#(parameter...) list")
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
