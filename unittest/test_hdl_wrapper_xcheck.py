#!/usr/bin/env python3
"""The HDL wrapper checks each port of a uvmAgent interface type for X and Z.

The wrapper's boundary pins are two-state, so an X the RTL drives onto an
output reaches SystemC as 0 and the run passes. The SV wrapper therefore
instantiates `<type>_xcheck` on the reconstructed interface of every port
whose interface type declares `uvmAgent: true`, clocked and reset by that
port's own domain. Verilator is two-state, so the instances sit under
`ifndef VERILATOR`.

A signal typed by an optional payload, axi4_stream's tuser, is checked only
when the port binds that payload, through the checker's CHECK_<SIGNAL>
parameter: an unbound one is an undriven placeholder.

The plain fixture block has an rdy_vld port on its default clock, a status
port on a second clock with its own reset, and a pop_ack port, whose type has
no agent and so gets no checker. The parameterized block's checkers are in the
wrapper body, and it has one axi4_stream port that binds tuser_t and one that
does not.
"""

import os
import subprocess
import sys
import tempfile
import types

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
from templates.systemVerilog import module_hdl_wrapper
from _tmp_helpers import remove_tree


ARCH_YAML = """ipParameters:
  constants:
    XC_W: {value: 8, maxValue: 16, desc: "Width knob of pdut"}

constants:
  DATA_WIDTH: {value: 8, desc: "Data width"}

types:
  dataT: {width: DATA_WIDTH, desc: "Data"}
  pDataT: {width: XC_W, desc: "Parameterized data"}

variables:
  value: {type: dataT, desc: "Value"}
  pValue: {type: pDataT, desc: "Parameterized value"}

structures:
  dataSt: {value: {}}
  pDataSt: {pValue: {}}

interfaces:
  dataIf:
    interfaceType: rdy_vld
    desc: "Data stream"
    structures:
      - {structure: dataSt, structureType: data_t}
  statusIf:
    interfaceType: status
    desc: "Status"
    structures:
      - {structure: dataSt, structureType: data_t}
  popIf:
    interfaceType: pop_ack
    desc: "Pop"
    structures:
      - {structure: dataSt, structureType: rdata_t}
  pDataIf:
    interfaceType: rdy_vld
    desc: "Parameterized data stream"
    structures:
      - {structure: pDataSt, structureType: data_t}
  axisUserIf:
    interfaceType: axi4_stream
    desc: "Stream that binds TUSER"
    structures:
      - {structure: dataSt, structureType: tdata_t}
      - {structure: dataSt, structureType: tid_t}
      - {structure: dataSt, structureType: tdest_t}
      - {structure: dataSt, structureType: tuser_t}
  axisNoUserIf:
    interfaceType: axi4_stream
    desc: "Stream that binds no TUSER"
    structures:
      - {structure: dataSt, structureType: tdata_t}
      - {structure: dataSt, structureType: tid_t}
      - {structure: dataSt, structureType: tdest_t}

blocks:
  top:
    desc: "Top block"
    hasVl: false
    hasRtl: false
    clocks:
      clk: {default: true}
      clkSlow: {}
    resets:
      rst_n: {clock: clk}
      rstSlow_n: {clock: clkSlow}
  dut:
    desc: "Block under test"
    hasVl: true
    clocks:
      clk: {default: true}
      clkSlow: {}
    resets:
      rst_n: {clock: clk}
      rstSlow_n: {clock: clkSlow}
    ports:
      dataIn: {interface: dataIf, direction: dst}
      statusOut: {interface: statusIf, direction: src, clock: clkSlow}
      popOut: {interface: popIf, direction: src}
  pdut:
    desc: "Parameterized block, whose checkers sit in the wrapper body"
    hasVl: true
    params: [XC_W]
    ports:
      pIn: {interface: pDataIf, direction: dst}
      axisUser: {interface: axisUserIf, direction: src}
      axisNoUser: {interface: axisNoUserIf, direction: src}
  pPeer:
    desc: "Other end of every pdut port"
    params: [XC_W]
    ports:
      pOut: {interface: pDataIf, direction: src}
      axisUserIn: {interface: axisUserIf, direction: dst}
      axisNoUserIn: {interface: axisNoUserIf, direction: dst}
  peer:
    desc: "Other end of every dut port"
    clocks:
      clk: {default: true}
      clkSlow: {}
    resets:
      rst_n: {clock: clk}
      rstSlow_n: {clock: clkSlow}
    ports:
      dataOut: {interface: dataIf, direction: src}
      statusIn: {interface: statusIf, direction: dst, clock: clkSlow}
      popIn: {interface: popIf, direction: dst}

instances:
  uTop: {container: top, instanceType: top}
  uDut: {container: top, instanceType: dut}
  uPeer: {container: top, instanceType: peer}
  uPdut: {container: top, instanceType: pdut, variant: v0}
  uPPeer: {container: top, instanceType: pPeer, variant: v0}

parameters:
  pdut:
    v0: {XC_W: 8}
  pPeer:
    v0: {XC_W: 8}

connections:
  - {interface: dataIf, src: uPeer, srcport: dataOut, dst: uDut, dstport: dataIn}
  - {interface: statusIf, src: uDut, srcport: statusOut, dst: uPeer, dstport: statusIn, clock: clkSlow}
  - {interface: popIf, src: uDut, srcport: popOut, dst: uPeer, dstport: popIn}
  - {interface: pDataIf, src: uPPeer, srcport: pOut, dst: uPdut, dstport: pIn}
  - {interface: axisUserIf, src: uPdut, srcport: axisUser, dst: uPPeer, dstport: axisUserIn}
  - {interface: axisNoUserIf, src: uPdut, srcport: axisNoUser, dst: uPPeer, dstport: axisNoUserIn}
"""

