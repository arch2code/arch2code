#!/usr/bin/env python3
"""Block-param / ipParameters-constant linkage: a param resolves to exactly one
parameterizable backing constant, respects its maxValue, and is satisfiable at
both ends of a parameterized connection. A declared parameter needs no
consumer, and a non-parameterized interface or cross-variant boundary channel
must not trip the validator. Also pins module-local vs context-shared
declaration selection when two blocks share one exposed param."""

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
yamlFormat: 2
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


def _expect_success(arch_content, test_name):
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
        if result.returncode != 0:
            print("  FAIL: expected success but build failed")
            print('  ' + '\n  '.join((result.stderr + result.stdout).split('\n')[:25]))
            return False
        print("  PASS: build succeeded")
        return True
    finally:
        _cleanup([project_path, arch_path, db_path])


def test_unconsumed_ipparameters_constant_allowed():
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
    return _expect_success(arch, "unconsumed ipParameters constant is allowed")


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
    # Finding the backing constant is the paramSource foreign key's job, so an
    # unbacked param is rejected by the generic FK miss diagnostic rather than by
    # _post_validateBlockParamBacking, which now only judges the resolved row.
    return _expect_error(
        arch,
        ["NO_BACKING", "section params", "no constants row named"],
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
    big:
      W: 64
"""
    return _expect_error(
        arch,
        ["big", "exceeding the backing", "maxValue"],
        "variant binding exceeds backing maxValue")


# ----------------------------------------------------------------------------
# Parameterized-interface connection-endpoint validation. A parameterized
# interface implies both connected endpoints carry the backing param its
# payload depends on; an endpoint block that does not is an error.
# ----------------------------------------------------------------------------

# Shared building blocks: a parameterizable payload (dataSt -> dataT -> WIDTH)
# exposed through a push_ack interface, with a producer block that backs WIDTH
# (so it is not an orphan). The consumer side varies per test.
_C36_COMMON = """ipParameters:
  constants:
    WIDTH: { value: 8, maxValue: 16, desc: "backing width" }
  types:
    dataT: { width: WIDTH, maxBitwidth: 16, desc: "parameterizable payload word" }

structures:
  dataSt:
    data: { varType: dataT, desc: "parameterizable payload" }

interfaces:
  dataIf:
    desc: "parameterized push/ack stream"
    interfaceType: push_ack
    structures:
      - { structure: dataSt, structureType: data_t }

blocks:
  producer:
    desc: "parameterized producer that backs WIDTH"
    params: [WIDTH]
    ports:
      out: { interface: dataIf, direction: src }
"""


def test_param_interface_endpoint_missing_param():
    # consumer carries a port on the parameterized dataIf but declares no
    # params: at all. A parameterizable structure on a block's own surface makes
    # the block's shape parameter-dependent, so it must be declared as a
    # template (params:) block. The own-surface check fires first here, before
    # the per-interface endpoint diagnostic (which is covered by
    # test_param_interface_endpoint_wrong_param, where the block does declare
    # params: but not the one the interface needs).
    arch = _C36_COMMON + """  consumer:
    desc: "endpoint on a parameterized interface without the backing param"
    ports:
      in: { interface: dataIf, direction: dst }
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uProd: { container: top, instanceType: producer, variant: v0 }
  uCons: { container: top, instanceType: consumer }

connections:
  - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in }

parameters:
  producer:
    v0:
      WIDTH: 8
"""
    return _expect_error(
        arch,
        ["consumer", "own surface", "declares no params"],
        "parameterized interface endpoint declares no params (own-surface)")


def test_param_interface_both_endpoints_parameterized():
    # Both endpoints carry WIDTH: the payload is sized in each module's own
    # scope, so the connection is legal and projectCreate succeeds.
    arch = _C36_COMMON + """  consumer:
    desc: "endpoint that carries the backing param"
    params: [WIDTH]
    ports:
      in: { interface: dataIf, direction: dst }
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uProd: { container: top, instanceType: producer, variant: v0 }
  uCons: { container: top, instanceType: consumer, variant: v0 }

connections:
  - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in }

parameters:
  producer:
    v0:
      WIDTH: 8
  consumer:
    v0:
      WIDTH: 8
"""
    return _expect_success(
        arch,
        "parameterized interface with both endpoints parameterized")


def test_param_interface_endpoint_wrong_param():
    # The consumer is parameterized, but with an unrelated backing param
    # (OTHER_W), not the WIDTH the payload depends on. It is parameterizable yet
    # still cannot size the payload, so the error reports a missing required
    # parameter rather than an unparameterized block - the second reason branch.
    arch = """ipParameters:
  constants:
    WIDTH: { value: 8, maxValue: 16, desc: "backing width the payload needs" }
    OTHER_W: { value: 8, maxValue: 16, desc: "unrelated backing param" }
  types:
    dataT: { width: WIDTH, maxBitwidth: 16, desc: "parameterizable payload word" }

structures:
  dataSt:
    data: { varType: dataT, desc: "parameterizable payload" }

interfaces:
  dataIf:
    desc: "parameterized push/ack stream"
    interfaceType: push_ack
    structures:
      - { structure: dataSt, structureType: data_t }

blocks:
  producer:
    desc: "parameterized producer that backs WIDTH"
    params: [WIDTH]
    ports:
      out: { interface: dataIf, direction: src }
  consumer:
    desc: "parameterized, but carries the wrong backing param"
    params: [OTHER_W]
    ports:
      in: { interface: dataIf, direction: dst }
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uProd: { container: top, instanceType: producer, variant: v0 }
  uCons: { container: top, instanceType: consumer, variant: v0 }

