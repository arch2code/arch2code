#!/usr/bin/env python3
"""A register-bus interface may not carry a parameterizable structure, even
when it is a reusable-IP leaf's own `registerPorts:` interface.

The leaf declares `ipParameters:` with a parameter that drives the
register-bus data type, and the leaf's `registerPorts:` interface binds a
structure that references that parameterized type. Registers and memories
may be parameterizable; the bus itself may not, so `make db` must reject
this shape naming the interface, its interfaceType, the parameterizable
structure, and the file.

Topology::

    uTop (top)
    +-- uAPBDecode ........... primary router (upstream=apbReg)
    +-- uLeaf0 (paramLeaf, variant=paramVar0, PARAM_REG_DATA_WIDTH=32)
    +-- uLeaf1 (paramLeaf, variant=paramVar1, PARAM_REG_DATA_WIDTH=32)

    paramLeaf block:
        params:        [PARAM_REG_DATA_WIDTH]
        registerPorts: regs -> paramReg interface
                                +-- addr_t = apbAddrSt
                                +-- data_t = paramRegDataSt (parameterized)
"""

import sys

from _addrctl_helpers import (
    build_database,
    cleanup,
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
        paramVar0:
            PARAM_REG_DATA_WIDTH: 32
        paramVar1:
            PARAM_REG_DATA_WIDTH: 32

registers:
    - { register: cfg, regType: rw, block: paramLeaf, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "paramReg",
    "apb",
    "address-bus",
    "paramRegDataSt",
    "fixed-width",
]


def _run():
    print("leaf's parameterizable registerPorts: interface is rejected")
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
