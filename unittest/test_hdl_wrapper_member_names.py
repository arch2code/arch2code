#!/usr/bin/env python3
"""HDL wrapper member names never collide with interface class names.

The Verilated SystemC wrapper declares one Verilated bridge member and one BFM
member per port, named by `intf_gen_utils.sc_hdl_member_names`. A member named
like a class hides that class for the rest of the wrapper, so the next
declaration that spells the class fails to compile. The old names,
`<port>_hdl_if` and `<port>_bfm`, did collide. A port `status` of type status
declared a member `status_hdl_if`, and the next port's `status_hdl_if<...>`
declaration failed with "no template named 'status_hdl_if'". A port
`status_src` declared a member `status_src_bfm`, which is the BFM class itself.

The name check covers every shipped interface, with ports named after the
interface's sc_channel type and that type plus `_src` / `_dst`. The rendered
check builds the status repro and reads the hdl_if and BFM declarations the
wrapper template emits for it.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import types

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
import pysrc.intf_gen_utils as intf_gen_utils
from templates.systemc import module_hdl_wrapper


# The class names an interface contributes are its sc_channel type plus one of
# these generator-spelled suffixes.
CLASS_SUFFIXES = ('_channel', '_in', '_out', '_hdl_if', '_src_bfm', '_dst_bfm')

# `status` followed by a second status-typed port is the reported repro.
# `status_src` and `status_dst` would have declared members named like the
# status BFM classes.
ARCH_YAML = """constants:
  STATUS_WIDTH: {value: 8, desc: "Status width"}

types:
  statusT: {width: STATUS_WIDTH, desc: "Status"}

variables:
  value: {type: statusT, desc: "Status value"}

structures:
  statusSt: {value: {}}

interfaces:
  statusIf:
    interfaceType: status
    desc: "Status"
    structures:
      - {structure: statusSt, structureType: data_t}

blocks:
  top: {desc: "Top block"}
  dut:
    desc: "Block whose port names match interface class names"
    ports:
      status: {interface: statusIf, direction: src}
      dft_ctrl: {interface: statusIf, direction: dst}
      status_src: {interface: statusIf, direction: src}
      status_dst: {interface: statusIf, direction: dst}
  peer:
    desc: "Other end of every dut port"
    ports:
      statusIn: {interface: statusIf, direction: dst}
      dftCtrlOut: {interface: statusIf, direction: src}
      statusSrcIn: {interface: statusIf, direction: dst}
      statusDstOut: {interface: statusIf, direction: src}

instances:
  uTop: {container: top, instanceType: top}
  uDut: {container: top, instanceType: dut}
  uPeer: {container: top, instanceType: peer}

connections:
  - {interface: statusIf, src: uDut, srcport: status, dst: uPeer, dstport: statusIn}
  - {interface: statusIf, src: uPeer, srcport: dftCtrlOut, dst: uDut, dstport: dft_ctrl}
  - {interface: statusIf, src: uDut, srcport: status_src, dst: uPeer, dstport: statusSrcIn}
  - {interface: statusIf, src: uPeer, srcport: statusDstOut, dst: uDut, dstport: status_dst}
"""

PROJECT_YAML = """projectName: hdlMemberNames
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

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
    """Build the fixture outside builder/base, so its database also carries
    the pro interface definitions. Returns (db, tmpdir)."""
    tmpdir = tempfile.mkdtemp(prefix='hdl_member_names_')
    projDir = os.path.join(tmpdir, 'proj')
    os.makedirs(projDir)
    with open(os.path.join(projDir, 'arch.yaml'), 'w') as f:
        f.write(ARCH_YAML)
    projectPath = os.path.join(projDir, 'hdlMemberNamesProject.yaml')
    with open(projectPath, 'w') as f:
        f.write(PROJECT_YAML)
    dbPath = os.path.join(tmpdir, 'hdlMemberNames.db')
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', projectPath, '--db', dbPath],
        capture_output=True, text=True, timeout=300, cwd=base_dir, env=env)
    if result.returncode != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"failed to build fixture database:\n"
                           f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    return dbPath, tmpdir


