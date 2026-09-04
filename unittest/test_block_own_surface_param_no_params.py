#!/usr/bin/env python3
"""Lock the own-surface-parameterizable-without-own-params validator.

`calcBlockConfigInfo()` walks every structure reachable from a block and
distinguishes two ways a block can become `isParameterizable`:

- An OWN-surface parameterizable structure: the block's own register,
  memory, or own-port interface references a parameterizable type. The
  block must be a `template<typename Config>` (it must declare its own
  `params:`) so it has a `Config` to instantiate the type with. Without
  own `params:` there is no valid C++ realization, so the validator calls
  `printError(...)` whose message begins
  "... has a parameterizable structure on its own surface ...".

- A TRANSIT/CONTAINER parameterizable structure: the block merely
  *contains* children that are wired together by a parameterizable
  connection (walk step 2, `own_surface=False`). Each child owns the
  parameterizable surface and declares its own `params:`; the container is
  resolved at a frozen variant. This is valid and must NOT error, even
  though the container block is still flagged `isParameterizable`.

These tests build minimal fixtures for both arms:

- NEGATIVE (register): a register on a no-`params:` block whose payload
  structure references a parameterizable type -> error (walk step 4/5).
- NEGATIVE (own port): a block with a parameterizable port but no
  `params:` -> error (walk step 1).
- POSITIVE control (transit): a container with no `params:` holding a
  parameterizable connection between two contained children that DO
  declare `params:` -> build succeeds (walk step 2).

The stable assertion substring is "parameterizable structure on its own
surface", which is the leading clause of the validator message.
"""

import sys
import os
import tempfile
import subprocess

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen


OWN_SURFACE_SUBSTRING = "parameterizable structure on its own surface"


def _create_project(arch_content):
    """Write a minimal temp project.yaml + single arch YAML. The project
    declares no address-policy sections, so a register on a block does not
    enter the address-calculation path; this keeps the fixture focused on
    the calcBlockConfigInfo own-surface validation."""
    arch_fd, arch_path = tempfile.mkstemp(
        suffix='.yaml', prefix='arch_own_surface_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(arch_content)

    project_content = (
        "projectName: own_surface_param_test\n"
        "yamlFormat: 2\n"
        "topInstance: uTop\n"
        "\n"
        "dirs:\n"
        "  root: ..\n"
        "\n"
        "projectFiles:\n"
        f"  - {os.path.basename(arch_path)}\n"
    )
    proj_fd, project_path = tempfile.mkstemp(
        suffix='_project.yaml', prefix='proj_own_surface_', dir=test_dir)
    os.close(proj_fd)
    with open(project_path, 'w') as f:
        f.write(project_content)
    return project_path, arch_path


def _run_arch2code(project_path, db_path):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', project_path, '--db', db_path],
        capture_output=True, text=True, cwd=test_dir, env=env, timeout=60)


def _cleanup(paths):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.unlink(p)
            except OSError:
                pass


def _find_block(prj, simple_name):
    for _key, row in prj.data['blocks'].items():
        if isinstance(row, dict) and row.get('block') == simple_name:
            return row
    raise AssertionError(f"No block named '{simple_name}' found")


# A parameterizable type declared standalone (isParameterizable + maxBitwidth)
# backed by a parameterizable constant (isParameterizable + maxValue). No
# ipParameters block is required to make a type parameterizable; this is the
# leanest way to place a parameterizable structure on a block surface.
PARAM_TYPE_PREAMBLE = """constants:
    WIDTH:
        value: 8
        isParameterizable: true
        maxValue: 16
        desc: "Parameterizable width"

types:
    pdataT:
        width: WIDTH
        maxBitwidth: 16
        desc: "Parameterizable data type"

variables:
    pdata: { type: pdataT, desc: "Parameterizable payload variable" }
"""


# --------------------------------------------------------------------------
# NEGATIVE: parameterizable structure on a block's OWN register, block has
# no params: (walk step 4).
# --------------------------------------------------------------------------
OWN_REGISTER_ARCH = (
    PARAM_TYPE_PREAMBLE
    + """
structures:
    pRegSt:
        pdata: { generator: register }

blocks:
    top:  { desc: "Top container" }
    leaf: { desc: "Leaf owning a parameterizable register but declaring NO params:" }

instances:
    uTop:  { container: top, instanceType: top }
    uLeaf: { container: top, instanceType: leaf }

registers:
    - register: cfg
      regType: rw
      block: leaf
      structure: pRegSt
      desc: "Register whose payload structure references a parameterizable type"
"""
)


# --------------------------------------------------------------------------
# NEGATIVE: parameterizable own-port interface on a block with no params:
# (walk step 1). The peer block legitimately declares params:.
# --------------------------------------------------------------------------
OWN_PORT_ARCH = (
    PARAM_TYPE_PREAMBLE
    + """
structures:
    paramBusSt:
        pdata: { desc: "Payload" }

interfaces:
    paramBus:
        desc: "Parameterized point-to-point bus"
        interfaceType: rdy_vld
        structures:
            - { structure: paramBusSt, structureType: data_t }

blocks:
    top: { desc: "Top container", hasMdl: true }
    srcBlock:
        desc: "Source block with a parameterizable port but NO params:"
        hasMdl: true
        ports:
            out: { interface: paramBus, direction: src }
    dstBlock:
        desc: "Destination block (legitimately parameterizable)"
        hasMdl: true
        params: [WIDTH]
        ports:
            in: { interface: paramBus, direction: dst }

instances:
    uTop: { container: top, instanceType: top }
    uSrc: { container: top, instanceType: srcBlock }
    uDst: { container: top, instanceType: dstBlock, variant: w0 }

parameters:
    dstBlock:
        w0:
            WIDTH: 8

connections:
    - { interface: paramBus, src: uSrc, srcport: out, dst: uDst, dstport: in }
"""
)