PROJECT_YAML = """projectName: hdlXcheck
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

clocks:
  clk: {desc: "Main clock", default: true, period: 1, timeUnit: ns}
  clkSlow: {desc: "Slow clock", period: 3, timeUnit: ns}

resets:
  rst_n: {desc: "Main reset", default: true, clock: clk}
  rstSlow_n: {desc: "Slow reset", clock: clkSlow}

projectFiles:
  - arch.yaml
"""


FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


def build_database():
    """Returns (db, tmpdir)."""
    tmpdir = tempfile.mkdtemp(prefix='hdl_xcheck_')
    try:
        projDir = os.path.join(tmpdir, 'proj')
        os.makedirs(projDir)
        with open(os.path.join(projDir, 'arch.yaml'), 'w') as f:
            f.write(ARCH_YAML)
        projectPath = os.path.join(projDir, 'hdlXcheckProject.yaml')
        with open(projectPath, 'w') as f:
            f.write(PROJECT_YAML)
        dbPath = os.path.join(tmpdir, 'hdlXcheck.db')
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '--yaml', projectPath, '--db', dbPath],
            capture_output=True, text=True, timeout=300, cwd=base_dir, env=env)
        if result.returncode != 0:
            raise RuntimeError(f"failed to build fixture database:\n"
                               f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        return dbPath, tmpdir
    except BaseException:
        remove_tree(tmpdir)
        raise


def render(proj, block, section):
    args = types.SimpleNamespace(section=section, mode='', parent=None, variant=None,
                                 sectionindent=0, template='module_hdl_sv_wrapper',
                                 fileMapKey=None)
    return [line.strip() for line in module_hdl_wrapper.render_sv(args, proj, block).splitlines()]


def test_wrapper_instances(proj, dut):
    print("\n[render] the SV wrapper checks the agent-typed ports")
    lines = render(proj, dut, '')
    for line in lines:
        if 'xcheck' in line or 'VERILATOR' in line:
            print(f"  {line}")
    instances = [line for line in lines if '_xcheck ' in line]
    check(instances == [
        'rdy_vld_xcheck dataIn_xcheck (.clk(clk), .rst_n(rst_n), .intf(dataIn));',
        'status_xcheck statusOut_xcheck (.clk(clkSlow), .rst_n(rstSlow_n), .intf(statusOut));'],
        "the rdy_vld port is checked on clk/rst_n and the status port on clkSlow/rstSlow_n")
    check(not any('popOut' in line for line in instances),
          "the pop_ack port, whose type has no agent, has no checker")
    if instances:
        first = lines.index(instances[0])
        last = lines.index(instances[-1])
        check(lines[first - 1] == '`ifndef VERILATOR' and lines[last + 1] == '`endif',
              "the checkers sit in one `ifndef VERILATOR block")
        check(first > next(i for i, line in enumerate(lines) if line.endswith(' dut (')),
              "the checkers follow the DUT instance")


def test_body_instances(proj, pdut):
    print("\n[render] the parameterized wrapper body checks its ports, tuser only where bound")
    lines = render(proj, pdut, 'body')
    instances = [line for line in lines if '_xcheck ' in line]
    for line in instances:
        print(f"  {line}")
    check(instances == [
        'rdy_vld_xcheck pIn_xcheck (.clk(clk), .rst_n(rst_n), .intf(pIn));',
        'axi4_stream_xcheck #(.CHECK_TUSER(1\'b1)) axisUser_xcheck '
        '(.clk(clk), .rst_n(rst_n), .intf(axisUser));',
        'axi4_stream_xcheck #(.CHECK_TUSER(1\'b0)) axisNoUser_xcheck '
        '(.clk(clk), .rst_n(rst_n), .intf(axisNoUser));'],
        "the body checks every port, with CHECK_TUSER on only for the port that binds tuser_t")
    if instances:
        first = lines.index(instances[0])
        check(lines[first - 1] == '`ifndef VERILATOR'
              and lines[lines.index(instances[-1]) + 1] == '`endif',
              "the body's checkers sit in one `ifndef VERILATOR block")


def main():
    print("=" * 72)
    print("TESTING HDL WRAPPER X/Z CHECKERS")
    print("=" * 72)
    try:
        dbPath, tmpdir = build_database()
    except RuntimeError as exc:
        print(f"  FAIL: fixture project must build: {exc}")
        return 1
    try:
        proj = projectOpen(dbPath)
        dut = proj.getBlockData(proj.getQualBlock('dut'))
        # The SV generator sets this from the file's GENERATED_CODE_PARAM line.
        dut['importPackages'] = []
        test_wrapper_instances(proj, dut)
        pdut = proj.getBlockData(proj.getQualBlock('pdut'))
        pdut['importPackages'] = []
        test_body_instances(proj, pdut)
    finally:
        remove_tree(tmpdir)

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} check(s) failed")
        return 1
    print("PASS: all HDL wrapper X/Z checker checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
