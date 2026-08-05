#!/usr/bin/env python3
"""Nested router that is itself parameterized.

Two-level topology (primary + one nested router) where the nested
router block declares `params:` and `ipParameters:` with two named
variants. The single router instance binds one variant; the other
remains declared so the router is reusable under either parent
configuration. Asserts the post-parse pass tolerates parameterized
router blocks, the nested-router walk identifies the primary correctly,
and `isParameterizable` is set on the router's block row.

This covers a nested router whose own block carries parameterization
metadata (params + variants) without the parameterized structures lying on
the upstream register-bus interface itself.

Topology::

    uTop (top)
    +-- uAPBDecode ............ primary router (upstream=apbReg)
    +-- uSub (sub)
        +-- uSubDecode (paramSubDecode, variant=paramSubV0)
        |     params:           [PARAM_ROUTER_KNOB]  -> isParameterizable
        |     upstreamPort:     apbReg               (NOT parameterized)
        |     registerDecoder:  apbReg
        +-- uSubLeaf (subLeaf, addressGroup=sub)

    Variants declared: paramSubV0 (KNOB=4), paramSubV1 (KNOB=8).
    Only paramSubV0 is bound; paramSubV1 remains available for reuse.
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


# Inlined preamble: the router's `paramScratchSt` is a parameterizable
# structure derived from `PARAM_ROUTER_KNOB`; declaring it on the router
# block (without exposing it as an upstream interface) gives the router
# a parameterizable surface — and therefore an `isParameterizable: true`
# flag — without altering the register-bus structures themselves.
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
        PARAM_ROUTER_KNOB:
            value: 4
            maxValue: 8
            desc: "Per-variant knob bound on the nested router"
    types:
        paramRouterKnobT:
            width: PARAM_ROUTER_KNOB
            maxBitwidth: 8
            desc: "Parameterizable knob exposed on the router block"

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
"""


ARCH_YAML = (
    PARAM_PREAMBLE
    + """
blocks:
    top:
        desc: "Primary container"
        hasMdl: true
    sub:
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
    paramSubDecode:
        desc: "Parameterized nested router; reusable under two variants"
        hasMdl: true
        params: [PARAM_ROUTER_KNOB]
        addressBlock:
            addressGroup: sub
            addressIncrement: 0x00100000
            maxAddressSpaces: 16
            varType: addr_id_sub
            enumPrefix: ADDR_ID_SUB_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
"""
    + render_leaf('subLeaf')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uSub:        { container: top, instanceType: sub }
    uSubDecode:  { container: sub, instanceType: paramSubDecode, variant: paramSubV0 }
    uSubLeaf:    { container: sub, instanceType: subLeaf, addressGroup: sub }

parameters:
    paramSubDecode:
        paramSubV0:
            PARAM_ROUTER_KNOB: 4
        paramSubV1:
            PARAM_ROUTER_KNOB: 8

registers:
    - { register: cfg, regType: rw, block: subLeaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("nested router that is itself parameterized")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # The router block declares params:, so isParameterizable must be
        # set even though paramSubDecode's upstream / downstream
        # interfaces are not themselves parameterized.
        _router_key, router_row = find_block(prj, 'paramSubDecode')
        assert bool(router_row.get('isParameterizable')), (
            "paramSubDecode must be flagged isParameterizable; "
            f"got {router_row.get('isParameterizable')!r}"
        )

        # The bound instance carries the chosen variant; the second
        # variant remains available in the parameter table for reuse.
        _inst_key, sub_decode_row = find_instance(prj, 'uSubDecode')
        assert sub_decode_row.get('variant') == 'paramSubV0', (
            f"uSubDecode must bind variant 'paramSubV0'; "
            f"got {sub_decode_row.get('variant')!r}"
        )

        # Parent-to-child router bind: primary dispatches to the nested
        # router's container sibling.
        parent_to_child = find_connections(prj, src='uAPBDecode', dst='uSub')
        assert len(parent_to_child) == 1, \
            f"expected 1 uAPBDecode->uSub bind, got {len(parent_to_child)}"

        # Boundary connectionMap maps the inherited apbReg port onto the
        # nested router instance.
        boundary = find_connection_maps(prj, instance='uSubDecode')
        assert any(cm.get('port') == 'apbReg' for cm in boundary), \
            f"missing uSubDecode boundary connectionMap; got {boundary}"

        # Router-to-leaf bind from the nested router only.
        sub_leaf_bind = find_connections(prj, src='uSubDecode', dst='uSubLeaf')
        assert len(sub_leaf_bind) == 1, \
            f"expected 1 uSubDecode->uSubLeaf bind, got {len(sub_leaf_bind)}"
        assert find_connections(prj, src='uAPBDecode', dst='uSubLeaf') == [], \
            "primary must not dispatch directly to the nested-router leaf"

        # Handler block / instance for the routed leaf.
        find_block(prj, 'subLeaf_regs')
        find_instance(prj, 'u_subLeaf_regs')

        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uSub', 'uSubLeaf'):
            key, _ = find_instance(prj, simple)
            assert key in instances_with_regapb, \
                f"INSTANCES_WITH_REGAPB missing '{key}'"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