# --------------------------------------------------------------------------
# POSITIVE control: the parameterizable surface is owned by the CONTAINED
# children (both declare params:); the container `top` declares no params:
# and reaches the parameterizable interface only through the contained
# connection (walk step 2, own_surface=False). Must NOT error; `top` is
# still flagged isParameterizable.
# --------------------------------------------------------------------------
TRANSIT_ARCH = (
    PARAM_TYPE_PREAMBLE
    + """
structures:
    paramBusSt:
        pdata: { desc: "Payload" }

interfaces:
    paramBus:
        desc: "Parameterized point-to-point bus"
        interfaceType: rdy_vld
        structures:
            - { structure: paramBusSt, structureType: data_t }

blocks:
    top: { desc: "Top container, no params: of its own", hasMdl: true }
    srcBlock:
        desc: "Source block (owns the parameterizable port, declares params:)"
        hasMdl: true
        params: [WIDTH]
        ports:
            out: { interface: paramBus, direction: src }
    dstBlock:
        desc: "Destination block (owns the parameterizable port, declares params:)"
        hasMdl: true
        params: [WIDTH]
        ports:
            in: { interface: paramBus, direction: dst }

instances:
    uTop: { container: top, instanceType: top }
    uSrc: { container: top, instanceType: srcBlock, variant: w0 }
    uDst: { container: top, instanceType: dstBlock, variant: w0 }

parameters:
    srcBlock:
        w0:
            WIDTH: 8
    dstBlock:
        w0:
            WIDTH: 8

connections:
    - { interface: paramBus, src: uSrc, srcport: out, dst: uDst, dstport: in }
"""
)


def _assert_own_surface_error(arch_yaml, test_name):
    """Build a fixture expected to FAIL with the own-surface validator
    message; verify a clean (non-traceback) error carrying the substring."""
    print(f"\n{'=' * 70}\nTest: {test_name}\n{'=' * 70}")
    project_path, arch_path = _create_project(arch_yaml)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    paths = [project_path, arch_path, db_path]
    try:
        result = _run_arch2code(project_path, db_path)
        if result.returncode == 0:
            print("  FAIL: expected the build to fail, but it succeeded")
            return False
        output = result.stdout + result.stderr
        if 'Traceback (most recent call last)' in output:
            print("  FAIL: got a Python traceback instead of a clean error")
            print('  ' + '\n  '.join(output.splitlines()[-15:]))
            return False
        if OWN_SURFACE_SUBSTRING not in output:
            print(f"  FAIL: expected substring not found: "
                  f"'{OWN_SURFACE_SUBSTRING}'")
            print('  ' + '\n  '.join(output.splitlines()[:25]))
            return False
        msg = next((ln for ln in output.splitlines()
                    if OWN_SURFACE_SUBSTRING in ln), '')
        print("  PASS: own-surface validator error raised")
        print(f"     {msg.strip()[:120]}")
        return True
    finally:
        _cleanup(paths)


def test_own_register_no_params():
    """Register payload structure is parameterizable, owning block has no
    params: -> own-surface error (walk step 4)."""
    return _assert_own_surface_error(
        OWN_REGISTER_ARCH, "own parameterizable register, no params:")


def test_own_port_no_params():
    """Own-port parameterizable interface, owning block has no params: ->
    own-surface error (walk step 1)."""
    return _assert_own_surface_error(
        OWN_PORT_ARCH, "own parameterizable port, no params:")


def test_transit_container_no_params_ok():
    """Positive control: parameterizable interface reached only through a
    contained child connection; container has no params: -> no error, and
    the container is still flagged isParameterizable (walk step 2)."""
    print(f"\n{'=' * 70}\nTest: transit/container, no params: (positive "
          f"control)\n{'=' * 70}")
    project_path, arch_path = _create_project(TRANSIT_ARCH)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    paths = [project_path, arch_path, db_path]
    try:
        result = _run_arch2code(project_path, db_path)
        if result.returncode != 0:
            print("  FAIL: transit/container build errored unexpectedly")
            print('  ' + '\n  '.join(
                (result.stdout + result.stderr).splitlines()[-20:]))
            return False
        prj = projectOpen(db_path)
        top = _find_block(prj, 'top')
        if not bool(top['isParameterizable']):
            print("  FAIL: container 'top' should be flagged isParameterizable "
                  "via the contained parameterizable connection")
            return False
        print("  PASS: transit/container build succeeded; 'top' flagged "
              "isParameterizable without erroring")
        return True
    finally:
        _cleanup(paths)


def run_all_tests():
    tests = [
        test_own_register_no_params,
        test_own_port_no_params,
        test_transit_container_no_params_ok,
    ]
    results = []
    for fn in tests:
        try:
            results.append((fn.__name__, fn()))
        except Exception as e:
            print(f"\n  EXCEPTION in {fn.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((fn.__name__, False))

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
