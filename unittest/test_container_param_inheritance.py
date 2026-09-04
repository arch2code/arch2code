#!/usr/bin/env python3
"""`containerParam:` - a child variant sourcing a parameter from its container.

A child's variant writes `PARAM: { containerParam: OTHER }` and takes that
parameter from the block the instance sits in. The value is not known where the
variant is declared, so the C++ Config becomes a template over the container's
Config and the SystemVerilog instantiation forwards the container's symbol.

This is a DIFFERENT mechanism from `test_container_param_channel_binding.py`,
which covers a container's own parameter typing a channel between two of its
children. Nothing there declares `containerParam:`.

Three functionality-executing cells, no database read-back:

1. The domain relation is REJECTED when it cannot hold. The container parameter
   and the child parameter may be backed by different constants, but the
   container's `maxValue` must not exceed the child's, or the container can be
   bound to a value the child cannot accept. The diagnostic must name the
   instance, both backing constants and both bounds.
2. Differently-backed parameters of equal domain are ACCEPTED, and the value
   resolves. The real Config emission path renders the two structs, and the
   rendered text is COMPILED AND RUN: the child parameter must resolve, through
   the container's Config, to the value the container binds.
3. The emitted SystemVerilog forwards the container's parameter symbol at the
   child instantiation.

Two properties stop a cell passing by coincidence, and they cover different
cells:

- The container binds 5, which is neither the child constant's default (1) nor
  the container constant's default (2). Only cell 2 pins a number, so this is
  what makes a fallback to either default fail there. Cell 3 asserts a symbol
  and would pass at any bound value.
- The two constants are named differently, so a resolver matching on spelling
  rather than on the authored `containerParam:` link fails cells 2 and 3 alike.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from types import SimpleNamespace

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import cleanup, write_temp
from pysrc.processYaml import projectOpen
from pysrc.systemcGen import genSystemC
from pysrc.systemVerilogGenerator import systemVerilogGenerator
from templates.systemc import config
from templates.systemVerilog import moduleInterfacesInstances

CXX = 'clang++'
CLOG2_DIR = os.path.join(base_dir, 'common', 'systemc')

# What the container binds, and the two declared defaults it must not be
# confused with.
BOUND_ALGO = 5
CHILD_DEFAULT = 1
CONTAINER_DEFAULT = 2
# The child's acceptance bound. The container's is the varying input: equal is
# accepted, wider is rejected.
CHILD_MAX = 7
WIDER_MAX = 15

# `cont` declares CONT_ALGO and contains `uLeaf`, whose variant sources the
# child's own LEAF_ALGO from it.
#
# `dummyT` is load-bearing despite being referenced by nothing: a context is
# include-valid only if it declares a plain types/structures/constants section,
# and only an include-valid context owns a SystemVerilog package. Without it the
# project has no package for cell 3's render to import.
ARCH_TEMPLATE = """ipParameters:
    constants:
        LEAF_ALGO: {{ value: {child_default}, maxValue: {child_max}, desc: "Leaf algorithm select" }}
        CONT_ALGO: {{ value: {container_default}, maxValue: {container_max}, desc: "Algorithm the container asks its leaves for" }}

types:
    dummyT: {{ width: 8, desc: "Makes this context include-valid; see module docstring" }}

blocks:
    top:
        desc: "Top block"
        hasMdl: true
    cont:
        desc: "Container declaring the knob it passes down"
        params: [CONT_ALGO]
        hasMdl: true
        hasRtl: true
    leaf:
        desc: "Leaf sourcing its algorithm from its container"
        params: [LEAF_ALGO]
        hasMdl: true
        hasRtl: true

instances:
    uTop:  {{ container: top,  instanceType: top }}
    uCont: {{ container: top,  instanceType: cont, variant: use }}
    uLeaf: {{ container: cont, instanceType: leaf, variant: fromCont }}

parameters:
    cont:
        use:
            CONT_ALGO: {bound}
    leaf:
        fromCont:
            LEAF_ALGO: {{ containerParam: CONT_ALGO }}
