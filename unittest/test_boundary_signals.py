#!/usr/bin/env python3
"""Test HDL wrapper boundary width spelling.

The wrappers should spell active widths directly from existing interface and
structure metadata. Parameterizable payloads stay symbolic (`Config` on the
SystemC side, block params on the SV side); fixed payloads stay fixed-width.

A required payload parameter that types no signal, only an isEval hdlparam,
still takes its bridge slot, sized by its bound payload.
"""

import sys
import os
import subprocess
import tempfile
import types

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
import pysrc.intf_gen_utils as intf_gen_utils
from templates.systemc import module_hdl_wrapper
from _addrctl_helpers import build_database, cleanup


def build_test_database():
    """Build a fresh database from the ip_test example project."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_boundary_')
    os.close(db_fd)

    project_yaml = os.path.join(
        base_dir, 'examples', 'ip_test', 'prj', 'yaml', 'ip_testProject.yaml')
    arch2code_path = os.path.join(base_dir, 'arch2code.py')
    cmd = [sys.executable, arch2code_path, '-y', project_yaml, '--db', db_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=base_dir)

    if result.returncode != 0:
        os.unlink(db_path)
        raise RuntimeError(
            f"Failed to build test database:\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}")
    return db_path


FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


def check_equal(actual, expected, message):
    check(actual == expected, f"{message}: expected {expected!r}, got {actual!r}")


def port_data(block_data, port_name):
    for port_group in block_data['ports'].values():
        if port_name in port_group:
            return port_group[port_name]
    raise KeyError(port_name)


def sv_mp(proj, block_data, port_name):
    return intf_gen_utils.sv_gen_modport_signal_blast(
        port_data(block_data, port_name), proj, block_data)


def sc_mp(proj, block_data, port_name):
    return intf_gen_utils.sc_gen_modport_signal_blast(
        port_data(block_data, port_name), proj, block_data)


def test_ip(proj):
    print("\n[ip] wrapper boundary widths")
    ret = proj.getBlockData(proj.getQualBlock('ip'))
    ip_data_sv = sv_mp(proj, ret, 'ipDataIf')
    ip_data_sc = sc_mp(proj, ret, 'ipDataIf')

    check('input bit [(IP_DATA_WIDTH + 1)-1:0] ipDataIf_data' in ip_data_sv['ports'],
          "ipDataIf SV payload uses symbolic active width")
    check_equal(ip_data_sc['hdl_if_decl'],
                'push_ack_hdl_if<sc_bv<ipDataSt<Config>::_bitWidth>> ipDataIf_hdl_inst;',
                "ipDataIf SystemC hdl_if uses Config-dependent _bitWidth")
    check_equal(ip_data_sc['bfm_decl'],
                'push_ack_dst_bfm<ipDataSt<Config>, sc_bv<ipDataSt<Config>::_bitWidth>> ipDataIf_bfm_inst;',
                "ipDataIf SystemC BFM uses Config-dependent bridge width")

    regs_sv = sv_mp(proj, ret, 'regs')
    check('input bit [31:0] regs_paddr' in regs_sv['ports'],
          "regs paddr remains fixed 32-bit")
    check('input bit [31:0] regs_pwdata' in regs_sv['ports'],
          "regs pwdata remains fixed 32-bit")
    check('output bit [31:0] regs_prdata' in regs_sv['ports'],
          "regs prdata remains fixed 32-bit")


def test_src(proj):
    print("\n[src] wrapper boundary widths")
    ret = proj.getBlockData(proj.getQualBlock('src'))
    out0_sv = sv_mp(proj, ret, 'out0')
    out1_sv = sv_mp(proj, ret, 'out1')
    out0_sc = sc_mp(proj, ret, 'out0')
    out1_sc = sc_mp(proj, ret, 'out1')

    check('output bit [(OUT0_DATA_WIDTH + 1)-1:0] out0_data' in out0_sv['ports'],
          "out0 SV payload uses OUT0_DATA_WIDTH")
    check('output bit [(OUT1_DATA_WIDTH + 1)-1:0] out1_data' in out1_sv['ports'],
          "out1 SV payload uses OUT1_DATA_WIDTH")
    check_equal(out0_sc['hdl_if_decl'],
                'push_ack_hdl_if<sc_bv<srcOut0St<Config>::_bitWidth>> out0_hdl_inst;',
                "out0 SystemC hdl_if uses Config-dependent _bitWidth")
    check_equal(out1_sc['hdl_if_decl'],
                'push_ack_hdl_if<sc_bv<srcOut1St<Config>::_bitWidth>> out1_hdl_inst;',
                "out1 SystemC hdl_if uses Config-dependent _bitWidth")


# payload_t types no signal; only mask_t, its byte count, does.
BYTE_MASK_ARCH = """
interface_defs:
    byte_mask:
        parameters:
            payload_t: { datatype: struct }
        hdlparams:
            mask_t: { datatype: integer, isEval: true, value: 'payload_t.to_bytes()' }
        signals:
            mask: mask_t
            valid: bool
        modports:
            src: { inputs: [], outputs: [mask, valid] }
            dst: { inputs: [mask, valid], outputs: [] }
        sc_channel: { type: byte_mask, multicycle_types: [] }

