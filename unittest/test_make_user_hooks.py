#!/usr/bin/env python3
"""Each EXTRA_* user hook set in shared.mk reaches its own tool command only.

Works on a private copy of examples/simple_ip whose include/make/shared.mk
appends one distinct value to every tool hook. Checks:
- EXTRA_GEN_OPTS on the db build, every gen call and newmodule of the project;
- VERILATOR_USER_OPTS and EXTRA_VERILATOR_OPTS on lint and on every model
  verilate, EXTRA_LINT_OPTS on lint only, EXTRA_VL_OPTS on the verilates only;
- EXTRA_VL_CFLAGS inside the single quoted -CFLAGS argument of each verilate;
- EXTRA_VL_LIB_OBJS, named under $(A2C_VL_BUILD_DIR), added to the archive and
  ordered after every verilate, in the verilation sub-make that reads only
  shared.mk;
- make help-hooks prints every value.
"""

import os
import shlex
import sys

from test_file_prefix import copy_simple_ip, make, remove, run

HOOK_VALUES = {
    'EXTRA_GEN_OPTS': '--debug',
    'VERILATOR_USER_OPTS': '-DHOOK_USER',
    'EXTRA_VERILATOR_OPTS': '-DHOOK_VERILATOR',
    'EXTRA_LINT_OPTS': '-DHOOK_LINT',
    'EXTRA_VL_OPTS': '-DHOOK_VL',
    'EXTRA_VL_CFLAGS': '-DHOOK_CFLAG',
    'EXTRA_VL_LIB_OBJS': '$(A2C_VL_BUILD_DIR)/obj_dir/hook/hook.o',
}
LINT_ONLY = {'-DHOOK_LINT'}
VL_ONLY = {'-DHOOK_VL'}
BOTH = {'-DHOOK_USER', '-DHOOK_VERILATOR'}


def dryRun(directory, *args):
    result = run(['make', '-C', directory, '--no-print-directory', '-n', *args])
    if result.returncode != 0:
        raise AssertionError(f"make -n {' '.join(args)} failed in {directory}:\n"
                             f"{result.stdout}\n{result.stderr}")
    return result.stdout


def commands(output, tool):
    # Echoed recipe lines whose first word is `tool`, as token lists.
    found = []
    for line in output.splitlines():
        words = line.split()
        if words and os.path.basename(words[0]) == tool:
            found.append(shlex.split(line))
    return found


def checkVerilator(label, cmds, want, notWant):
    failures = []
    if not cmds:
        return [f"{label}: no verilator command"]
    for tokens in cmds:
        missing = want - set(tokens)
        leaked = notWant & set(tokens)
        if missing:
            failures.append(f"{label}: verilator lacks {sorted(missing)}")
        if leaked:
            failures.append(f"{label}: verilator carries {sorted(leaked)}")
    return failures


def main():
    work = copy_simple_ip()
    try:
        shared = os.path.join(work, 'include', 'make', 'shared.mk')
        with open(shared, 'a') as f:
            f.write(''.join(f'{name} += {value}\n' for name, value in HOOK_VALUES.items()))
        rundir = os.path.join(work, 'rundir')
        vlBuildDir = os.path.join(rundir, 'build', 'vl')
        hookObj = os.path.join(vlBuildDir, 'obj_dir', 'hook', 'hook.o')
        failures = []

        # The reused sub-projects build from their own shared.mk, without the hooks.
        rootDb = os.path.join(work, 'simple_ip.db')

        def genCalls(output):
            return [c for c in commands(output, 'arch2code.py') if c[c.index('--db') + 1] == rootDb]

        for target, output in (('db', make(work, 'db')), ('gen', dryRun(work, 'gen')),
                               ('newmodule', dryRun(work, 'newmodule'))):
            calls = genCalls(output)
            lacking = [' '.join(c) for c in calls if '--debug' not in c]
            if not calls or lacking:
                failures.append(f"{target}: arch2code.py lacks EXTRA_GEN_OPTS: {lacking or 'no call'}")

        lint = dryRun(os.path.join(work, 'rtl'), 'lint')
        failures += checkVerilator('lint', commands(lint, 'verilator'),
                                   BOTH | LINT_ONLY, VL_ONLY | {'-DHOOK_CFLAG'})

        vl = dryRun(rundir, 'all', 'VL_DUT=1')
        verilates = commands(vl, 'verilator')
        failures += checkVerilator('model wrapping', verilates, BOTH | VL_ONLY, LINT_ONLY)
        for tokens in verilates:
            cflags = tokens[tokens.index('-CFLAGS') + 1]
            if not cflags.startswith('-std=') or not cflags.endswith(' -DHOOK_CFLAG'):
                failures.append(f"-CFLAGS argument does not end in EXTRA_VL_CFLAGS: {cflags!r}")
        if f'echo "ADDMOD {hookObj}"' not in vl:
            failures.append(f"archive script does not ADDMOD {hookObj}")

        # The ordering rule, read from the sub-make's own database.
        os.makedirs(vlBuildDir, exist_ok=True)
        database = run(['make', '-C', vlBuildDir, '-pq', '-f',
                        os.path.join(work, '..', '..', 'include', 'make', 'a2c-vl-build-entry.mk'),
                        'vlwrap', f'REPO_ROOT={work}']).stdout
        rules = [line for line in database.splitlines() if line.startswith(f'{hookObj}:')]
        tops = [t for t in verilates if '--Mdir' in t]
        mdirs = [t[t.index('--Mdir') + 1] for t in tops]
        if len(rules) != 1:
            failures.append(f"expected one rule for {hookObj}, found {rules}")
        else:
            missing = [m for m in mdirs if m not in rules[0]]
            if missing:
                failures.append(f"{hookObj} is not ordered after {missing}: {rules[0]}")

        hooks = run(['make', '-C', rundir, '--no-print-directory', 'help-hooks']).stdout
        for name, value in HOOK_VALUES.items():
            shown = hookObj if name == 'EXTRA_VL_LIB_OBJS' else value
            lines = [line for line in hooks.splitlines() if line.startswith(f'{name} ')]
            if len(lines) != 1 or not lines[0].endswith(f': {shown}'):
                failures.append(f"help-hooks does not show {name} = {shown}: {lines}")

        if failures:
            for failure in failures:
                print(f"FAIL: {failure}")
            print("SOME TESTS FAILED")
            return 1
        print(f"PASS: {len(HOOK_VALUES)} hooks set in shared.mk reach only their own "
              f"commands ({len(verilates)} verilates, 1 lint)")
        print("ALL TESTS PASSED")
        return 0
    finally:
        remove(work)


if __name__ == '__main__':
    sys.exit(main())
