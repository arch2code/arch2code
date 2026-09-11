#!/usr/bin/env python3
"""Nested router that takes its parameters from its container instead of
declaring its own variant.

Topology (shared across all three cells)::

    uTop (top)
    +-- uAPBDecode ............ primary router (upstream=apbReg)
    +-- uMid (mid)
        +-- uParamRouter (paramMidRouter) ... nested router
        |     params:           [PARAM_UPSTREAM_WIDTH]
        |     upstreamPort:     paramApb       (parameterizable data;
        |                                       paramUpstreamDataSt)
        |     registerDecoder:  apbReg
        +-- uMidLeaf (midLeaf, addressGroup=mid)

The parent-router-to-nested-router junction check (`postParseRegisterPorts.py`)
resolves the nested router's own value through its container's sibling
instance (`uMid`), not through an empty configuration, so a router that
inherits or takes a `containerParam:` binding is a supported shape:

  (a) `uParamRouter` sets `inheritContainerParam: true` and takes `uMid`'s
      `PARAM_UPSTREAM_WIDTH`, matching `uAPBDecode`'s. Build succeeds.
  (b) Same shape, but `uMid` is configured narrower than `uAPBDecode`. Build
      fails, naming the parent-to-nested-router dispatch and the container
      site (`uMid`) whose configuration governed the mismatch.
  (c) `uParamRouter` declares a variant whose `PARAM_UPSTREAM_WIDTH` binding
      is `{ containerParam: PARAM_UPSTREAM_WIDTH }`, taking `uMid`'s value
      the same way as (a). Build succeeds.
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


BLOCKS_YAML = """
blocks:
    top:
        desc: "Primary container"
        hasMdl: true
    mid:
        desc: "Nested router's container"
        hasMdl: true
        params: [PARAM_UPSTREAM_WIDTH]
    apbDecode:
        desc: "Primary router"
        hasMdl: true
        params: [PARAM_UPSTREAM_WIDTH]
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


def _arch_yaml(router_instance_line, router_parameters, apb_width,
               mid_width, leaf_width):
    return (
        PARAM_PREAMBLE
        + BLOCKS_YAML
        + render_leaf('midLeaf',
                      extra_block_lines='        params: [PARAM_UPSTREAM_WIDTH]\n')
        + f"""
instances:
    uTop:          {{ container: top, instanceType: top }}
    uAPBDecode:    {{ container: top, instanceType: apbDecode, variant: apbV0 }}
    uMid:          {{ container: top, instanceType: mid, variant: midV0 }}
    {router_instance_line}
    uMidLeaf:      {{ container: mid, instanceType: midLeaf, addressGroup: mid, variant: midLeafV0 }}

parameters:
{router_parameters}
    apbDecode:
        apbV0:
            PARAM_UPSTREAM_WIDTH: {apb_width}
    mid:
        midV0:
            PARAM_UPSTREAM_WIDTH: {mid_width}
    midLeaf:
        midLeafV0:
            PARAM_UPSTREAM_WIDTH: {leaf_width}

registers:
    - {{ register: cfg, regType: rw, block: midLeaf, structure: cfgRegSt, desc: "" }}
"""
    )


def _assert_common_binds(prj):
    """Parent-to-child bind and boundary connectionMap shared by every
    passing cell."""
    parent_to_child = find_connections(prj, src='uAPBDecode', dst='uMid')
    assert len(parent_to_child) == 1, (
        f"expected 1 uAPBDecode->uMid bind, got {len(parent_to_child)}"
    )
    assert parent_to_child[0]['interface'] == 'paramApb', (
        f"parent-to-child bind must name the child router's upstream "
        f"interface; got '{parent_to_child[0]['interface']}'"
    )

    boundary = find_connection_maps(prj, instance='uParamRouter')
    assert any(cm.get('port') == 'paramApb' for cm in boundary), (
        f"nested-router upstream connectionMap must declare port "
        f"'paramApb'; got {boundary}"
    )

    leaf_bind = find_connections(prj, src='uParamRouter', dst='uMidLeaf')
    assert len(leaf_bind) == 1, (
        f"expected 1 uParamRouter->uMidLeaf bind, got {len(leaf_bind)}"
    )

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


def _run_inherit_matching():
    print("nested router inherits its container's parameters, matching")
    arch_yaml = _arch_yaml(
        'uParamRouter:  { container: mid, instanceType: paramMidRouter, '
        'inheritContainerParam: true }',
        '', 32, 32, 32)
    db_path, project_path, arch_paths = build_database(arch_yaml)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        _router_key, router_row = find_block(prj, 'paramMidRouter')
        assert router_row['isParameterizable'], (
            "paramMidRouter must be flagged isParameterizable; "
            f"got {router_row.get('isParameterizable')!r}"
        )
        _assert_common_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def _run_inherit_mismatching():
    print("nested router inherits its container's parameters, mismatching")
    arch_yaml = _arch_yaml(
        'uParamRouter:  { container: mid, instanceType: paramMidRouter, '
        'inheritContainerParam: true }',
        '', 32, 16, 16)
    _db_path, project_path, arch_paths, result = build_database(
        arch_yaml, expect_success=False)
    paths = [project_path, _db_path] + arch_paths
    try:
        combined = result.stdout + result.stderr
        for needle in ("Register-bus dispatch from parent router",
                       "'uAPBDecode'", "'uParamRouter'",
                       "its container's configuration",
                       "block 'mid'", "variant 'midV0'"):
            assert needle in combined, (
                f"rejection message missing '{needle}'\n{combined}"
            )
        print("PASS")
        return True
    finally:
        cleanup(paths)


def _run_container_param_matching():
    print("nested router takes a containerParam: binding, matching")
    router_parameters = """    paramMidRouter:
        paramMidV0:
            PARAM_UPSTREAM_WIDTH: { containerParam: PARAM_UPSTREAM_WIDTH }
"""
    arch_yaml = _arch_yaml(
        'uParamRouter:  { container: mid, instanceType: paramMidRouter, '
        'variant: paramMidV0 }',
        router_parameters, 32, 32, 32)
    db_path, project_path, arch_paths = build_database(arch_yaml)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        _router_key, router_row = find_block(prj, 'paramMidRouter')
        assert router_row['isParameterizable'], (
            "paramMidRouter must be flagged isParameterizable; "
            f"got {router_row.get('isParameterizable')!r}"
        )
        _assert_common_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def _run():
    results = [
        _run_inherit_matching(),
        _run_inherit_mismatching(),
        _run_container_param_matching(),
    ]
    return all(results)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
