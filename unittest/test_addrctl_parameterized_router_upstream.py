#!/usr/bin/env python3
"""A register-bus interface may not carry a parameterizable structure, even
when it is only a nested router's private upstreamPort feed from its parent
router.

`paramApb` is the nested router's `addressBlock.upstreamPort` interface,
declared parameterizable through `paramUpstreamDataSt` (backed by
`PARAM_UPSTREAM_WIDTH`). Registers and memories may be parameterizable; the
bus itself may not, so `make db` must reject this shape naming the
interface, its interfaceType, the parameterizable structure, and the file.
This holds regardless of whether the router carries the parameter in its
own params:.
"""

import sys

from _addrctl_helpers import (
    build_database,
    cleanup,
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
    + render_leaf('midLeaf',
                  extra_block_lines='        params: [PARAM_UPSTREAM_WIDTH]\n')
    + """
instances:
    uTop:          { container: top, instanceType: top }
    uAPBDecode:    { container: top, instanceType: apbDecode, variant: apbV0 }
    uMid:          { container: top, instanceType: mid, variant: midV0 }
    uParamRouter:  { container: mid, instanceType: paramMidRouter, variant: paramMidV0 }
    uMidLeaf:      { container: mid, instanceType: midLeaf, addressGroup: mid, variant: midLeafV0 }

parameters:
    paramMidRouter:
        paramMidV0:
            PARAM_UPSTREAM_WIDTH: 32
    apbDecode:
        apbV0:
            PARAM_UPSTREAM_WIDTH: 32
    mid:
        midV0:
            PARAM_UPSTREAM_WIDTH: 32
    midLeaf:
        midLeafV0:
            PARAM_UPSTREAM_WIDTH: 32

registers:
    - { register: cfg, regType: rw, block: midLeaf, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "paramApb",
    "apb",
    "address-bus",
    "paramUpstreamDataSt",
    "fixed-width",
]


def _run():
    print("nested router's parameterizable upstream interface is rejected")
    db_path, project_path, arch_paths, result = build_database(
        ARCH_YAML, expect_success=False)
    paths = [project_path, db_path] + arch_paths
    try:
        combined = result.stdout + result.stderr
        if 'Traceback (most recent call last)' in combined:
            print("FAIL: got a Python stack trace instead of a clean error")
            print(combined)
            return False
        missing = [p for p in REQUIRED_SUBSTRINGS if p.lower() not in combined.lower()]
        if missing:
            print(f"FAIL: diagnostic missing substrings: {missing}")
            print(combined)
            return False
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
