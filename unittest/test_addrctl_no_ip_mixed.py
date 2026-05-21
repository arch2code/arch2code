#!/usr/bin/env python3
"""T4.3: Non-parameterized leaf and parameterized leaf under one router.

Asserts the post-parse pass treats both leaves identically — one
router-to-leaf bind per leaf instance, one handler per leaf block —
regardless of whether the leaf carries `params:` and a `variant:`
binding.
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
    + """    paramLeaf:
        desc: "Routed leaf with a block-level parameter"
        hasMdl: true
        params: [LEAF_WIDTH]
        registerPorts:
            regs: { interface: apbReg }
    plainLeaf:
        desc: "Routed leaf with no parameters"
        hasMdl: true
        registerPorts:
            regs: { interface: apbReg }

instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uParamLeaf:  { container: top, instanceType: paramLeaf, addressGroup: top, variant: variantA }
    uPlainLeaf:  { container: top, instanceType: plainLeaf, addressGroup: top }

parameters:
    paramLeaf:
        - { variant: variantA, param: LEAF_WIDTH, value: 8 }

registers:
    - { register: cfgP, regType: rw, block: paramLeaf, structure: cfgRegSt, desc: "" }
    - { register: cfgN, regType: rw, block: plainLeaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("T4.3: parameterized + non-parameterized leaf under one router")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Both leaves receive their dispatch bind.
        for dst in ('uParamLeaf', 'uPlainLeaf'):
            conns = find_connections(prj, src='uAPBDecode', dst=dst)
            assert len(conns) == 1, \
                f"expected exactly one uAPBDecode->{dst} bind, got {len(conns)}"

        # Both leaves get a handler block and instance.
        for block, inst in (('paramLeaf_regs', 'u_paramLeaf_regs'),
                            ('plainLeaf_regs', 'u_plainLeaf_regs')):
            find_block(prj, block)
            find_instance(prj, inst)

        assert_no_global_register_binds(prj)
        print("PASS: T4.3")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
