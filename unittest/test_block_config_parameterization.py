#!/usr/bin/env python3
"""Regression coverage for block config parameterization.

`calcBlockConfigInfo()` must honor parse-time register/memory row
`isParameterizable` flags. A row can be parameterizable even when its
payload/address structures are not, for example when `wordLines` is backed by
an ipParameters constant.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    find_block,
    iter_rows,
    projectOpen,
    render_leaf,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
ipParameters:
    constants:
        PARAM_WORD_LINES:
            value: 4
            maxValue: 8
            desc: "Memory-register depth parameter"

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    paramOwner:
        desc: "Consumes PARAM_WORD_LINES only to validate ipParameters linkage"
        hasMdl: true
        params: [PARAM_WORD_LINES]
"""
    + render_router('apbDecode', 'top')
    + render_leaf('wordLineLeaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: wordLineLeaf, addressGroup: top }

registers:
    - { register: wordMemReg, regType: memory, block: wordLineLeaf, structure: cfgRegSt, addressStruct: apbAddrSt, wordLines: PARAM_WORD_LINES, desc: "Memory register with parameterized depth" }

memories:
    - { memory: wordMem, block: wordLineLeaf, structure: cfgRegSt, addressStruct: apbAddrSt, wordLines: PARAM_WORD_LINES, regAccess: true, desc: "Memory with parameterized depth" }
"""
)

CONNECTION_ARCH_YAML = """constants:
    ADDR_WIDTH: { value: 32, desc: "Unused address width" }

ipParameters:
    constants:
        PARAM_BUS_WIDTH:
            value: 16
            maxValue: 32
            desc: "Parameterized payload width"
    types:
        paramBusT:
            width: PARAM_BUS_WIDTH
            maxBitwidth: 32
            desc: "Parameterized payload type"

structures:
    paramBusSt:
        data: { varType: paramBusT, desc: "Payload" }

interfaces:
    paramBus:
        desc: "Parameterized point-to-point bus"
        interfaceType: rdy_vld
        structures:
            - { structure: paramBusSt, structureType: data_t }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    paramOwner:
        desc: "Consumes PARAM_BUS_WIDTH only to validate ipParameters linkage"
        hasMdl: true
        params: [PARAM_BUS_WIDTH]
    srcBlock:
        desc: "Source block"
        hasMdl: true
        params: [PARAM_BUS_WIDTH]
        ports:
            out: { interface: paramBus, direction: src }
    dstBlock:
        desc: "Destination block"
        hasMdl: true
        params: [PARAM_BUS_WIDTH]
        ports:
            in: { interface: paramBus, direction: dst }

instances:
    uTop: { container: top, instanceType: top }
    uSrc: { container: top, instanceType: srcBlock }
    uDst: { container: top, instanceType: dstBlock }

connections:
    - { interface: paramBus, src: uSrc, srcport: out, dst: uDst, dstport: in }
"""


def _find_register(prj, simple_name):
    for _key, row in iter_rows(prj, 'registers'):
        if row.get('register') == simple_name:
            return row
    raise AssertionError(f"No register named '{simple_name}' found")


def _find_memory(prj, simple_name):
    for _key, row in iter_rows(prj, 'memories'):
        if row.get('memory') == simple_name:
            return row
    raise AssertionError(f"No memory named '{simple_name}' found")


def _find_row(prj, section, field, value):
    for _key, row in iter_rows(prj, section):
        if row.get(field) == value:
            return row
    raise AssertionError(f"No {section} row with {field}='{value}' found")


def _run_wordlines_register():
    print("Block config: wordLines-only register parameterizes block")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        reg_row = _find_register(prj, 'wordMemReg')
        assert bool(reg_row.get('isParameterizable')), (
            "wordMemReg must be parameterizable because wordLines references "
            "PARAM_WORD_LINES"
        )

        mem_row = _find_memory(prj, 'wordMem')
        assert bool(mem_row.get('isParameterizable')), (
            "wordMem must be parameterizable because wordLines references "
            "PARAM_WORD_LINES"
        )

        _leaf_key, leaf_row = find_block(prj, 'wordLineLeaf')
        assert not leaf_row.get('params'), (
            "wordLineLeaf should not rely on the block params special case"
        )
        assert bool(leaf_row.get('isParameterizable')), (
            "wordLineLeaf must inherit parameterization from wordMemReg"
        )

        print("PASS: wordLines-only register parameterizes block")
        return True
    finally:
        cleanup(paths)


def _run_parameterized_connection():
    print("Block config: parameterized interface connection carries row flags")
    db_path, project_path, arch_paths = build_database(CONNECTION_ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        intf_row = _find_row(prj, 'interfaces', 'interface', 'paramBus')
        assert bool(intf_row.get('isParameterizable')), (
            "paramBus interface must inherit parameterization from paramBusSt"
        )

        conn_row = _find_row(prj, 'connections', 'interface', 'paramBus')
        assert bool(conn_row.get('isParameterizable')), (
            "paramBus connection must inherit parameterization from its interface"
        )

        _top_key, top_row = find_block(prj, 'top')
        assert bool(top_row.get('isParameterizable')), (
            "top must be parameterizable because it contains a parameterized "
            "connection"
        )

        print("PASS: parameterized interface connection carries row flags")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if (_run_wordlines_register()
                 and _run_parameterized_connection()) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
