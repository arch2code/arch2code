#!/usr/bin/env python3
"""TT.4: Nested router whose upstreamPort carries parameterizable structures.

The nested router declares `params:` and `ipParameters:` with a
parameter that drives the data structure on its own
`addressBlock.upstreamPort` interface. Asserts that the post-parse
pass tolerates parameterizable structures on the router-to-router
register-bus interface, emits the parent-to-child router bind with the
child-side interface name, and that the nested router's block is
flagged `isParameterizable`.

The resolved parameter value matches the primary router's upstream
data width so that the parent → nested router-to-router bind remains
packed-form compatible. Width-mismatch behavior is covered by the
E3.2 prerequisite fixture, not here.

Topology::

    uTop (top)
    +-- uAPBDecode ............ primary router (upstream=apbReg)
    +-- uMid (mid)
        +-- uParamRouter (paramMidRouter, variant=paramMidV0)
        |     params:           [PARAM_UPSTREAM_WIDTH]
        |     upstreamPort:     paramApb       (parameterizable data;
        |                                       paramUpstreamDataSt)
        |     registerDecoder:  apbReg
        +-- uMidLeaf (midLeaf, addressGroup=mid)

    Parent-to-child bind uAPBDecode -> uMid is emitted under the
    child-side interface name (paramApb), and the container-boundary
    connectionMap on uParamRouter declares port 'paramApb'.
"""

import sys

from _addrctl_helpers import (
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_block,
    find_connection_maps,
    find_connections,
    find_instance,
    projectOpen,
    render_leaf,
)


# Inlined preamble: APB primary-side interface plus the nested router's
# parameterizable upstream interface and the parameterizable data type.
# Merged into a single set of top-level keys so ruamel.yaml's duplicate-
# key check does not fire when concatenating with helper preambles.
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
        PARAM_UPSTREAM_WIDTH:
            value: 32
            maxValue: 32
            desc: "Parameterizable data width on the nested router's upstreamPort"
    types:
        paramUpstreamDataT:
            width: PARAM_UPSTREAM_WIDTH
            maxBitwidth: 32
            desc: "Parameterizable router-bus data word"

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }
    paramUpstreamDataSt:
        data: { varType: paramUpstreamDataT, generator: data }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    paramApb:
        desc: "Nested router's upstreamPort interface with parameterizable data"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: paramUpstreamDataSt, structureType: data_t }
"""


ARCH_YAML = (
    PARAM_PREAMBLE
    + """
blocks:
    top:
        desc: "Primary container"
        hasMdl: true
    mid:
        desc: "Nested router's container"
        hasMdl: true
    apbDecode:
        desc: "Primary router"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
    paramMidRouter:
        desc: "Nested router declaring params; upstreamPort uses paramApb"
        hasMdl: true
        params: [PARAM_UPSTREAM_WIDTH]
        addressBlock:
            addressGroup: mid
            addressIncrement: 0x00100000
            maxAddressSpaces: 16
            varType: addr_id_mid
            enumPrefix: ADDR_ID_MID_
            upstreamPort: paramApb
            registerDecoderPort: apbReg
"""
    + render_leaf('midLeaf')
    + """
instances:
    uTop:          { container: top, instanceType: top }
    uAPBDecode:    { container: top, instanceType: apbDecode }
    uMid:          { container: top, instanceType: mid }
    uParamRouter:  { container: mid, instanceType: paramMidRouter, variant: paramMidV0 }
    uMidLeaf:      { container: mid, instanceType: midLeaf, addressGroup: mid }

parameters:
    paramMidRouter:
        - { variant: paramMidV0, param: PARAM_UPSTREAM_WIDTH, value: 32 }

registers:
    - { register: cfg, regType: rw, block: midLeaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("TT.4: nested router with parameterizable upstream interface")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        _router_key, router_row = find_block(prj, 'paramMidRouter')
        assert bool(router_row.get('isParameterizable')), (
            "paramMidRouter must be flagged isParameterizable; "
            f"got {router_row.get('isParameterizable')!r}"
        )

        # Parent-to-child router bind: parent dispatches to the nested
        # router's container sibling (uMid). The connection's interface
        # is the child router's upstream interface (paramApb).
        parent_to_child = find_connections(prj, src='uAPBDecode', dst='uMid')
        assert len(parent_to_child) == 1, (
            f"expected 1 uAPBDecode->uMid bind, got {len(parent_to_child)}"
        )
        assert parent_to_child[0]['interface'] == 'paramApb', (
            f"parent-to-child bind must name the child router's upstream "
            f"interface; got '{parent_to_child[0]['interface']}'"
        )

        # Boundary connectionMap on the container routes the inherited
        # paramApb port through to the nested router instance.
        boundary = find_connection_maps(prj, instance='uParamRouter')
        assert any(cm.get('port') == 'paramApb' for cm in boundary), (
            f"nested-router upstream connectionMap must declare port "
            f"'paramApb'; got {boundary}"
        )

        # Router-to-leaf bind from the nested router.
        leaf_bind = find_connections(prj, src='uParamRouter', dst='uMidLeaf')
        assert len(leaf_bind) == 1, (
            f"expected 1 uParamRouter->uMidLeaf bind, got {len(leaf_bind)}"
        )

        # Handler block for the leaf and INSTANCES_WITH_REGAPB membership.
        find_block(prj, 'midLeaf_regs')
        find_instance(prj, 'u_midLeaf_regs')
        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uMid', 'uMidLeaf'):
            key, _ = find_instance(prj, simple)
            assert key in instances_with_regapb, (
                f"INSTANCES_WITH_REGAPB missing '{key}'"
            )

        assert_no_global_register_binds(prj)
        print("PASS: TT.4")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