types:
    dataT: { width: 32, desc: "Payload width" }

structures:
    dataSt:
        value: { varType: dataT, desc: "Payload" }

interfaces:
    maskIf:
        interfaceType: byte_mask
        desc: "One mask bit per payload byte"
        structures:
            - { structure: dataSt, structureType: payload_t }

blocks:
    top: { desc: "Top block" }
    leaf:
        desc: "Byte mask leaf"
        hasMdl: true
        hasRtl: true
        hasVl: true
        clocks:
            clk: { period: 10 }
        ports:
            out: { interface: maskIf, direction: src }

instances:
    uTop: { container: top, instanceType: top }
"""


def test_byte_mask():
    print("\n[byte_mask] required payload that types no signal")
    db_path, project_path, arch_paths = build_database(
        BYTE_MASK_ARCH, project_name='boundary_byte_mask')
    try:
        proj = projectOpen(db_path)
        ret = proj.getBlockData(proj.getQualBlock('leaf'))

        def render(section):
            args = types.SimpleNamespace(section=section, hierarchy=False)
            return module_hdl_wrapper.render_sc(args, proj, ret).splitlines()

        check_equal(render('hdl_if_decl'),
                    ['byte_mask_hdl_if<sc_bv<32>, sc_bv<4>> out_hdl_inst;'],
                    "hdl_if takes the 32-bit payload then the 4-bit mask")
        check_equal(render('bfm_decl'),
                    ['byte_mask_src_bfm<dataSt, sc_bv<32>, sc_bv<4>> out_bfm_inst;'],
                    "BFM splices the bridge group after the payload")
        check('output bit [3:0] out_mask' in sv_mp(proj, ret, 'out')['ports'],
              "SV wrapper mask port is 4 bits")
        leafKey = proj.getQualBlock('leaf')
        top = next(t for t, v in proj.config.getConfig('VLTOPS').items()
                   if v['blockKey'] == leafKey)
        pins = [(p['pin'], p['width'], p['vector'])
                for p in proj.getVlTopBoundaryPins(ret, top)]
        check_equal(pins[:2], [('out_mask', 4, True), ('out_valid', 1, False)],
                    "boundary pins size the mask by the payload's bytes")
    finally:
        cleanup([project_path, db_path] + arch_paths)


def main():
    print("=" * 72)
    print("TESTING HDL WRAPPER BOUNDARY WIDTH SPELLING")
    print("=" * 72)
    db_path = build_test_database()
    try:
        proj = projectOpen(db_path)
        test_ip(proj)
        test_src(proj)
    finally:
        os.unlink(db_path)
    test_byte_mask()

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all wrapper-boundary checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