def test_no_member_matches_a_class_name(proj):
    print("\n[names] no member name equals an interface class name")
    channelTypes = sorted({row['sc_channel']['type']
                           for row in proj.data['interface_defs'].values()})
    print(f"  sc_channel types: {', '.join(channelTypes)}")
    classNames = {channelType + suffix
                  for channelType in channelTypes for suffix in CLASS_SUFFIXES}
    collisions = []
    for channelType in channelTypes:
        for port in (channelType, channelType + '_src', channelType + '_dst'):
            for member in intf_gen_utils.sc_hdl_member_names(port):
                if member in classNames:
                    collisions.append(f"port '{port}' -> member '{member}'")
    check(not collisions,
          "ports named <T>, <T>_src and <T>_dst declare no member named like "
          f"a class (collisions: {collisions})")


def test_blast_uses_member_names(proj, dut):
    print("\n[blast] the port blast spells members through sc_hdl_member_names")
    for port in ('status', 'dft_ctrl', 'status_src', 'status_dst'):
        portData = next(group[port] for group in dut['ports'].values()
                        if port in group)
        mp = intf_gen_utils.sc_gen_modport_signal_blast(portData, proj, dut)
        check((mp['hdl_inst_name'], mp['bfm_inst_name'])
              == intf_gen_utils.sc_hdl_member_names(port),
              f"port '{port}' members come from sc_hdl_member_names")


def render_section(proj, dut, section):
    args = types.SimpleNamespace(section=section, hierarchy=False)
    return module_hdl_wrapper.render_sc(args, proj, dut).splitlines()


def test_rendered_repro(proj, dut):
    print("\n[render] the status repro declares distinct members")
    hdlDecls = render_section(proj, dut, 'hdl_if_decl')
    for line in hdlDecls:
        print(f"  {line}")
    check(len(hdlDecls) == 4, f"one hdl_if declaration per port, got {len(hdlDecls)}")
    check(hdlDecls[0].startswith('status_hdl_if<')
          and hdlDecls[0].endswith('> status_hdl_inst;'),
          "port 'status' declares status_hdl_if<...> status_hdl_inst")
    check(hdlDecls[1].startswith('status_hdl_if<')
          and hdlDecls[1].endswith('> dft_ctrl_hdl_inst;'),
          "the next status port's status_hdl_if<...> declaration follows it")

    bfmDecls = render_section(proj, dut, 'bfm_decl')
    for line in bfmDecls:
        print(f"  {line}")
    check(any(line.startswith('status_src_bfm<')
              and line.endswith('> status_src_bfm_inst;') for line in bfmDecls),
          "port 'status_src' declares status_src_bfm<...> status_src_bfm_inst")
    check(any(line.startswith('status_dst_bfm<')
              and line.endswith('> status_dst_bfm_inst;') for line in bfmDecls),
          "port 'status_dst' declares status_dst_bfm<...> status_dst_bfm_inst")

    connect = render_section(proj, dut, 'bfm_connect')
    check('status_bfm_inst.hdl_if_p(status_hdl_inst);' in connect,
          "the status BFM binds to the status bridge member")


def main():
    print("=" * 72)
    print("TESTING HDL WRAPPER MEMBER NAMES")
    print("=" * 72)
    try:
        dbPath, tmpdir = build_database()
    except RuntimeError as exc:
        print(f"  FAIL: fixture project must build: {exc}")
        return 1
    try:
        proj = projectOpen(dbPath)
        dut = proj.getBlockData(proj.getQualBlock('dut'))
        test_no_member_matches_a_class_name(proj)
        test_blast_uses_member_names(proj, dut)
        test_rendered_repro(proj, dut)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all HDL wrapper member name checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
