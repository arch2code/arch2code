#!/usr/bin/env python3
"""projectOpen.getSocketCatalogView drive/observe/listen-name contract.

Two fixtures:
  pySocket-like — req_ack both directions plus push_ack; all drive; no `_obs`.
  py_test-like  — APB src, AXI read/write dst, status dst; irq is observe;
                  APB/AXI/status have `_obs` listen names; status drive name
                  is not in listenNames.
"""

from _addrctl_helpers import (
    build_database,
    cleanup,
    find_block,
    projectOpen,
)


PYSOCKET_LIKE_YAML = """
types:
    word32_t: { width: 32, desc: "word" }

structures:
    msgSt:
        param1: { varType: word32_t }
    respSt:
        response: { varType: word32_t }

interfaces:
    test_req_ack:
        interfaceType: req_ack
        desc: "Python-initiated req_ack"
        structures:
            - { structure: msgSt, structureType: data_t }
            - { structure: respSt, structureType: rdata_t }
    dut2Python_req_ack:
        interfaceType: req_ack
        desc: "DUT-initiated req_ack"
        structures:
            - { structure: msgSt, structureType: data_t }
            - { structure: respSt, structureType: rdata_t }
    test_push_ack:
        interfaceType: push_ack
        desc: "Python-initiated push"
        structures:
            - { structure: msgSt, structureType: data_t }

blocks:
    top:
        desc: "Root container"
        hasMdl: true
    stim:
        desc: "Socket shell block"
        hasMdl: true
    dut:
        desc: "DUT"
        hasMdl: true

instances:
    uTop: { container: top, instanceType: top }
    u_stim: { container: top, instanceType: stim }
    u_dut: { container: top, instanceType: dut }

connections:
    - { interface: test_req_ack, src: u_stim, dst: u_dut }
    - { interface: dut2Python_req_ack, src: u_dut, dst: u_stim }
    - { interface: test_push_ack, src: u_stim, dst: u_dut }
"""


PY_TEST_LIKE_YAML = """
constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Register bus data width" }
    REG_WIDTH:  { value: 16, desc: "Register payload width" }
    AXI_ADDRESS_WIDTH: { value: 32, desc: "AXI address width" }
    AXI_DATA_WIDTH: { value: 32, desc: "AXI data width" }
    AXI_STROBE_WIDTH: { value: 4, desc: "AXI strobe width" }

types:
    apbAddrT: { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT: { width: DATA_WIDTH, desc: "APB data" }
    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }
    axiAddrT: { width: AXI_ADDRESS_WIDTH, desc: "AXI address" }
    axiDataT: { width: AXI_DATA_WIDTH, desc: "AXI data" }
    axiStrobeT: { width: AXI_STROBE_WIDTH, desc: "AXI strobe" }
    irqT: { width: 1, desc: "IRQ bit" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }
    axiAddrSt:
        addr: { varType: axiAddrT }
    axiDataSt:
        data: { varType: axiDataT }
    axiStrobeSt:
        strobe: { varType: axiStrobeT }
    irqSt:
        irq: { varType: irqT }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    dma_axi_read_if:
        desc: "AXI read"
        interfaceType: axi_read
        multiCycleMode: api_list_size
        maxTransferSize: 256
        structures:
            - { structure: axiAddrSt, structureType: addr_t }
            - { structure: axiDataSt, structureType: data_t }
    dma_axi_write_if:
        desc: "AXI write"
        interfaceType: axi_write
        multiCycleMode: api_list_size
        maxTransferSize: 256
        structures:
            - { structure: axiAddrSt, structureType: addr_t }
            - { structure: axiDataSt, structureType: data_t }
            - { structure: axiStrobeSt, structureType: strb_t }
    dma_irq_if:
        desc: "IRQ / status observe"
        interfaceType: status
        structures:
            - { structure: irqSt, structureType: data_t }

blocks:
    top:
        desc: "Root container"
        hasMdl: true
    py_test:
        desc: "Socket shell block"
        hasMdl: true
    dut:
        desc: "DUT"
        hasMdl: true

instances:
    uTop: { container: top, instanceType: top }
    u_py_test: { container: top, instanceType: py_test }
    u_dut: { container: top, instanceType: dut }

connections:
    - { interface: apbReg, src: u_py_test, dst: u_dut }
    - { interface: dma_axi_read_if, src: u_dut, dst: u_py_test }
    - { interface: dma_axi_write_if, src: u_dut, dst: u_py_test }
    - { interface: dma_irq_if, src: u_dut, dst: u_py_test }
"""


