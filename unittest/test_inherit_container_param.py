#!/usr/bin/env python3
"""Contained-block config inheritance (`inheritContainerParam`).

A contained-block INSTANCE may declare `inheritContainerParam: true` in place of
a `variant:` selector. That instance is then typed with the CONTAINER block's
active Config template symbol (`Config`); C++ template instantiation resolves the
concrete struct at the container's own instantiation site (including the
transitive variant case). No config value is plumbed. The child block keeps its
own `params:` and still emits its own DefaultConfig for standalone use.

Positive: a container with params [WIDTH, DEPTH] contains a child with params
[WIDTH] (a by-name subset) using `inheritContainerParam: true`. db-create
succeeds; the projectOpen per-instance config selection carries the contracted
`inheritContainer` flag, and the template layer spells the child instance's
Config template argument as `<Config>` (the container's own symbol).

Negatives (each must fail db-create with a clear diagnostic):
  (a) child params are NOT a by-name subset of the container's;
  (b) `variant:` and `inheritContainerParam:` are set on one instance;
  (c) the container block is not parameterized (declares no params);
  (d) the child block declares no params;
  (f) a child parameter shares the container's name but is backed by a
      different `ipParameters` declaration.

A fifth negative covers the top-instance guard: `inheritContainerParam: true` on
the root top instance (whose container is `_topInstance`, not a block) must fail
db-create with a clean diagnostic, not a traceback.

`inheritContainerParam` forwards each parameter by name, so a by-name subset is
not enough: a child declaration of a shared name with a smaller `maxValue` would
be sized below what the container can bind. Negative (f) declares WIDTH twice, in
two files that do not include each other, so each block resolves its own WIDTH
and only the shared-declaration check rejects the design.

Validation (e) — container and child must be the same owning project — is
implemented in calcBlockConfigInfo::validate_inherit_container_params but is not
unit-fixtured here: it requires a multi-project composition
(provider-override/include closure), which is heavier than a single-file unit
fixture. It is exercised by the composed examples and the debayer product
acceptance.
"""

import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectCreate, projectOpen
from pysrc import intf_gen_utils


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


def _make_project(arch_yaml, name, extra_files=()):
    arch_path = _write_temp(arch_yaml, '.yaml', f'{name}_arch_')
    project_yaml = f"""projectName: {name}
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""
    project_path = _write_temp(project_yaml, '_project.yaml', f'{name}_project_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    return project_path, db_path, [arch_path] + list(extra_files)


def _run_create_subprocess(project_path, db_path):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', project_path, '--db', db_path],
        capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
    return result


# --- Positive fixture: subset child inherits the container's Config ---------
# The child also carries a type payload: a `types:` row sized by WIDTH
# (`pT`), bound to a `datatype: type` interface parameter on one of the
# child's own ports. `uSrc` gives that port a connection to satisfy
# declared-ports validation; it declares no ports: of its own, so its side
# of the connection is inferred rather than checked for compatibility, and
# the fixture stays focused on the child's own payload resolution.
POSITIVE_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "width param"}
    DEPTH: {value: 4, maxValue: 16, desc: "depth param"}

types:
  pT: {width: WIDTH, isParameterizable: true, desc: "type payload sized by the inherited WIDTH"}

interface_defs:
  type_intf:
    parameters:
      p_ty: {datatype: type}
    signals:
      valid: bool
      ready: bool
      sig_ty: p_ty
    modports:
      src:
        inputs: ['ready']
        outputs: ['valid', 'sig_ty']
      dst:
        inputs: ['valid', 'sig_ty']
        outputs: ['ready']
    sc_channel:
      type: 'type_intf'
      multicycle_types: []

interfaces:
  typeIf:
    interfaceType: type_intf
    desc: "type_intf binding its datatype: type payload to pT"
    structures:
      - {structure: pT, structureType: p_ty}

blocks:
  containerIp:
    desc: "Parameterized container block"
    params: [WIDTH, DEPTH]
  childIp:
    desc: "Parameterized child block (subset params)"
    params: [WIDTH]
    ports:
      inTy: {interface: typeIf, direction: dst}
  srcIp:
    desc: "Type payload source sibling (implied port)"
    params: [WIDTH]
  top:
    desc: "Top block"

instances:
  uTop:       { container: top, instanceType: top }
  uContainer: { container: top, instanceType: containerIp, variant: cv0 }
  uChild:     { container: containerIp, instanceType: childIp, inheritContainerParam: true }
  uSrc:       { container: containerIp, instanceType: srcIp, inheritContainerParam: true }

parameters:
  containerIp:
    cv0:
      WIDTH: 8
      DEPTH: 4

connections:
  - {interface: typeIf, src: uSrc, srcport: outTy, dst: uChild, dstport: inTy}
"""