connections:
  - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in }

parameters:
  producer:
    v0:
      WIDTH: 8
  consumer:
    v0:
      OTHER_W: 8
"""
    return _expect_error(
        arch,
        ["dataIf", "uCons", "does not declare the required parameter", "missing WIDTH"],
        "parameterized interface endpoint parameterized with the wrong param")


def test_param_interface_src_endpoint_missing_param():
    # The shortfall is on the src (producer) end this time: the producer has a
    # parameterizable port on its own surface but declares no params: at all,
    # so the own-surface check rejects it. This shows the check applies to the
    # src endpoint too, not only the consumer. The consumer carries WIDTH.
    arch = """ipParameters:
  constants:
    WIDTH: { value: 8, maxValue: 16, desc: "backing width" }
  types:
    dataT: { width: WIDTH, maxBitwidth: 16, desc: "parameterizable payload word" }

structures:
  dataSt:
    data: { varType: dataT, desc: "parameterizable payload" }

interfaces:
  dataIf:
    desc: "parameterized push/ack stream"
    interfaceType: push_ack
    structures:
      - { structure: dataSt, structureType: data_t }

blocks:
  producer:
    desc: "src endpoint lacking the backing param"
    ports:
      out: { interface: dataIf, direction: src }
  consumer:
    desc: "consumer that carries the backing param"
    params: [WIDTH]
    ports:
      in: { interface: dataIf, direction: dst }
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uProd: { container: top, instanceType: producer }
  uCons: { container: top, instanceType: consumer, variant: v0 }

connections:
  - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in }

parameters:
  consumer:
    v0:
      WIDTH: 8
"""
    return _expect_error(
        arch,
        ["producer", "own surface", "declares no params"],
        "parameterized interface src endpoint declares no params (own-surface)")


def test_nonparam_interface_endpoints_ok():
    # Baseline: a non-parameterized interface (plain payload, fixed width)
    # between two non-parameterized blocks. The connection is not
    # parameterizable, so endpoint validation does not fire and the build
    # succeeds. Guards against the validator over-firing on plain interfaces.
    arch = """types:
  ctrlT: { width: 4, desc: "plain payload word" }

structures:
  ctrlSt:
    flag: { varType: ctrlT, desc: "plain payload" }

interfaces:
  ctrlIf:
    desc: "non-parameterized push/ack stream"
    interfaceType: push_ack
    structures:
      - { structure: ctrlSt, structureType: data_t }

blocks:
  producer:
    desc: "plain producer"
    ports:
      out: { interface: ctrlIf, direction: src }
  consumer:
    desc: "plain consumer"
    ports:
      in: { interface: ctrlIf, direction: dst }
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uProd: { container: top, instanceType: producer }
  uCons: { container: top, instanceType: consumer }

connections:
  - { interface: ctrlIf, src: uProd, srcport: out, dst: uCons, dstport: in }
"""
    return _expect_success(
        arch,
        "non-parameterized interface between non-parameterized endpoints")


def test_crossvariant_nonparam_boundary_channel():
    # The C3.5 cross-variant boundary path: two parameterized blocks bound to
    # different variants (WIDTH 8 vs 16) connected through a non-parameterized
    # boundary interface. Because the channel interface is not parameterizable,
    # endpoint validation correctly skips it and the build succeeds - the
    # per-leg payload adaptation is a runtime concern, not a static error.
    arch = """ipParameters:
  constants:
    WIDTH: { value: 8, maxValue: 32, desc: "per-variant backing width" }

types:
  boundaryT: { width: 16, desc: "fixed-width boundary word" }

structures:
  boundarySt:
    flag: { varType: boundaryT, desc: "fixed-width boundary payload" }

interfaces:
  boundaryIf:
    desc: "non-parameterized boundary push/ack stream"
    interfaceType: push_ack
    structures:
      - { structure: boundarySt, structureType: data_t }

blocks:
  producer:
    desc: "parameterized producer (variant v0)"
    params: [WIDTH]
    ports:
      out: { interface: boundaryIf, direction: src }
  consumer:
    desc: "parameterized consumer (variant v1)"
    params: [WIDTH]
    ports:
      in: { interface: boundaryIf, direction: dst }
  top: { desc: "top" }

instances:
  uTop: { container: top, instanceType: top }
  uProd: { container: top, instanceType: producer, variant: v0 }
  uCons: { container: top, instanceType: consumer, variant: v1 }

connections:
  - { interface: boundaryIf, src: uProd, srcport: out, dst: uCons, dstport: in }

parameters:
  producer:
    v0:
      WIDTH: 8
  consumer:
    v1:
      WIDTH: 16
"""
    return _expect_success(
        arch,
        "cross-variant blocks bridged by a non-parameterized boundary channel")


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
    v0:
      SHARED_WIDTH: 12
  blockB:
    v0:
      SHARED_WIDTH: 16
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
            "JOIN constants c ON c.constantKey = bp.paramSourceKey "
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
        test_unconsumed_ipparameters_constant_allowed,
        test_unbacked_block_param,
        test_non_parameterizable_backing,
        test_variant_binding_exceeds_maxvalue,
        test_param_interface_endpoint_missing_param,
        test_param_interface_endpoint_wrong_param,
        test_param_interface_src_endpoint_missing_param,
        test_param_interface_both_endpoints_parameterized,
        test_nonparam_interface_endpoints_ok,
        test_crossvariant_nonparam_boundary_channel,
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
