#!/usr/bin/env python3
"""A register-bus interface may not carry a parameterizable structure, even
on the primary router's own upstreamPort (the bus a real master feeds).

`paramApb` is `paramTopDecode`'s `addressBlock.upstreamPort` interface,
declared parameterizable through `paramParentDataSt` (backed by
`PARAM_PARENT_WIDTH`). Registers and memories may be parameterizable; the
bus itself may not, so `make db` must reject this shape naming the
interface, its interfaceType, the parameterizable structure, and the file.
"""

import sys

from _addrctl_helpers import (
    build_database,
    cleanup,
    render_leaf,
)


PARAM_PARENT_PREAMBLE = """constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Leaf-side register bus data width" }
    PARAM_PARENT_WIDTH:
        value: 16
        maxValue: 32
        desc: "Router upstream data width overridden by variant"
    REG_WIDTH:  { value: 16, desc: "Register payload width" }

types:
    apbAddrT: { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT: { width: DATA_WIDTH, desc: "APB data" }
    paramParentDataT:
        width: PARAM_PARENT_WIDTH
        maxBitwidth: 32
        desc: "Parameterized parent router data word"
    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    paramParentDataSt:
        data: { varType: paramParentDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }

interfaces:
    apbReg:
        desc: "Leaf-side APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    paramApb:
        desc: "Parent router APB register bus with variant-sized data"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: paramParentDataSt, structureType: data_t }
"""


ARCH_YAML = (
    PARAM_PARENT_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    paramTopDecode:
        desc: "Parameterized primary router"
        hasMdl: true
        params: [PARAM_PARENT_WIDTH]
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: paramApb
            registerDecoderPort: apbReg
"""
    + render_leaf('leaf',
                  extra_block_lines='        params: [PARAM_PARENT_WIDTH]\n')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: paramTopDecode, variant: topV0 }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top, variant: leafV0 }

parameters:
    paramTopDecode:
        topV0:
            PARAM_PARENT_WIDTH: 32
    leaf:
        leafV0:
            PARAM_PARENT_WIDTH: 32

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "paramApb",
    "apb",
    "address-bus",
    "paramParentDataSt",
    "fixed-width",
]


def _run():
    print("parent router's parameterizable upstream interface is rejected")
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