def _by_port(view):
    return {row['port']: row for row in view['ports']}


def _run_pysocket_like():
    print("pySocket-like: req_ack both directions plus push_ack")
    db_path, project_path, arch_paths = build_database(PYSOCKET_LIKE_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        stim_key, _ = find_block(prj, 'stim')
        view = prj.getSocketCatalogView(stim_key)
        by_port = _by_port(view)

        assert set(by_port) >= {'test_req_ack', 'dut2Python_req_ack', 'test_push_ack'}, \
            f"missing expected ports: {sorted(by_port)}"

        for port in ('test_req_ack', 'dut2Python_req_ack', 'test_push_ack'):
            row = by_port[port]
            assert row['role'] == 'drive', f"{port} role expected drive, got {row['role']!r}"
            assert row['hasPortSocket'] is True, f"{port} should emit a port_socket thread"
            assert row['observeName'] is None, f"{port} must not have an observe name"
            assert row['name'] == f"stim.{port}", f"{port} name expected stim.{port}, got {row['name']!r}"

        assert by_port['test_req_ack']['direction'] == 'src'
        assert by_port['dut2Python_req_ack']['direction'] == 'dst'
        assert by_port['test_push_ack']['interfaceType'] == 'push_ack'

        assert all('_obs' not in name for name in view['listenNames']), \
            f"pySocket-like listenNames must not contain _obs: {view['listenNames']}"
        assert view['syncNames'] == [], \
            f"pySocket-like syncNames expected empty, got {view['syncNames']!r}"
        assert view['usesLockstep'] is False
        print("PASS: pySocket-like drive names, no _obs, no sync")
        return True
    finally:
        cleanup(paths)


def _run_py_test_like():
    print("py_test-like: APB src, AXI dst, status observe")
    db_path, project_path, arch_paths = build_database(PY_TEST_LIKE_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        py_test_key, _ = find_block(prj, 'py_test')
        view = prj.getSocketCatalogView(py_test_key)
        by_port = _by_port(view)

        apb = by_port['apbReg']
        assert apb['interfaceType'] == 'apb'
        assert apb['direction'] == 'src'
        assert apb['role'] == 'drive'
        assert apb['name'] == 'py_test.apbReg'
        assert apb['observeName'] == 'py_test.apbReg_obs'

        axi_rd = by_port['dma_axi_read_if']
        assert axi_rd['interfaceType'] == 'axi_read'
        assert axi_rd['direction'] == 'dst'
        assert axi_rd['role'] == 'drive'
        assert axi_rd['observeName'] == 'py_test.dma_axi_read_if_obs'

        axi_wr = by_port['dma_axi_write_if']
        assert axi_wr['interfaceType'] == 'axi_write'
        assert axi_wr['direction'] == 'dst'
        assert axi_wr['role'] == 'drive'
        assert axi_wr['observeName'] == 'py_test.dma_axi_write_if_obs'

        irq = by_port['dma_irq_if']
        assert irq['interfaceType'] == 'status'
        assert irq['direction'] == 'dst'
        assert irq['role'] == 'observe'
        assert irq['hasPortSocket'] is True
        assert irq['name'] == 'py_test.dma_irq_if'
        assert irq['observeName'] == 'py_test.dma_irq_if_obs'

        listen = view['listenNames']
        assert 'py_test.apbReg' in listen
        assert 'py_test.apbReg_obs' in listen
        assert 'py_test.dma_axi_read_if_obs' in listen
        assert 'py_test.dma_axi_write_if_obs' in listen
        assert 'py_test.dma_irq_if_obs' in listen
        assert 'py_test.dma_irq_if' not in listen, \
            "status drive name must not be a listen name"
        assert view['usesLockstep'] is True
        assert view['syncNames'] == ['pysocket_sync']
        print("PASS: py_test-like irq observe + APB/AXI _obs; status drive not listened")
        return True
    finally:
        cleanup(paths)


def _run():
    ok = _run_pysocket_like()
    ok = _run_py_test_like() and ok
    return ok


if __name__ == '__main__':
    raise SystemExit(0 if _run() else 1)
