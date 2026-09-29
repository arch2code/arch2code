#!/usr/bin/env python3
"""A testbench `GENERATED_CODE_PARAM` line must not carry `--variant=` for a
DUT block that declares no `params:`.

`intf_gen_utils.resolve_dut_variant_selection` used to accept the variant
unconditionally on the no-own-params path and pass it straight through as the
`instanceFactory` key, so a stale `--variant=<name>` on a plain block's
testbench silently selected a factory variant that does not exist. It must
now `printError` and fail the build instead.

Copies the `helloWorld` example (whose `helloWorld` block declares no
`params:`), appends `--variant=bogus` to its testbench's
`GENERATED_CODE_PARAM` line, and checks `make gen` rejects it by name; then
restores the line and checks `make gen` passes again.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(base_dir, 'examples', 'helloWorld')
TB_RELPATH = os.path.join('tb', 'helloWorld', 'helloWorldTestbench.cppm')

PARAM_LINE_ORIGINAL = "// GENERATED_CODE_PARAM --block=helloWorld --mode=module\n"
PARAM_LINE_BOGUS = "// GENERATED_CODE_PARAM --block=helloWorld --mode=module --variant=bogus\n"


def copy_fixture(project):
    shutil.copytree(
        FIXTURE, project,
        ignore=shutil.ignore_patterns(
            'rundir', '.cache', '.gen', '*.db', '*.db-*', '*.log',
            'compile_commands.json'))


def set_param_line(project, line):
    path = os.path.join(project, TB_RELPATH)
    with open(path) as f:
        text = f.read()
    if PARAM_LINE_ORIGINAL not in text and PARAM_LINE_BOGUS not in text:
        raise RuntimeError(f"expected GENERATED_CODE_PARAM line not found in {path}")
    text = text.replace(PARAM_LINE_ORIGINAL, line).replace(PARAM_LINE_BOGUS, line)
    with open(path, 'w') as f:
        f.write(text)


def env():
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    return e


def make(targets, project, e):
    # Each target is its own invocation, mirroring `make db && make gen -j`.
    text = ''
    returncode = 0
    for target in targets:
        cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
               '-j8', target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=e)
        text += result.stdout + result.stderr
        returncode = result.returncode
        if result.returncode != 0:
            break
    return text, returncode


def _header(name):
    print("\n" + "=" * 70)
    print(f"Test: {name}")
    print("=" * 70)


def test_stale_variant_rejected_then_cleared():
    _header("--variant= on a params-less block's testbench fails gen; clean gen passes")
    ok = True
    tmp = tempfile.mkdtemp(prefix='tb_variant_plain_block_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'helloWorld')
        copy_fixture(project)
        e = env()

        text, rc = make(['db'], project, e)
        if rc != 0:
            raise RuntimeError(f"make db failed unexpectedly:\n{text}")

        set_param_line(project, PARAM_LINE_BOGUS)
        text, rc = make(['gen'], project, e)
        if rc == 0:
            print("  FAIL: make gen succeeded with a stale --variant= on a "
                  "params-less block")
            ok = False
        if 'Traceback' in text:
            print(f"  FAIL: make gen crashed instead of failing cleanly:\n{text}")
            ok = False
        for needle in ("helloWorld", "bogus", "declares no params", "--variant="):
            if needle not in text:
                print(f"  FAIL: gen output missing substring {needle!r}:\n{text}")
                ok = False
        if ok:
            print("  ok: gen rejected the stale --variant= with the expected message")

        set_param_line(project, PARAM_LINE_ORIGINAL)
        text, rc = make(['gen'], project, e)
        if rc != 0:
            print(f"  FAIL: make gen failed after restoring the clean param line:\n{text}")
            ok = False
        else:
            print("  ok: gen passes again once --variant= is removed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if ok:
        print("  PASS")
    return ok


def run_all_tests():
    print("=" * 70)
    print("TESTING: --variant= rejected on a params-less block's testbench")
    print("=" * 70)
    result = test_stale_variant_rejected_then_cleared()
    print("\n" + "=" * 70)
    print(f"  {'PASS' if result else 'FAIL'}")
    print("=" * 70)
    return 0 if result else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