def _run_positive():
    print("inheritContainerParam: subset child inherits container Config")
    original_cwd = os.getcwd()
    project_path, db_path, extra = _make_project(POSITIVE_YAML, 'inherit_pos')
    paths = [project_path, db_path] + extra
    try:
        # db-create must succeed with an inheriting instance.
        projectCreate(project_path, db_path)

        prj = projectOpen(db_path)
        container_key = [
            k for k, r in prj.data['blocks'].items()
            if isinstance(r, dict) and r.get('block') == 'containerIp'][0]
        view = prj.getBlockData(container_key)
        child_inst = next(
            inst for inst in view['subBlockInstances'].values()
            if inst['instance'] == 'uChild')
        sel = child_inst['instanceConfigSelection']

        # Contracted flag present and set for the inheriting instance.
        assert sel['inheritContainer'] is True, \
            f"expected inheritContainer True, got {sel.get('inheritContainer')!r}"
        # Template layer spells the container's own Config symbol.
        struct = intf_gen_utils.cpp_config_struct_name(sel)
        assert struct == 'Config', \
            f"expected Config struct name 'Config', got {struct!r}"
        arg = intf_gen_utils.cpp_config_arg(sel)
        assert arg == '<Config>', \
            f"expected template arg '<Config>', got {arg!r}"

        # The child's type payload (its `inTy` port, bound to `pT`) spells its
        # width as `Config::WIDTH`. At the container's instantiation site
        # `Config` is the bound cv0 struct, so the width is the container's
        # WIDTH, not one the child freezes on its own.
        typeif_row = next(r for r in prj.data['interfaces'].values()
                          if r['interface'] == 'typeIf')
        intf_def = prj.data['interface_defs'][typeif_row['interfaceTypeKey']]
        (payload,) = prj.getIntfParamBindings(intf_def, typeif_row['structures'])
        spelled = intf_gen_utils.sc_type_payload_name(payload, prj)
        assert spelled == 'pT<Config>, Config::WIDTH', \
            f"expected type payload 'pT<Config>, Config::WIDTH', got {spelled!r}"

        print("  PASS: inheriting instance types on the container's <Config>")
        print("  PASS: inherited type payload width scopes to Config::WIDTH")
        return True
    except Exception as e:  # noqa: BLE001 - surface as a test failure
        print(f"  FAIL: {e}")
        return False
    finally:
        os.chdir(original_cwd)
        _cleanup(paths)


# --- Negative (a): child params not a by-name subset of the container's -----
NEG_SUBSET_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "width param"}
    DEPTH: {value: 4, maxValue: 16, desc: "depth param"}
    EXTRA: {value: 2, maxValue: 8, desc: "child-only param not on container"}

blocks:
  containerIp:
    desc: "Parameterized container block"
    params: [WIDTH, DEPTH]
  childIp:
    desc: "Child with a param the container does not declare"
    params: [WIDTH, EXTRA]
  top:
    desc: "Top block"

instances:
  uTop:       { container: top, instanceType: top }
  uContainer: { container: top, instanceType: containerIp, variant: cv0 }
  uChild:     { container: containerIp, instanceType: childIp, inheritContainerParam: true }

parameters:
  containerIp:
    cv0:
      WIDTH: 8
      DEPTH: 4
"""


# --- Negative (b): variant and inheritContainerParam both set ---------------
NEG_MUTEX_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "width param"}
    DEPTH: {value: 4, maxValue: 16, desc: "depth param"}

blocks:
  containerIp:
    desc: "Parameterized container block"
    params: [WIDTH, DEPTH]
  childIp:
    desc: "Parameterized child block (subset params)"
    params: [WIDTH]
  top:
    desc: "Top block"

instances:
  uTop:       { container: top, instanceType: top }
  uContainer: { container: top, instanceType: containerIp, variant: cv0 }
  uChild:     { container: containerIp, instanceType: childIp, variant: dv0, inheritContainerParam: true }

parameters:
  containerIp:
    cv0:
      WIDTH: 8
      DEPTH: 4
  childIp:
    dv0:
      WIDTH: 8
"""


# --- Negative (c): container block is not parameterized ---------------------
NEG_CONTAINER_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "width param"}

