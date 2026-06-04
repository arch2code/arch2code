#!/usr/bin/env python3
"""Block-parameter / ipParameters-constant linkage validation and the
per-block parameterized declaration set.

Negative cases (each must fail projectCreate with a clear, traceback-free
message):
- An ipParameters constant consumed by no block param (orphan).
- A block param with no same-name ipParameters constant backing it.
- A block param backed by a non-parameterizable constant (a plain
  ``constants:`` entry colliding with the param name). This is the single
  validation behind both "backing const not marked isParameterizable" and
  "plain constant name collision with a block param" - the param resolves to a
  same-name constant that is not parameterizable.
- A variant binding that exceeds its backing constant's maxValue (worst-case
  sizing would under-allocate).

Positive case (must succeed, asserted in-process against the database):
- One exposed param consumed by two blocks, and a parameterizable type and
  structure (used only by hand-written code, not by any port/memory/register)
  selected module-local for both consuming blocks, types before structures.
"""

import os
import sqlite3
import sys
import tempfile
import subprocess


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectCreate


def _write_temp(content, suffix, prefix):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=test_dir)
    os.close(fd)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _cleanup(paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass


def _project_for(arch_path):
    arch_basename = os.path.basename(arch_path)
    project_content = f"""projectName: param_linkage_test
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {arch_basename}
"""
    return _write_temp(project_content, '_project.yaml', 'proj_linkage_')


# ----------------------------------------------------------------------------
# Negative cases: craft YAML, run arch2code, expect failure + message patterns.
# ----------------------------------------------------------------------------

def _expect_error(arch_content, expected_patterns, test_name):
    print(f"\n{'='*70}\nTest: {test_name}\n{'='*70}")
    arch_path = _write_temp(arch_content, '.yaml', 'arch_linkage_')
    project_path = _project_for(arch_path)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        cmd = [sys.executable, os.path.join(base_dir, 'arch2code.py'),
               '--yaml', project_path, '--db', db_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=test_dir, env=env)
        error_output = result.stderr + result.stdout

        if result.returncode == 0:
            print("  FAIL: expected error but build succeeded")
            return False
        if 'Traceback (most recent call last)' in error_output:
            print("  FAIL: got Python stack trace instead of clean error")
            return False
        missing = [p for p in expected_patterns if p.lower() not in error_output.lower()]
        if missing:
            print(f"  FAIL: expected patterns not found: {missing}")
            print('  ' + '\n  '.join(error_output.split('\n')[:25]))
            return False
        print(f"  PASS: got expected error (patterns {expected_patterns})")
        return True
    finally:
        _cleanup([project_path, arch_path, db_path])


def test_orphan_ipparameters_constant():
    arch = """ipParameters:
  constants:
    UNUSED_W: { value: 8, maxValue: 16, desc: "consumed by no block param" }

blocks:
  ip: { desc: "ip" }
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uIp: { container: top, instanceType: ip }
"""
    return _expect_error(
        arch,
        ["UNUSED_W", "not consumed by any", "ipParameters constant"],
        "orphan ipParameters constant")


def test_unbacked_block_param():
    arch = """blocks:
  ip:
    desc: "ip"
    params: [NO_BACKING]
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uIp: { container: top, instanceType: ip }
"""
    return _expect_error(
        arch,
        ["NO_BACKING", "no backing constant"],
        "block param without ipParameters backing")


def test_non_parameterizable_backing():
    # A block param whose same-name backing is a plain (non-parameterizable)
    # constants: entry. This is the "plain constant name collision with a block
    # param" case and the "backing const not marked isParameterizable" case -
    # one validation, reached two ways.
    arch = """constants:
  WIDTH: { value: 8, desc: "plain, non-parameterizable" }

blocks:
  ip:
    desc: "ip"
    params: [WIDTH]
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uIp: { container: top, instanceType: ip }
"""
    return _expect_error(
        arch,
        ["WIDTH", "non-parameterizable constant"],
        "block param backed by a non-parameterizable constant")


def test_variant_binding_exceeds_maxvalue():
    arch = """ipParameters:
  constants:
    W: { value: 8, maxValue: 16, desc: "backing" }

blocks:
  ip:
    desc: "ip"
    params: [W]
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uIp: { container: top, instanceType: ip, variant: big }

parameters:
  ip:
    - { variant: big, param: W, value: 64 }
"""
    return _expect_error(
        arch,
        ["big", "exceeding the backing", "maxValue"],
        "variant binding exceeds backing maxValue")


# ----------------------------------------------------------------------------
# Positive case: in-process projectCreate, then assert against the database.
# ----------------------------------------------------------------------------

def test_shared_param_two_blocks_and_decl_set():
    print(f"\n{'='*70}\nTest: shared param consumed by two blocks; "
          f"declaration set\n{'='*70}")
    arch = """ipParameters:
  constants:
    SHARED_WIDTH: { value: 8, maxValue: 16, desc: "shared exposed param" }
  types:
    sharedDataT:
      width: SHARED_WIDTH
      maxBitwidth: 16
      desc: "parameterizable type referenced only by hand-written code"

structures:
  sharedDataSt:
    payload: { varType: sharedDataT }

blocks:
  blockA:
    desc: "consumer A"
    params: [SHARED_WIDTH]
  blockB:
    desc: "consumer B"
    params: [SHARED_WIDTH]
  top:
    desc: "top"

instances:
  uTop: { container: top, instanceType: top }
  uA: { container: top, instanceType: blockA, variant: v0 }
  uB: { container: top, instanceType: blockB, variant: v0 }

parameters:
  blockA:
    - { variant: v0, param: SHARED_WIDTH, value: 12 }
  blockB:
    - { variant: v0, param: SHARED_WIDTH, value: 16 }
"""
    arch_path = _write_temp(arch, '.yaml', 'arch_linkage_pos_')
    project_path = _project_for(arch_path)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    original_cwd = os.getcwd()
    conn = None
    try:
        projectCreate(project_path, db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        g.db = conn
        g.cur = conn.cursor()

        # Both blocks back the same exposed param, which is parameterizable.
        g.cur.execute(
            "SELECT b.block AS block, c.isParameterizable AS isParam "
            "FROM blocksparams bp "
            "JOIN blocks b ON b.blockKey = bp.blockKey "
            "JOIN constants c ON c.constantKey = bp.paramKey "
            "WHERE bp.param = 'SHARED_WIDTH'")
        consumers = {r['block']: r['isParam'] for r in g.cur.fetchall()}
        if set(consumers) != {'blockA', 'blockB'}:
            print(f"  FAIL: expected SHARED_WIDTH consumed by blockA and blockB, "
                  f"got {sorted(consumers)}")
            return False
        if not all(consumers.values()):
            print(f"  FAIL: backing constant not parameterizable: {consumers}")
            return False

        # Each consuming block carries the shared parameterizable type and
        # structure module-local, type before structure.
        expected = [('type', 'sharedDataT'), ('structure', 'sharedDataSt')]
        for block in ('blockA', 'blockB'):
            g.cur.execute("SELECT blockKey FROM blocks WHERE block = ?", (block,))
            block_key = g.cur.fetchone()['blockKey']
            g.cur.execute(
                "SELECT declKind, declKey, orderIndex FROM blockParameterizedDecls "
                "WHERE blockKey = ? ORDER BY orderIndex", (block_key,))
            rows = g.cur.fetchall()
            got = [(r['declKind'], r['declKey'].split('/', 1)[0]) for r in rows]
            if got != expected:
                print(f"  FAIL: {block} declaration set {got}, expected {expected}")
                return False
            if [r['orderIndex'] for r in rows] != [0, 1]:
                print(f"  FAIL: {block} orderIndex not contiguous from 0")
                return False

        print("  PASS: shared param consumed by two blocks; both carry "
              "sharedDataT then sharedDataSt")
        return True
    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False
    finally:
        if conn is not None:
            conn.close()
        os.chdir(original_cwd)
        _cleanup([project_path, arch_path, db_path])


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING: block-param / ipParameters-constant linkage + decl set")
    print("="*70)
    tests = [
        test_orphan_ipparameters_constant,
        test_unbacked_block_param,
        test_non_parameterizable_backing,
        test_variant_binding_exceeds_maxvalue,
        test_shared_param_two_blocks_and_decl_set,
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