"""


def _build_database(container_max, project_name):
    """Run `arch2code.py` over a temp project. Returns (db_path, paths, result).

    The build runs in a subprocess because validation populates process-global
    state, so a second in-process build would trip the first build's globals.

    `_addrctl_helpers.build_database` is not used: it emits address-policy
    sections this fixture has no registers to need, and its 30-second subprocess
    timeout is tight for a suite that also compiles C++ under the parallel
    runner's full fan-out.
    """
    arch_path = write_temp(
        ARCH_TEMPLATE.format(child_default=CHILD_DEFAULT, child_max=CHILD_MAX,
                             container_default=CONTAINER_DEFAULT,
                             container_max=container_max, bound=BOUND_ALGO),
        '.yaml', 'contparam_arch_')
    project_path = write_temp(
        f"""projectName: {project_name}
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
""", '_project.yaml', 'contparam_project_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    paths = [project_path, arch_path, db_path]
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '--yaml', project_path, '--db', db_path],
            capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
    except Exception:
        cleanup(paths)
        raise
    return db_path, paths, result


def test_wider_container_domain_is_rejected():
    """The container's backing constant accepts values the child's does not."""
    print(f"\n{'='*70}\nTest: container maxValue wider than the child's is rejected"
          f"\n{'='*70}")
    _db_path, paths, result = _build_database(WIDER_MAX, 'contparam_reject_test')
    try:
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            print("FAIL: build succeeded; a container whose domain exceeds the "
                  f"child's must be rejected\n{combined}")
            return False
        # Both sides and both bounds: a message naming only one of them does not
        # tell the author which declaration to change.
        for needle in ("instance uLeaf", "child block 'leaf'", "param 'LEAF_ALGO'",
                       "container block 'cont'", "parameter 'CONT_ALGO'",
                       f"allows values up to {WIDER_MAX}",
                       f"allows only {CHILD_MAX}"):
            if needle not in combined:
                print(f"FAIL: diagnostic missing '{needle}'\n{combined}")
                return False
        print("PASS: rejected, naming the instance, both constants and both bounds")
        return True
    finally:
        cleanup(paths)


def _struct_body(rendered, structName):
    """Text between a struct's opening line and its closing brace, or ''.

    Walks the rendered text structurally rather than re-parsing C++, matching
    `test_eval_cpp_emit.py`. The marker also matches a class template, whose
    `template<...>` line sits above the `struct` line.
    """
    marker = f'struct {structName} {{'
    if marker not in rendered:
        return ''
    return rendered.split(marker, 1)[1].split('};', 1)[0]


def _render_config(prj):
    """Render the real per-variant Config emission for the fixture's context."""
    ctx = prj.data['blocks'][prj.getQualBlock('leaf')]['_context']
    data = prj.getContextData([ctx], genSystemC.dataTypeMappings)
    return config.includeConfig(None, prj, data)


def _compile_and_run(rendered, work_dir):
    """Compile the rendered structs and run them.

    The child Config is a template, so applying it to the container's Config is
    what performs the resolution; the compiler does it and `main` reports it.
    Returns a failure description, or the empty string when the value resolved.
    """
    source = os.path.join(work_dir, 'container_param_resolution.cpp')
    with open(source, 'w') as f:
        f.write(rendered)
        f.write(f"""
using resolved = leafFromContConfig<contUseConfig>;
static_assert(resolved::LEAF_ALGO == {BOUND_ALGO},
              "child parameter must resolve to the value its container binds");
int main() {{ return resolved::LEAF_ALGO == {BOUND_ALGO} ? 0 : 1; }}
""")
    binary = os.path.join(work_dir, 'container_param_resolution')
    compiled = subprocess.run(
        [CXX, '-std=c++23', '-Wall', '-Wextra', '-Werror',
         '-I' + CLOG2_DIR, source, '-o', binary],
        capture_output=True, text=True)
    if compiled.returncode != 0:
        return f"rendered Config did not compile:\n{compiled.stderr}"
    # Run it as well as compiling it: a static_assert alone would be satisfied
    # by a translation unit that never linked into a program.
    ran = subprocess.run([binary], capture_output=True, text=True, timeout=60)
    if ran.returncode != 0:
        return (f"child parameter did not resolve to {BOUND_ALGO} "
                f"(exit {ran.returncode})")
    return ''


