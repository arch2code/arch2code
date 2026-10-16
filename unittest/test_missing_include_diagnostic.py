#!/usr/bin/env python3
"""A deleted YAML include that is still referenced fails with one clear error.

Works on a private copy of examples/helloWorld whose testbench YAML includes
extra.yaml. After a good `make db`, deletes extra.yaml and checks that the next
`make db` fails with exactly one error, which names extra.yaml and the file
that includes it, and prints no Python traceback.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir


FIXTURE = os.path.join(base_dir, 'examples', 'helloWorld')
TB_YAML = os.path.join('arch', 'yaml', 'helloWorld_tb.yaml')
EXTRA_YAML = os.path.join('arch', 'yaml', 'extra.yaml')
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def make(project, *args):
    result = subprocess.run(['make', '-C', project, '--no-print-directory',
                             f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}', *args],
                            capture_output=True, text=True, timeout=600,
                            env=dict(os.environ, NO_COLOR='1'))
    return result, ANSI.sub('', result.stdout + result.stderr)


def main():
    failures = []

    def check(ok, message):
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        if not ok:
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix='missing_include_') as tmp:
        project = os.path.join(tmp, 'helloWorld')
        shutil.copytree(FIXTURE, project, symlinks=True, ignore=shutil.ignore_patterns(
            'rundir', '.gen', '*.db', '*.db-*', 'compile_commands.json'))
        with open(os.path.join(project, TB_YAML), 'a') as f:
            f.write('\ninclude:\n  - extra.yaml\n')
        with open(os.path.join(project, EXTRA_YAML), 'w') as f:
            f.write('constants:\n  EXTRA_CONST: {value: 1, desc: "Included constant"}\n')
        result, output = make(project, 'db')
        if result.returncode != 0:
            print(f"FAIL: make db with extra.yaml present failed:\n{output}")
            return 1

        os.remove(os.path.join(project, EXTRA_YAML))
        result, output = make(project, 'db')
        print(output.strip())
        errors = re.findall(r'^Error Number (\d+):$', output, re.MULTILINE)
        check(result.returncode != 0, "make db fails once extra.yaml is gone")
        check('Traceback' not in output, "the failure prints no Python traceback")
        check(errors == ['1'], f"exactly one error is reported (found {errors})")
        named = [l for l in output.splitlines() if 'extra.yaml' in l and 'helloWorld_tb.yaml' in l]
        check(bool(named), "the error names extra.yaml and its includer helloWorld_tb.yaml")

    if failures:
        print("SOME TESTS FAILED")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
