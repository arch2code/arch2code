#!/usr/bin/env python3
"""TT.3: IP leaf whose registerPorts: interface references a parameterizable type.

The leaf declares `ipParameters:` with a parameter that drives a
register-bus data type, and the leaf's `registerPorts:` interface binds
a structure that references that parameterized type. Two variants of
the leaf coexist under a single router. Asserts that the post-parse
pass synthesises one handler block for the parameterizable leaf, emits
two distinct router-to-leaf binds (one per instance), and that the leaf
block is flagged `isParameterizable`.

Both variants resolve the register width to the same value so that the
emitted bind interface remains consistent with the router's upstream
`apbReg`. The intent here is structural coverage of the parameterized-
type code path on the register-bus interface; per-variant width
*mismatch* diagnostics are covered separately by the E3.2 prerequisite
fixture.

Topology::

    uTop (top)
    +-- uAPBDecode ........... primary router (upstream=apbReg)
    +-- uLeaf0 (paramLeaf, variant=paramVar0, PARAM_REG_DATA_WIDTH=32)
    +-- uLeaf1 (paramLeaf, variant=paramVar1, PARAM_REG_DATA_WIDTH=32)

    paramLeaf block:
        params:        [PARAM_REG_DATA_WIDTH]    -> isParameterizable
        registerPorts: regs -> paramReg interface
                                +-- addr_t = apbAddrSt
                                +-- data_t = paramRegDataSt (parameterized)

    Both leaf instances share the same handler block (paramLeaf_regs)
    and handler instance (u_paramLeaf_regs); two distinct router-to-
    leaf binds are emitted (uAPBDecode -> uLeaf0, uAPBDecode -> uLeaf1).
"""

import sys

from _addrctl_helpers import (
    build_database,
    cleanup,
    find_block,
    find_connections,
    find_instance,
    iter_rows,
    projectOpen,
    render_router,
)

# Inlined APB+leaf preamble. The base APB_PREAMBLE helper declares
# `structures:` and `interfaces:` top-level keys; this fixture needs to
# add a parameterizable structure and a leaf-scope interface alongside
# them. ruamel.yaml rejects duplicate top-level keys, so we merge all
# constants / types / structures / interfaces declarations into one
# block here rather than concatenating two preambles.
PARAM_PREAMBLE = """constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Register bus data width" }
    REG_WIDTH:  { value: 16, desc: "Register payload width" }

types:
    apbAddrT: { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT: { width: DATA_WIDTH, desc: "APB data" }
    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }

ipParameters:
    constants:
        PARAM_REG_DATA_WIDTH:
            value: 32
            maxValue: 32
            desc: "Parameterizable data width on the leaf's register bus"
    types:
        paramRegDataT:
            width: PARAM_REG_DATA_WIDTH
            maxBitwidth: 32
            desc: "Parameterizable register-bus data word"

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }
    paramRegDataSt:
        data: { varType: paramRegDataT, generator: data }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    paramReg:
        desc: "Leaf register bus with parameterizable data structure"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: paramRegDataSt, structureType: data_t }
"""


ARCH_YAML = (
    PARAM_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    paramLeaf:
        desc: "Parameterizable leaf — register-bus structure uses an ipParameters type"
        hasMdl: true
        params: [PARAM_REG_DATA_WIDTH]
        registerPorts:
            regs: { interface: paramReg }
"""
    + render_router('apbDecode', 'top')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uLeaf0:      { container: top, instanceType: paramLeaf, addressGroup: top, variant: paramVar0 }
    uLeaf1:      { container: top, instanceType: paramLeaf, addressGroup: top, variant: paramVar1 }

parameters:
    paramLeaf:
        - { variant: paramVar0, param: PARAM_REG_DATA_WIDTH, value: 32 }
        - { variant: paramVar1, param: PARAM_REG_DATA_WIDTH, value: 32 }

registers:
    - { register: cfg, regType: rw, block: paramLeaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("TT.3: parameterizable register-bus interface on a leaf")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Leaf block is flagged parameterizable because it declares
        # ipParameters and binds them via `params:`.
        _leaf_key, leaf_row = find_block(prj, 'paramLeaf')
        assert bool(leaf_row.get('isParameterizable')), (
            "paramLeaf must be flagged isParameterizable; "
            f"got {leaf_row.get('isParameterizable')!r}"
        )

        # Handler block / instance: one per block type, not per leaf
        # instance — even though two variants exist.
        find_block(prj, 'paramLeaf_regs')
        find_instance(prj, 'u_paramLeaf_regs')
        handler_blocks = [
            row for _key, row in iter_rows(prj, 'blocks')
            if row.get('block') == 'paramLeaf_regs'
        ]
        assert len(handler_blocks) == 1, (
            f"expected exactly one paramLeaf_regs handler block, "
            f"got {len(handler_blocks)}"
        )

        # Two distinct router-to-leaf binds, one per instance.
        bind_v0 = find_connections(prj, src='uAPBDecode', dst='uLeaf0')
        bind_v1 = find_connections(prj, src='uAPBDecode', dst='uLeaf1')
        assert len(bind_v0) == 1, \
            f"expected 1 uAPBDecode->uLeaf0 bind, got {len(bind_v0)}"
        assert len(bind_v1) == 1, \
            f"expected 1 uAPBDecode->uLeaf1 bind, got {len(bind_v1)}"
        assert bind_v0[0] is not bind_v1[0], \
            "per-instance binds must be distinct rows"

        # Both variants appear in INSTANCES_WITH_REGAPB.
        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uLeaf0', 'uLeaf1'):
            key, _ = find_instance(prj, simple)
            assert key in instances_with_regapb, \
                f"INSTANCES_WITH_REGAPB missing '{key}'"

        # The Stage 7 register-bus invariant: no synthesised register-
        # bus bind carries `_context: '_global'`. This is asserted in
        # every test_addrctl_*.py fixture for repository-wide coverage.
        # See _addrctl_helpers.assert_no_global_register_binds.
        from _addrctl_helpers import assert_no_global_register_binds
        assert_no_global_register_binds(prj)
        print("PASS: TT.3")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