blocks:
  containerIp:
    desc: "Non-parameterized container block"
  childIp:
    desc: "Parameterized child block"
    params: [WIDTH]
  top:
    desc: "Top block"

instances:
  uTop:       { container: top, instanceType: top }
  uContainer: { container: top, instanceType: containerIp }
  uChild:     { container: containerIp, instanceType: childIp, inheritContainerParam: true }
"""


# --- Negative (d): child block declares no params ---------------------------
NEG_CHILD_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "width param"}
    DEPTH: {value: 4, maxValue: 16, desc: "depth param"}

blocks:
  containerIp:
    desc: "Parameterized container block"
    params: [WIDTH, DEPTH]
  childIp:
    desc: "Child block with no params"
  top:
    desc: "Top block"

instances:
  uTop:       { container: top, instanceType: top }
  uContainer: { container: top, instanceType: containerIp, variant: cv0 }
  uChild:     { container: containerIp, instanceType: childIp, inheritContainerParam: true }

parameters:
  containerIp:
    cv0:
      WIDTH: 8
      DEPTH: 4
"""


# --- Negative (f): child parameter is a different declaration -------------
# Two WIDTH constants in two files that do not include each other; the top
# file includes both and wires the inheritContainerParam instance across them.
NEG_DIFFDECL_CONTAINER_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "container's own WIDTH declaration"}

blocks:
  containerIp:
    desc: "Parameterized container block"
    params: [WIDTH]
"""

NEG_DIFFDECL_CHILD_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 16, desc: "child's own WIDTH declaration, a different constant"}

blocks:
  childIp:
    desc: "Parameterized child block; WIDTH is its own declaration"
    params: [WIDTH]
"""


def _diffdecl_arch_yaml(container_basename, child_basename):
    return f"""include:
  - {container_basename}
  - {child_basename}

blocks:
  top:
    desc: "Top block"

instances:
  uTop:       {{ container: top, instanceType: top }}
  uContainer: {{ container: top, instanceType: containerIp, variant: cv0 }}
  uChild:     {{ container: containerIp, instanceType: childIp, inheritContainerParam: true }}

parameters:
  containerIp:
    cv0:
      WIDTH: 8
"""


# --- Negative (top instance): inheritContainerParam on the root top instance -
# The topInstance's container is `_topInstance` (not a block), so the guard must
# reject it cleanly rather than raising a KeyError on the block lookup.
NEG_TOPINSTANCE_YAML = """blocks:
  top:
    desc: "Top block"

instances:
  uTop: { container: top, instanceType: top, inheritContainerParam: true }
"""


# --- Positive fixture: inheriting child wired to a variant-bound sibling ----
# The interface-compatibility check resolves each junction side under that
# side's own variant bindings. An inheriting instance carries no variant, so it
# resolves at the constants' DECLARED DEFAULTS rather than at the container's
# binding, while its variant-bound sibling resolves at the bound value. Here the
# default is 8 and the container binds 32, so any adjudication of this junction
# reports a bogus 32-vs-8 payload mismatch on a design that is correct: both
# ends are 32 bits in emitted code, because the inheriting child is templated on
# the container's Config. Both wiring directions are covered because the
# connection-side binding is chosen from the endpoints (dst preferred), so the
# misresolution lands on the inheriting end in one direction and on the
# non-inheriting end in the other.
def _sibling_yaml(srcInstance, srcPort, dstInstance, dstPort,
                  producerDirection, consumerDirection):
    return f"""ipParameters:
  constants:
    WIDTH: {{value: 8, maxValue: 128, desc: "width param; declared default 8"}}
  types:
    dataT: {{width: WIDTH, maxBitwidth: 128, desc: "parameterizable data word"}}

types:
  markerT: {{width: 1, desc: "marker bit"}}

structures:
  dataSt:
    marker: {{varType: markerT, desc: "marker"}}
    data:   {{varType: dataT,   desc: "payload"}}

interfaces:
  dataIf:
    desc: "one shared data interface declaration"
    interfaceType: push_ack
    structures:
      - {{structure: dataSt, structureType: data_t}}

blocks:
  top:
    desc: "Top block"
  containerIp:
    desc: "Parameterized container block"
    params: [WIDTH]
  inheritIp:
    desc: "Child that inherits the container's Config"
    params: [WIDTH]
    ports:
      p: {{interface: dataIf, direction: {producerDirection}}}
  boundIp:
    desc: "Sibling bound to an explicit variant"
    params: [WIDTH]
    ports:
      p: {{interface: dataIf, direction: {consumerDirection}}}

instances:
  uTop:       {{ container: top, instanceType: top }}
  uContainer: {{ container: top, instanceType: containerIp, variant: cv0 }}
  uInherit:   {{ container: containerIp, instanceType: inheritIp, inheritContainerParam: true }}
  uBound:     {{ container: containerIp, instanceType: boundIp, variant: cv0 }}

parameters:
  containerIp:
    cv0:
      WIDTH: 32
  boundIp:
    cv0:
      WIDTH: 32
  inheritIp:
    cv0:
      WIDTH: 32

connections:
  - {{interface: dataIf, src: {srcInstance}, srcport: {srcPort}, dst: {dstInstance}, dstport: {dstPort}}}
"""


