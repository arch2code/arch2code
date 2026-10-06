#!/usr/bin/env python3
"""An hdlparam that resolves to no width stops the render.

An `hdlparams:` entry in an interface_defs entry supplies a signal width, and on
the SystemC side a positional template argument for the Verilated bridge. There
is no way to emit the signal without the width: a skipped entry would emit an
illegal `sc_bv<0>` / `bit [-1:0]`, and would silently retype every later
positional argument. Both render paths must therefore report what failed and
stop, so the malformed file is never written.

The case covered here is an hdlparam whose `value:` names a parameter the
interface declares `optional:` and the interface leaves unbound. The parameter
is declared, so it is bound into the render helper's parameter map, but it
carries no structure, and `get_struct_width` reports the structureKey it was
handed resolving to nothing.

An hdlparam naming a token the interface does not declare at all is a defect in
a developer-authored interface definition, and is checked statically over every
shipped definition by `test_interface_def_contracts.py`, so it is not
exercised at render time here.

The error is raised while rendering, not while building the database, so the
fixture project builds successfully and the render helpers are then driven
in-process. The render helpers stop through `exit(warningAndErrorReport())`,
which is the same value `arch2code.py` exits with, so asserting the raised
SystemExit code is non-zero asserts the build fails.
"""

import io
import os
import contextlib
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
from pysrc.arch2codeHelper import warningAndErrorReport
import pysrc.arch2codeGlobals as arch2codeGlobals
import pysrc.intf_gen_utils as intf_gen_utils


# `opt_stream` is a minimal streaming protocol that declares the parameter its
# tustrb_t hdlparam evaluates, but declares it optional, and `optIf` below
# leaves it unbound, so the hdlparam is handed a structureKey that names no
# structure. `goodIf` is a stock axi4_stream, whose hdlparams do resolve, and is
# rendered as the control.
ARCH_YAML = """interface_defs:
  opt_stream:
    parameters:
      tdata_t: {datatype: struct}
      tuser_t: {datatype: struct, optional: true}
    hdlparams:
      tustrb_t: {isEval: True, datatype: integer, value: 'tuser_t.to_bytes()'}
    signals:
      tvalid: bool
      tready: bool
      tdata: tdata_t
      tustrb: tustrb_t
    modports:
      src:
        inputs: ['tready']
        outputs: ['tvalid', 'tdata', 'tustrb']
      dst:
        inputs: ['tvalid', 'tdata', 'tustrb']
        outputs: ['tready']
    sc_channel:
      type: 'opt_stream'
      multicycle_types: []

constants:
  DATA_WIDTH: {value: 32, desc: "Data width"}
  ID_WIDTH: {value: 4, desc: "Stream id width"}

types:
  dataT: {width: DATA_WIDTH, desc: "Data"}
  idT: {width: ID_WIDTH, desc: "Stream id"}

variables:
  data: {type: dataT, desc: "Data"}
  id: {type: idT, desc: "Stream id"}

structures:
  dataSt: {data: {}}
  idSt: {id: {}}

interfaces:
  optIf:
    interfaceType: opt_stream
    desc: "Interface leaving unbound the optional parameter an hdlparam evaluates"
    structures:
      - {structure: dataSt, structureType: tdata_t}
  goodIf:
    interfaceType: axi4_stream
    desc: "Interface whose definition has resolvable hdlparams"
    structures:
      - {structure: dataSt, structureType: tdata_t}
      - {structure: idSt, structureType: tid_t}
      - {structure: idSt, structureType: tdest_t}

blocks:
  top: {desc: "Top block"}
  producer: {desc: "Producer block"}
  consumer:
    desc: "Consumer block"
    ports:
      inOpt: {interface: optIf, direction: dst}
      inGood: {interface: goodIf, direction: dst}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer}
  uConsumer: {container: top, instanceType: consumer}

connections:
  - {interface: optIf, src: uProducer, srcport: outOpt, dst: uConsumer, dstport: inOpt}
  - {interface: goodIf, src: uProducer, srcport: outGood, dst: uConsumer, dstport: inGood}
"""


PROJECT_YAML = """projectName: hdlparam_error_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {arch_name}
"""


