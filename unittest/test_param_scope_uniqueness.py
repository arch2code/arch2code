#!/usr/bin/env python3
"""A block's params: name resolves through its file's include chain to
exactly one visible ipParameters declaration; two visible declarations of
one name are rejected naming every declaring file. A definitions-only file
may declare a parameter with no consumer of its own.

Fixtures cover a duplicate within one file, across two included files, and
the definitions-only case, which builds. A duplicate check fires mid-parse,
so one cell proves it still catches a duplicate declared out of section order."""

import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectOpen

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')


def _header(name):
    print(f"\n{'='*70}\nTest: {name}\n{'='*70}")


def _copy_fixture(name, prefix):
    fixture = os.path.join(test_dir, 'fixtures', name)
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    shutil.copytree(fixture, work, dirs_exist_ok=True)
    return work


def _build_db(work, project_file):
    db = os.path.join(work, 'scope.db')
    project = os.path.join(work, 'yaml', project_file)
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, ARCH2CODE, '--yaml', project, '--db', db],
        capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
    return result.stdout + result.stderr, result.returncode


def _read(work, yaml_file):
    with open(os.path.join(work, 'yaml', yaml_file)) as f:
        return f.read()


def _write(work, yaml_file, content):
    with open(os.path.join(work, 'yaml', yaml_file), 'w') as f:
        f.write(content)


def _rename_declaration(work, yaml_file, old_name, new_name):
    """Fault-inject a temp copy: rename a constant declaration and every line
    naming it, so the fixture keeps parsing but no longer duplicates the name."""
    path = os.path.join(work, 'yaml', yaml_file)
    with open(path) as f:
        content = f.read()
    content = re.sub(rf'\b{old_name}\b', new_name, content)
    with open(path, 'w') as f:
        f.write(content)


def _declares_constant(work, yaml_file, name):
    """True if yaml_file declares `name` as an ipParameters or plain constant."""
    parsed = yaml.safe_load(_read(work, yaml_file))
    ipParameters = parsed.get('ipParameters') or {}
    if name in (ipParameters.get('constants') or {}):
        return True
    return name in (parsed.get('constants') or {})