def test_equal_domain_accepted_and_value_resolves(prj):
    """Equal bounds on different constants, and the emitted C++ resolving."""
    print(f"\n{'='*70}\nTest: differently-backed equal domains accepted; the "
          f"emitted Config resolves\n{'='*70}")
    rendered = _render_config(prj)
    # The child's variant sources every parameter it names, so its Config is a
    # class template; the container's variant binds a value, so its Config is a
    # plain struct carrying the bound number. Every member assertion is scoped to
    # the struct that must carry it: B5 emits the whole context's parameterizable
    # constants into every Config, so an unscoped search would find the right
    # spelling in the wrong struct.
    childBody = _struct_body(rendered, 'leafFromContConfig')
    containerBody = _struct_body(rendered, 'contUseConfig')
    checks = [
        (rendered, 'template<typename ContainerConfig>',
         "child Config is not a template over the container's Config"),
        (childBody, 'LEAF_ALGO = ContainerConfig::CONT_ALGO;',
         "child's inherited member does not read the container's parameter"),
        (containerBody, f'CONT_ALGO = {BOUND_ALGO};',
         "container's Config does not carry the bound value"),
    ]
    for haystack, needle, why in checks:
        if needle not in haystack:
            print(f"FAIL: {why}; missing '{needle}'\n{rendered}")
            return False
    # The declared default must not have been frozen into the inherited member.
    if f'LEAF_ALGO = {CHILD_DEFAULT};' in childBody:
        print(f"FAIL: inherited member frozen to the child's declared default"
              f"\n{rendered}")
        return False

    with tempfile.TemporaryDirectory(prefix='contparam_build_') as work_dir:
        failure = _compile_and_run(rendered, work_dir)
        if failure:
            print(f"FAIL: {failure}")
            return False
    print(f"PASS: accepted, and the child resolves to {BOUND_ALGO} through the "
          f"container's Config")
    return True


def test_systemverilog_forwards_container_symbol(prj):
    """The instantiation forwards the container's symbol, not a literal."""
    print(f"\n{'='*70}\nTest: SystemVerilog forwards the container's parameter "
          f"symbol\n{'='*70}")
    containerKey = prj.getQualBlock('cont')
    ctx = prj.data['blocks'][containerKey]['_context']
    data = prj.getBlockData(containerKey, trimRegLeafInstance=False)
    data.update(prj.getContextData([ctx], systemVerilogGenerator.dataTypeMappings))
    data['importPackages'] = None
    rendered = moduleInterfacesInstances.render(
        SimpleNamespace(fileMapKey=None), prj, data)

    if '#(.LEAF_ALGO(CONT_ALGO))' not in rendered:
        print(f"FAIL: instantiation does not forward the container's symbol"
              f"\n{rendered}")
        return False
    # The container's own parameter list is what it declares, and no more: the
    # child's parameter reaches it through the forwarded symbol.
    if 'parameter LEAF_ALGO' in rendered:
        print(f"FAIL: container declares the child's parameter\n{rendered}")
        return False
    print("PASS: forwarded as .LEAF_ALGO(CONT_ALGO)")
    return True


def test_container_sourced_pair_needs_no_registrar(prj):
    """A containerParam variant is constructed directly by its container."""
    print(f"\n{'='*70}\nTest: containerParam pair needs no model registrar"
          f"\n{'='*70}")
    pair = (prj.getQualBlock('cont'), prj.getQualBlock('leaf'))
    if prj.registrarPairs[pair]['hasModelRegistrations']:
        print("FAIL: persisted requirements retained a registrar for the "
              "container-sourced variant")
        return False
    view = prj.getRegistrarConfigView(pair[1], pair[0])
    if view['hasRegistrations'] or view['registeredVariants']:
        print(f"FAIL: registrar view retained registrations: {view}")
        return False
    emitted = {os.path.basename(path)
               for path in prj.config.getConfig('BUILDMANIFEST')['scGenFiles']}
    if 'leafRegistrar.cppm' in emitted:
        print("FAIL: build manifest retained leafRegistrar.cppm")
        return False
    print("PASS: persisted requirements, view and manifest all suppress it")
    return True


def _run_cell(cell, *args):
    """Run one cell, reporting an exception as that cell's failure.

    Without this an exception in one cell hides every later cell's verdict,
    which is how a broken edit once cost the SystemVerilog cell silently.
    """
    try:
        return cell(*args)
    except Exception as exc:
        print(f"FAIL: {cell.__name__} raised {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return False


def run_all_tests():
    if shutil.which(CXX) is None:
        raise RuntimeError(f"{CXX} is not on PATH; it is the compiler the "
                           f"arch2code makefiles use and this suite needs it to "
                           f"resolve the emitted Config template")
    ok = _run_cell(test_wider_container_domain_is_rejected)
    # The container's bound equals the child's: the accepted disposition, on two
    # different backing constants.
    db_path, paths, result = _build_database(CHILD_MAX, 'contparam_accept_test')
    try:
        if result.returncode != 0:
            print("FAIL: equal-domain container/child pair was rejected\n"
                  f"{result.stdout}\n{result.stderr}")
            return 1
        prj = projectOpen(db_path)
        ok = _run_cell(test_equal_domain_accepted_and_value_resolves, prj) and ok
        ok = _run_cell(test_systemverilog_forwards_container_symbol, prj) and ok
        ok = _run_cell(test_container_sourced_pair_needs_no_registrar, prj) and ok
    finally:
        cleanup(paths)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
