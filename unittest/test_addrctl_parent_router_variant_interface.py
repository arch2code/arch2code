#!/usr/bin/env python3
"""Parent router upstream interface uses the bound variant value."""

import sys

from _addrctl_helpers import (
    build_database,
    cleanup,
    find_connections,
    projectOpen,
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
        - { variant: topV0, param: PARAM_PARENT_WIDTH, value: 32 }
    leaf:
        - { variant: leafV0, param: PARAM_PARENT_WIDTH, value: 32 }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("parent router interface uses bound variant")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        binds = find_connections(prj, src='uAPBDecode', dst='uLeaf')
        assert len(binds) == 1, (
            f"expected one router-to-leaf bind, got {len(binds)}")
        assert binds[0]['interface'] == 'paramApb', (
            f"expected parent router interface paramApb, "
            f"got {binds[0]['interface']!r}")
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
