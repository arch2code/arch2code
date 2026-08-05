#!/usr/bin/env python3
"""One router, two non-parameterized leaves each with one register."""

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
    + render_leaf('leafA')
    + render_leaf('leafB')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeafA:     { container: top, instanceType: leafA, addressGroup: top }
    uLeafB:     { container: top, instanceType: leafB, addressGroup: top }

registers:
    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "Leaf A configuration" }
    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "Leaf B configuration" }
"""
)


def _run():
    print("single router, two non-parameterized leaves")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        for block_name in ('apbDecode', 'leafA', 'leafB'):
            _block_key, row = find_block(prj, block_name)
            assert not bool(row.get('isParameterizable')), (
                f"block '{block_name}' should not be parameterizable; "
                f"got {row.get('isParameterizable')!r}"
            )

        find_block(prj, 'leafA_regs')
        find_block(prj, 'leafB_regs')
        find_instance(prj, 'u_leafA_regs')
        find_instance(prj, 'u_leafB_regs')

        conns_a = find_connections(prj, src='uAPBDecode', dst='uLeafA')
        conns_b = find_connections(prj, src='uAPBDecode', dst='uLeafB')
        assert len(conns_a) == 1, \
            f"expected one uAPBDecode->uLeafA bind, got {len(conns_a)}"
        assert len(conns_b) == 1, \
            f"expected one uAPBDecode->uLeafB bind, got {len(conns_b)}"

        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        leaf_a_key, _ = find_instance(prj, 'uLeafA')
        leaf_b_key, _ = find_instance(prj, 'uLeafB')
        assert leaf_a_key in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB missing '{leaf_a_key}'"
        assert leaf_b_key in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB missing '{leaf_b_key}'"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
