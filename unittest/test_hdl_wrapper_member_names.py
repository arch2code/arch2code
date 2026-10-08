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

The name check reads every class, struct, alias and typedef the interface
library headers declare, discovered by walking the interface trees, and
requires that none ends in `_inst`, the suffix both member names carry. A
negative case proves the scan reports such a type. The rendered check builds
the status repro and reads the hdl_if and BFM declarations the wrapper
template emits for it.
"""

import os
import re
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
from _tmp_helpers import remove_tree


# The shipped interface libraries, as test_interface_def_contracts.py walks
# them. `pro` is a separate repository and is absent from a base-only checkout.
INTERFACE_ROOTS = (
    os.path.join(base_dir, 'interfaces'),
    os.path.join(os.path.dirname(base_dir), 'pro', 'interfaces'),
)

# Names a C++ header declares as a type: class/struct, `using X =` and typedef.
TYPE_NAME_RE = re.compile(r'\b(?:class|struct)\s+(\w+)'
                          r'|\busing\s+(\w+)\s*='
                          r'|\btypedef\b[^;{]*?(\w+)\s*(?:\[[^\]]*\])?\s*;')

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
    try:
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
            raise RuntimeError(f"failed to build fixture database:\n"
                               f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        return dbPath, tmpdir
    except BaseException:
        remove_tree(tmpdir)
        raise


def library_type_names(roots):
    """Type name -> the header declaring it, over every .h under `roots`."""
    names = {}
    for root in roots:
        for dirpath, _, files in os.walk(root):
            for name in files:
                if not name.endswith('.h'):
                    continue
                path = os.path.join(dirpath, name)
                with open(path) as f:
                    for match in TYPE_NAME_RE.finditer(f.read()):
                        names.setdefault(next(g for g in match.groups() if g), path)
    return names


def inst_suffixed(names):
    return sorted(f"{name} ({path})" for name, path in names.items() if name.endswith('_inst'))


def test_no_library_type_ends_in_inst():
    print("\n[names] no interface library type ends in _inst")
    roots = [root for root in INTERFACE_ROOTS if os.path.isdir(root)]
    names = library_type_names(roots)
    print(f"  {len(names)} type names in {', '.join(roots)}")
    check('status_hdl_if' in names and 'status_src_bfm' in names,
          "the scan finds the status bridge and BFM classes")
    for member in intf_gen_utils.sc_hdl_member_names('status'):
        check(member.endswith('_inst'), f"member '{member}' carries the _inst suffix")
    bad = inst_suffixed(names)
    check(not bad, "no class, struct, alias or typedef in the interface library "
          "ends in _inst, so <port>_hdl_inst / <port>_bfm_inst never hide a library "
          f"type (found: {bad})")

    tmpdir = tempfile.mkdtemp(prefix='hdl_member_names_lib_')
    try:
        with open(os.path.join(tmpdir, 'status_bad.h'), 'w') as f:
            f.write('template<typename T> class status_hdl_inst { };\n')
        check(inst_suffixed(library_type_names([tmpdir])),
              "a library header declaring class status_hdl_inst is reported")
    finally:
        shutil.rmtree(tmpdir)


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
        test_no_library_type_ends_in_inst()
        test_blast_uses_member_names(proj, dut)
        test_rendered_repro(proj, dut)
    finally:
        remove_tree(tmpdir)

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all HDL wrapper member name checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