UNBOUND_SUBSTRINGS = [
    "does not name a structure",  # the failed lookup, not a width of zero
    "supplies no width",
]


FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


def create_test_files():
    arch_fd, arch_path = tempfile.mkstemp(
        suffix='.yaml', prefix='hdlparam_error_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(ARCH_YAML)

    project_fd, project_path = tempfile.mkstemp(
        suffix='_project.yaml', prefix='hdlparam_error_proj_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(PROJECT_YAML.format(arch_name=os.path.basename(arch_path)))

    return project_path, arch_path


def build_database():
    project_path, arch_path = create_test_files()
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '--yaml', project_path, '--db', db_path],
            capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to build database:\n"
                f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        return db_path, project_path, arch_path
    except Exception:
        cleanup((project_path, arch_path, db_path))
        raise


def cleanup(paths):
    for path in paths:
        if path and os.path.exists(path):
            os.unlink(path)


def port_data(block_data, port_name):
    for port_group in block_data['ports'].values():
        if port_name in port_group:
            return port_group[port_name]
    raise KeyError(port_name)


def render(fn, proj, block_data, port_name):
    """Render one port.

    Returns (errors raised, SystemExit code or None, captured diagnostics). A
    render that stops raises SystemExit carrying the value arch2code.py would
    have exited with; a render that completes returns None for it.
    """
    before = arch2codeGlobals.errorCount
    buffer = io.StringIO()
    exit_code = None
    with contextlib.redirect_stdout(buffer):
        try:
            fn(port_data(block_data, port_name), proj, block_data)
        except SystemExit as exc:
            exit_code = exc.code
    return arch2codeGlobals.errorCount - before, exit_code, buffer.getvalue()


def check_diagnostic(label, needles, raised, exit_code, output):
    check(raised == 1, f"{label} raises exactly one error (raised {raised})")
    check(exit_code not in (None, 0),
          f"{label} stops the render rather than writing the file "
          f"(exit code {exit_code})")
    for needle in needles:
        check(needle in output,
              f"{label} diagnostic names {needle}")
    if raised != 1 or exit_code in (None, 0) or not all(n in output for n in needles):
        print(f"  ---- {label} output ----\n{output}")


def main():
    print("=" * 72)
    print("TESTING UNRESOLVABLE interface_defs hdlparam DIAGNOSTIC")
    print("=" * 72)
    arch2codeGlobals.disableColors = True
    try:
        db_path, project_path, arch_path = build_database()
    except RuntimeError as exc:
        print(f"  FAIL: fixture project must build: {exc}")
        return 1
    try:
        proj = projectOpen(db_path)
        consumer = proj.getBlockData(proj.getQualBlock('consumer'))

        print("\n[control] a resolvable hdlparam renders silently")
        raised, exit_code, _ = render(intf_gen_utils.sv_gen_modport_signal_blast,
                                      proj, consumer, 'inGood')
        check(raised == 0 and exit_code is None,
              "SystemVerilog blast of axi4_stream renders without error")
        raised, exit_code, _ = render(intf_gen_utils.sc_gen_modport_signal_blast,
                                      proj, consumer, 'inGood')
        check(raised == 0 and exit_code is None,
              "SystemC blast of axi4_stream renders without error")

        print("\n[sv] hdlparam on an unbound optional, SystemVerilog signal blast")
        raised, exit_code, output = render(intf_gen_utils.sv_gen_modport_signal_blast,
                                           proj, consumer, 'inOpt')
        check_diagnostic("SystemVerilog blast", UNBOUND_SUBSTRINGS,
                         raised, exit_code, output)

        print("\n[sc] hdlparam on an unbound optional, SystemC signal blast")
        raised, exit_code, output = render(intf_gen_utils.sc_gen_modport_signal_blast,
                                           proj, consumer, 'inOpt')
        check_diagnostic("SystemC blast", UNBOUND_SUBSTRINGS,
                         raised, exit_code, output)

        print("\n[exit] the accumulated errors fail the build")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = warningAndErrorReport()
        check(exit_code != 0,
              "warningAndErrorReport(), the value arch2code.py exits with, "
              f"is non-zero (got {exit_code})")
    finally:
        cleanup((db_path, project_path, arch_path))

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all hdlparam diagnostic checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