def _run_inherit_sibling_accepted(label, arch_yaml, name):
    print(f"inheritContainerParam: {label}")
    project_path, db_path, extra = _make_project(arch_yaml, name)
    paths = [project_path, db_path] + extra
    try:
        result = _run_create_subprocess(project_path, db_path)
        combined = result.stdout + result.stderr
        if 'Traceback (most recent call last)' in combined:
            print("  FAIL: got Python stack trace")
            print(combined)
            return False
        if result.returncode != 0:
            print("  FAIL: a correct inheritContainerParam design was rejected; "
                  "the junction was adjudicated at the child's declared "
                  "defaults instead of the container's binding")
            print(combined)
            return False
        print("  PASS: accepted")
        return True
    finally:
        _cleanup(paths)


def _run_negative(label, arch_yaml, name, needle, extra_files=()):
    print(f"inheritContainerParam negative: {label}")
    project_path, db_path, extra = _make_project(arch_yaml, name, extra_files)
    paths = [project_path, db_path] + extra
    try:
        result = _run_create_subprocess(project_path, db_path)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            print("  FAIL: expected db-create failure but it succeeded")
            return False
        if 'Traceback (most recent call last)' in combined:
            print("  FAIL: got Python stack trace instead of clean error")
            print(combined)
            return False
        if needle not in combined:
            print(f"  FAIL: diagnostic missing expected text: {needle!r}")
            print(combined)
            return False
        print("  PASS: rejected with the expected diagnostic")
        return True
    finally:
        _cleanup(paths)


def run_all_tests():
    ok = True
    ok = _run_positive() and ok
    ok = _run_inherit_sibling_accepted(
        "inheriting producer into a variant-bound sibling is accepted",
        _sibling_yaml('uInherit', 'p', 'uBound', 'p', 'src', 'dst'),
        'inherit_sibling_fwd') and ok
    ok = _run_inherit_sibling_accepted(
        "variant-bound producer into an inheriting sibling is accepted",
        _sibling_yaml('uBound', 'p', 'uInherit', 'p', 'dst', 'src'),
        'inherit_sibling_rev') and ok
    ok = _run_negative(
        "child params not a subset of the container's",
        NEG_SUBSET_YAML, 'inherit_neg_subset',
        "are not a by-name subset of container block") and ok
    ok = _run_negative(
        "variant and inheritContainerParam are mutually exclusive",
        NEG_MUTEX_YAML, 'inherit_neg_mutex',
        "variant and inheritContainerParam are mutually exclusive") and ok
    ok = _run_negative(
        "container block is not parameterized",
        NEG_CONTAINER_YAML, 'inherit_neg_container',
        "to be parameterized (declare params)") and ok
    ok = _run_negative(
        "child block declares no params",
        NEG_CHILD_YAML, 'inherit_neg_child',
        "to declare params") and ok
    ok = _run_negative(
        "inheritContainerParam on the top instance (no container block)",
        NEG_TOPINSTANCE_YAML, 'inherit_neg_topinstance',
        "requires the instance to be contained in a block") and ok
    diffdecl_container_path = _write_temp(
        NEG_DIFFDECL_CONTAINER_YAML, '.yaml', 'inherit_neg_diffdecl_container_')
    diffdecl_child_path = _write_temp(
        NEG_DIFFDECL_CHILD_YAML, '.yaml', 'inherit_neg_diffdecl_child_')
    ok = _run_negative(
        "child's WIDTH is a different declaration than the container's WIDTH",
        _diffdecl_arch_yaml(os.path.basename(diffdecl_container_path),
                            os.path.basename(diffdecl_child_path)),
        'inherit_neg_diffdecl', "backs it with a different constant",
        extra_files=[diffdecl_container_path, diffdecl_child_path]) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
