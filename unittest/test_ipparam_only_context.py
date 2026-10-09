#!/usr/bin/env python3
"""A context whose only content is `ipParameters:` generates and builds.

The fixture's one design file declares `LEAF_W` under `ipParameters:` and
nothing under `constants:`, `types:` or `structures:`, so the context emits no
package and no Includes.cppm. The RTL container `ipp` instantiates the
parameterized `leaf` and lists the context in its `includeContext`, so the
generators meet a context with no emitted files. With no context in the project
emitting a package, INCLUDEFILES carries no `package_sv` key at all.

The suite copies the fixture to a temp tree and runs the same make targets a
user runs: `db`, `newmodule`, `gen`, then `lint` in `rtl/` and `run` in
`rundir/`. Before `gen` it fills the scaffolded testbench's user regions with
one empty test and an end-of-test voter, so the run ends and passes. After
`gen` it checks that no file imports the context's package or module.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'ipparam-only-context')
CONTEXT_IMPORT = re.compile(r'^\s*import\s+(ipp_package\b|ipp\s*;)', re.MULTILINE)
BUILD_JOBS = '8'

EXTERNAL = os.path.join('tb', 'ipp', 'ippExternal.cppm')
# Fills the scaffold's user regions as its own comments describe: the seeded
# placeholder test runs as an ADD_TEST and one voter waits for it. Anchored on
# the scaffold's text, so a scaffold reword fails here rather than leaving a run
# that never ends.
TESTBENCH = [
    ('// Plain non-modular headers, including any whose definitions live in a .cpp.\n',
     '// Plain non-modular headers, including any whose definitions live in a .cpp.\n'
     '#include "testController.h"\n'),
    ('    // external implementation members\n',
     '    // external implementation members\n'
     '    void test_replace_me(void)\n'
     '    {\n'
     '    }\n'
     '\n'
     '    void endOfTestVoter(void)\n'
     '    {\n'
     '        endOfTest eot(true);\n'
     '        testController::GetInstance().wait_all_tests_complete();\n'
     '        eot.setEndOfTest(true);\n'
     '    }\n'),
    ('    // ADD_TEST(test_replace_me);\n', '    ADD_TEST(test_replace_me);\n'),
    ('    // SC_THREAD(endOfTestVoter);\n', '    SC_THREAD(endOfTestVoter);\n'),
]


def make(target, project, *, directory=None, jobs=None):
    """Run one make target against the temp copy, with both roots overridden."""
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-C', directory or project,
           f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}']
    if jobs:
        cmd.append(f'-j{jobs}')
    cmd.append(target)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, env=env)
    return result.returncode, result.stdout + result.stderr


def fill_testbench(project):
    path = os.path.join(project, EXTERNAL)
    with open(path) as f:
        text = f.read()
    for old, new in TESTBENCH:
        if old not in text:
            raise RuntimeError(f"{EXTERNAL} no longer carries the anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def context_importers(project):
    """Every file under the project that imports the context's package or module."""
    found = []
    for root, _dirs, files in os.walk(project):
        for name in files:
            path = os.path.join(root, name)
            with open(path, errors='ignore') as f:
                if CONTEXT_IMPORT.search(f.read()):
                    found.append(os.path.relpath(path, project))
    return found


def check(project):
    for target in ('db', 'newmodule', 'gen'):
        if target == 'gen':
            fill_testbench(project)
        rc, output = make(target, project, jobs=BUILD_JOBS if target == 'gen' else None)
        if rc != 0:
            print(f"  FAIL: make {target} failed (rc={rc})")
            print(output)
            return False
    print("  PASS: make db, newmodule and gen succeed")

    importers = context_importers(project)
    if importers:
        print(f"  FAIL: these files import the ipParameters-only context: {importers}")
        return False
    print("  PASS: no file imports ipp_package or ipp")

    rc, output = make('lint', project, directory=os.path.join(project, 'rtl'))
    if rc != 0:
        print(f"  FAIL: make lint failed (rc={rc})")
        print(output)
        return False
    print("  PASS: make lint succeeds on the generated RTL")

    rc, output = make('run', project, directory=os.path.join(project, 'rundir'),
                      jobs=BUILD_JOBS)
    if rc != 0:
        print(f"  FAIL: make run failed (rc={rc})")
        print(output)
        return False
    print("  PASS: the model builds and runs")
    return True


def main():
    print("Test: a context with only ipParameters: generates, lints and runs")
    tmp = tempfile.mkdtemp(prefix='ipparam_only_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'ipp')
        shutil.copytree(FIXTURE, project)
        ok = check(project)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
