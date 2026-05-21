#!/usr/bin/env python3
"""T1.3: One router, two routed leaves at the same level.

Asserts that two router-to-leaf binds are emitted (one per leaf
instance), each carrying the leaf's authored port name, and that one
handler block / instance is synthesised per leaf block.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_block,
    find_connections,
    find_instance,
    projectOpen,
    render_leaf,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leafA', port_name='regsA')
    + render_leaf('leafB', port_name='regsB')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeafA:     { container: top, instanceType: leafA, addressGroup: top }
    uLeafB:     { container: top, instanceType: leafB, addressGroup: top }

registers:
    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "" }
    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("T1.3: single router, two routed leaves at the same level")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        find_block(prj, 'leafA_regs')
        find_block(prj, 'leafB_regs')
        find_instance(prj, 'u_leafA_regs')
        find_instance(prj, 'u_leafB_regs')

        conns_a = find_connections(prj, src='uAPBDecode', dst='uLeafA')
        conns_b = find_connections(prj, src='uAPBDecode', dst='uLeafB')
        assert len(conns_a) == 1, f"expected 1 uAPBDecode->uLeafA bind, got {len(conns_a)}"
        assert len(conns_b) == 1, f"expected 1 uAPBDecode->uLeafB bind, got {len(conns_b)}"
        assert conns_a[0]['dstport'] == 'regsA', \
            f"uLeafA dstport expected 'regsA', got {conns_a[0]['dstport']}"
        assert conns_b[0]['dstport'] == 'regsB', \
            f"uLeafB dstport expected 'regsB', got {conns_b[0]['dstport']}"

        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        leafA_inst, _ = find_instance(prj, 'uLeafA')
        leafB_inst, _ = find_instance(prj, 'uLeafB')
        assert leafA_inst in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB missing '{leafA_inst}'"
        assert leafB_inst in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB missing '{leafB_inst}'"

        assert_no_global_register_binds(prj)
        print("PASS: T1.3")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
