#!/usr/bin/env python3
"""T1.2: One router, one routed leaf with multiple registers and one memory."""

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
)


ARCH_YAML = """
constants:
    APB_ADDR_WIDTH:    { value: 32, desc: "APB address width" }
    APB_DATA_WIDTH:    { value: 32, desc: "APB data width" }
    MULTI_CFG_WIDTH:   { value: 16, desc: "Configuration register payload width" }
    MULTI_STAT_WIDTH:  { value: 24, desc: "Status register payload width" }
    MULTI_MEM_WORDS:   { value: 16, desc: "Reg-access memory wordlines" }
    MULTI_MEM_WIDTH:   { value: 32, desc: "Reg-access memory data width" }
    MULTI_MEM_AWIDTH:  { eval: "($MULTI_MEM_WORDS-1).bit_length()", desc: "Reg-access memory address width" }

types:
    apbAddrT:       { width: APB_ADDR_WIDTH, desc: "APB address" }
    apbDataT:       { width: APB_DATA_WIDTH, desc: "APB data" }
    multiCfgT:      { width: MULTI_CFG_WIDTH, desc: "Configuration payload" }
    multiStatT:     { width: MULTI_STAT_WIDTH, desc: "Status payload" }
    multiMemDataT:  { width: MULTI_MEM_WIDTH, desc: "Memory payload" }
    multiMemAddrT:  { width: MULTI_MEM_AWIDTH, desc: "Memory address" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    multiCfgSt:
        value: { varType: multiCfgT, generator: register, desc: "Configuration value" }
    multiStatSt:
        value: { varType: multiStatT, generator: register, desc: "Status value" }
    multiMemSt:
        data: { varType: multiMemDataT }
    multiMemAddrSt:
        address: { varType: multiMemAddrT }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    apbDecode:
        desc: "Primary APB decoder"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
    multi:
        desc: "Routed leaf with several registers and one memory"
        hasMdl: true
        registerPorts:
            regs: { interface: apbReg }

instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uMulti:     { container: top, instanceType: multi, addressGroup: top }

registers:
    - { register: multiCfg0,  regType: rw, block: multi, structure: multiCfgSt,  desc: "Config 0" }
    - { register: multiCfg1,  regType: rw, block: multi, structure: multiCfgSt,  desc: "Config 1" }
    - { register: multiStat,  regType: ro, block: multi, structure: multiStatSt, desc: "Status" }

memories:
    - { memory: multiMem, block: multi, structure: multiMemSt, addressStruct: multiMemAddrSt, wordLines: MULTI_MEM_WORDS, regAccess: true, desc: "Reg-access scratch memory" }
"""


def _run():
    print("T1.2: single router, one routed leaf with multiple registers and one memory")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        multi_key, _ = find_block(prj, 'multi')
        leaf_view = prj.getBlockData(multi_key)
        lad = leaf_view['addressDecode']
        assert bool(lad.get('hasDecoder')), \
            f"multi leaf should have a decoder, got {lad.get('hasDecoder')!r}"
        assert lad.get('registerBusPort') == 'regs', \
            f"multi registerBusPort expected 'regs', got {lad.get('registerBusPort')}"

        handler_block_key, handler_block_row = find_block(prj, 'multi_regs')
        assert bool(handler_block_row.get('isRegHandler')), \
            f"multi_regs expected isRegHandler truthy, got {handler_block_row.get('isRegHandler')!r}"

        handler_inst_key, handler_inst_row = find_instance(prj, 'u_multi_regs')
        assert handler_inst_row.get('instanceTypeKey') == handler_block_key, \
            f"u_multi_regs instanceTypeKey expected '{handler_block_key}', got '{handler_inst_row.get('instanceTypeKey')}'"
        assert handler_inst_row.get('containerKey') == multi_key, \
            f"u_multi_regs containerKey expected '{multi_key}', got '{handler_inst_row.get('containerKey')}'"

        conns = find_connections(prj, src='uAPBDecode', dst='uMulti')
        assert len(conns) == 1, \
            f"expected exactly one uAPBDecode->uMulti bind, got {len(conns)}"
        assert conns[0].get('dstport') == 'regs', \
            f"uMulti dstport expected 'regs', got {conns[0].get('dstport')}"

        maps = find_connection_maps(prj, instance='u_multi_regs')
        assert len(maps) == 1, \
            f"expected exactly one u_multi_regs connectionMap, got {len(maps)}"
        assert maps[0].get('port') == 'regs', \
            f"connectionMap port expected 'regs', got {maps[0].get('port')}"

        registers = [
            row.get('register') for row in prj.data['registers'].values()
            if isinstance(row, dict) and row.get('block') == 'multi'
        ]
        assert sorted(registers) == ['multiCfg0', 'multiCfg1', 'multiStat'], \
            f"unexpected multi register set: {registers}"

        memories = [
            row for row in prj.data['memories'].values()
            if isinstance(row, dict) and row.get('memory') == 'multiMem'
        ]
        assert len(memories) == 1, \
            f"expected one multiMem row, got {len(memories)}"
        assert memories[0].get('blockKey') == multi_key, \
            f"multiMem blockKey expected '{multi_key}', got '{memories[0].get('blockKey')}'"
        assert bool(memories[0].get('regAccess')), \
            f"multiMem expected regAccess truthy, got {memories[0].get('regAccess')!r}"

        handler_view = prj.getBlockData(handler_block_key)
        handler_memory_ports = handler_view.get('memoryPorts', {})
        assert 'multiMem_reg' in handler_memory_ports, (
            f"handler view memoryPorts expected to contain 'multiMem_reg'; "
            f"got {sorted(handler_memory_ports.keys())}"
        )

        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        multi_inst_key, _ = find_instance(prj, 'uMulti')
        assert multi_inst_key in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB missing '{multi_inst_key}'"

        assert_no_global_register_binds(prj)
        print("PASS: T1.2")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