def test_dup_declared_in_referring_and_included_file():
    _header("params: name declared in the referring file and an included file")
    work = _copy_fixture('param-scope-dup-own-file', 'param_scope_own_')
    try:
        if not (_declares_constant(work, 'psaTop.yaml', 'SHARED_W')
                and _declares_constant(work, 'psaIncluded.yaml', 'SHARED_W')):
            print("  FAIL: premise not met - SHARED_W must be an ipParameters "
                  "constant in both psaTop.yaml and psaIncluded.yaml")
            return False
        print("  PASS: premise holds, SHARED_W is declared in both files")

        out, rc = _build_db(work, 'psaProject.yaml')
        if rc == 0:
            print("  FAIL: expected rejection, build succeeded")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean error")
            return False
        missing = [p for p in ('psaTop.yaml', 'psaIncluded.yaml',
                                'more than one visible declaration')
                   if p not in out]
        if missing:
            print(f"  FAIL: expected patterns not found: {missing}")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: rejected, naming both declaring files")

        _rename_declaration(work, 'psaIncluded.yaml', 'SHARED_W', 'OTHER_W')
        out, rc = _build_db(work, 'psaProject.yaml')
        if rc != 0:
            print("  FAIL: fault-injected copy (declarations no longer "
                  "duplicated) should have built")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: fault-injected copy (renamed the included declaration) builds")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_dup_declared_own_file_ipparameters_below_blocks():
    _header("the referring file's own duplicate is caught even authored "
            "below its blocks: section")
    work = _copy_fixture('param-scope-dup-own-file', 'param_scope_reorder_')
    try:
        reordered = """include:
    - psaIncluded.yaml

blocks:
    top:
        desc: "Root"
    psaLeaf:
        desc: "Names SHARED_W, reachable through two visible declarations"
        params: [SHARED_W]

ipParameters:
    constants:
        SHARED_W: { value: 4, maxValue: 16, desc: "declared in the referring file" }

instances:
    uTop:  { container: top, instanceType: top }
    uLeaf: { container: top, instanceType: psaLeaf, variant: v0 }

parameters:
    psaLeaf:
        v0:
            SHARED_W: 4
"""
        _write(work, 'psaTop.yaml', reordered)
        if not (_declares_constant(work, 'psaTop.yaml', 'SHARED_W')
                and _declares_constant(work, 'psaIncluded.yaml', 'SHARED_W')):
            print("  FAIL: premise not met - SHARED_W must be an ipParameters "
                  "constant in both psaTop.yaml and psaIncluded.yaml")
            return False
        parsed = yaml.safe_load(_read(work, 'psaTop.yaml'))
        if list(parsed).index('blocks') > list(parsed).index('ipParameters'):
            print("  FAIL: premise not met - blocks: must sit above "
                  "ipParameters: in this copy")
            return False
        print("  PASS: premise holds, SHARED_W is declared in both files and "
              "psaTop.yaml authors blocks: above its own ipParameters:")

        out, rc = _build_db(work, 'psaProject.yaml')
        if rc == 0:
            print("  FAIL: expected rejection, build succeeded")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean error")
            return False
        missing = [p for p in ('psaTop.yaml', 'psaIncluded.yaml',
                                'more than one visible declaration')
                   if p not in out]
        if missing:
            print(f"  FAIL: expected patterns not found: {missing}")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: rejected, naming both declaring files, section order "
              "notwithstanding")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_dup_declared_in_two_included_files():
    _header("params: name declared in two included files")
    work = _copy_fixture('param-scope-dup-included-files', 'param_scope_incl_')
    try:
        if not (_declares_constant(work, 'psbDeclA.yaml', 'DUP_W')
                and _declares_constant(work, 'psbDeclB.yaml', 'DUP_W')):
            print("  FAIL: premise not met - DUP_W must be an ipParameters "
                  "constant in both psbDeclA.yaml and psbDeclB.yaml")
            return False
        print("  PASS: premise holds, DUP_W is declared in both included files")

        out, rc = _build_db(work, 'psbProject.yaml')
        if rc == 0:
            print("  FAIL: expected rejection, build succeeded")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean error")
            return False
        missing = [p for p in ('psbDeclA.yaml', 'psbDeclB.yaml',
                                'more than one visible declaration')
                   if p not in out]
        if missing:
            print(f"  FAIL: expected patterns not found: {missing}")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: rejected, naming both declaring files")

        _rename_declaration(work, 'psbDeclB.yaml', 'DUP_W', 'OTHER_W')
        out, rc = _build_db(work, 'psbProject.yaml')
        if rc != 0:
            print("  FAIL: fault-injected copy (declarations no longer "
                  "duplicated) should have built")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: fault-injected copy (renamed the second declaration) builds")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_shared_definitions_file_consumed_by_two_including_files():
    _header("one declaration in a definitions-only file, two including consumers")
    work = _copy_fixture('param-scope-shared-definitions', 'param_scope_shared_')
    try:
        defsParsed = yaml.safe_load(_read(work, 'pscDefs.yaml'))
        if 'blocks' in defsParsed:
            print("  FAIL: premise not met - pscDefs.yaml must declare no blocks:")
            return False
        if not _declares_constant(work, 'pscDefs.yaml', 'SHARED_C'):
            print("  FAIL: premise not met - SHARED_C must be an ipParameters "
                  "constant in pscDefs.yaml")
            return False
        print("  PASS: premise holds, pscDefs.yaml declares SHARED_C and no blocks:")

        out, rc = _build_db(work, 'pscProject.yaml')
        if rc != 0:
            print("  FAIL: expected success, build failed")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: build succeeded")

        prj = projectOpen(os.path.join(work, 'scope.db'))
        g.cur.execute(
            "SELECT b.block AS block, c._context AS ctx "
            "FROM blocksparams bp "
            "JOIN blocks b ON b.blockKey = bp.blockKey "
            "JOIN constants c ON c.constantKey = bp.paramSourceKey "
            "WHERE bp.param = 'SHARED_C'")
        resolved = {row['block']: row['ctx'] for row in g.cur.fetchall()}
        if set(resolved) != {'pscSrc', 'pscChk'}:
            print(f"  FAIL: expected pscSrc and pscChk to consume SHARED_C, "
                  f"resolved {sorted(resolved)}")
            return False
        contexts = set(resolved.values())
        if len(contexts) != 1 or not next(iter(contexts)).endswith('pscDefs.yaml'):
            print(f"  FAIL: expected both blocks' paramSourceKey to resolve to "
                  f"a constant declared in pscDefs.yaml, got {resolved}")
            return False
        print("  PASS: both blocks' paramSourceKey resolve to SHARED_C in "
              "pscDefs.yaml")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    print("\n" + "="*70)
    print("PARAM SCOPE UNIQUENESS TESTS")
    print("="*70)

    tests = [
        test_dup_declared_in_referring_and_included_file,
        test_dup_declared_own_file_ipparameters_below_blocks,
        test_dup_declared_in_two_included_files,
        test_shared_definitions_file_consumed_by_two_including_files,
    ]
    results = []
    for test_func in tests:
        try:
            results.append((test_func.__name__, test_func()))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    print("\n" + "="*70 + "\nTEST SUMMARY\n" + "="*70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    if passed == len(results):
        print("\n  ALL TESTS PASSED!")
        return 0
    print("\n  SOME TESTS FAILED")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
