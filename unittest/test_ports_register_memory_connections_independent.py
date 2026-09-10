#!/usr/bin/env python3
"""Register- and memory-connection-implied ports are independent of `ports:`.

A block may declare a complete `ports:` map for its own interface ports
and also be the target of a plain `registerConnections:` row (a register
owned by its container, forwarded down as a point-to-point status
channel, the shape `yaml/debayer.yaml`'s `bayer_pattern` uses) and a
plain `memoryConnections:` row. Neither kind of row has an interface a
`ports:` entry can name, so the partial-`ports:` completeness check in
`processYaml.py::validateDeclaredPorts` must not treat them as missing
`ports:` entries. This pins the `sourceType in ('registers', 'memories')`
exemption in the completeness loop.

`container` owns the register and the memory, the way `debayer` owns
`bayer_pattern`; `sink`, a sibling instance, is the connection target
and the block under test. Address bookkeeping needs an address group to
exist in the project even for this unrouted register, so the fixture
carries the same minimal APB router/leaf pair the sibling
`test_register_ports_independent_of_ports.py` uses, unconnected to
`cfg` or `tbl`.

A second build proves the skip is scoped correctly: dropping the real
interface port from `sink`'s `ports:` map must still be rejected, so
the register/memory skip does not swallow a genuinely missing port.
"""

import sys

from _addrctl_helpers import (
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


# Self-contained preamble: the APB register bus (addressBus: true, needed
# only so the project has an address group at all) plus a plain rdy_vld
# data bus for the connection under test, and the register/memory payload
# structures `container` owns.
PREAMBLE = """constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Register bus data width" }
    REG_WIDTH:  { value: 16, desc: "Register payload width" }
    WIDTH:      { value: 8,  desc: "Pixel sample width" }
    TBL_WIDTH:  { value: 8,  desc: "Table data width" }
    TBL_ADDR_WIDTH: { value: 4, desc: "Table address width" }

types:
    apbAddrT: { width: ADDR_WIDTH,     desc: "APB address" }
    apbDataT: { width: DATA_WIDTH,     desc: "APB data" }
    cfgT:     { width: REG_WIDTH,      desc: "Register payload" }
    pixT:     { width: WIDTH,          desc: "Pixel sample" }
    tblAddrT: { width: TBL_ADDR_WIDTH, desc: "Table address" }
    tblDataT: { width: TBL_WIDTH,      desc: "Table data" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }
    pixSt:
        pixel: { varType: pixT, generator: data }
    tblAddrSt:
        address: { varType: tblAddrT, generator: address }
    tblDataSt:
        data: { varType: tblDataT, generator: data }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    pixIf:
        desc: "Plain pixel data bus (not a register bus)"
        interfaceType: rdy_vld
        structures:
            - { structure: pixSt, structureType: data_t }
"""


ARCH_YAML_TEMPLATE = (
    PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    producer:
        desc: "Plain data producer"
        hasMdl: true
        ports:
            pixOut: { interface: pixIf, direction: src }
    consumer:
        desc: "Plain data consumer, downstream of sink"
        hasMdl: true
        ports:
            pixIn: { interface: pixIf, direction: dst }
    container:
        desc: "Owns the register and memory forwarded to sink, like debayer owning bayer_pattern"
        hasMdl: true
    sink:
        desc: "Block under test: complete ports:, also a register- and memory-connection target"
        hasMdl: true
__SINK_PORTS__
"""
    + render_router('apbDecode', 'top')
    + render_leaf('regLeaf')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uRegLeaf:    { container: top, instanceType: regLeaf, addressGroup: top }
    uProducer:   { container: top, instanceType: producer }
    uConsumer:   { container: top, instanceType: consumer }
    uContainer:  { container: top, instanceType: container, addressGroup: top }
    uSink:       { container: top, instanceType: sink }

connections:
    - { interface: pixIf, src: uProducer, srcport: pixOut, dst: uSink, dstport: pixIn }
    - { interface: pixIf, src: uSink, srcport: pixFwd, dst: uConsumer, dstport: pixIn }

registers:
    - { register: cfg, regType: rw, block: container, structure: cfgRegSt, desc: "Config register owned by the container" }

registerConnections:
    - { register: cfg, block: container, instance: uSink }

memories:
    - { memory: tbl, block: container, structure: tblDataSt, addressStruct: tblAddrSt, wordLines: 4, ports: [tblPort], desc: "Table owned by the container" }

memoryConnections:
    - { memory: tbl, block: container, instance: uSink, port: tblPort }
"""
)


COMPLETE_SINK_PORTS = (
    "        ports:\n"
    "            pixIn:  { interface: pixIf, direction: dst }\n"
    "            pixFwd: { interface: pixIf, direction: src }\n"
)

# Omits the genuine interface port 'pixFwd', keeping only 'pixIn' declared.
PARTIAL_SINK_PORTS = (
    "        ports:\n"
    "            pixIn:  { interface: pixIf, direction: dst }\n"
)


def _run_positive():
    print("register/memory connections are independent of a complete ports: map")
    arch_yaml = ARCH_YAML_TEMPLATE.replace('__SINK_PORTS__', COMPLETE_SINK_PORTS)
    # build_database raises if arch2code.py exits non-zero, so a fired
    # partial-ports: diagnostic is itself the failure signal.
    db_path, project_path, arch_paths = build_database(arch_yaml)
    cleanup([project_path, db_path] + arch_paths)
    print("PASS")
    return True


def _run_negative():
    print("a genuinely missing interface port is still rejected")
    arch_yaml = ARCH_YAML_TEMPLATE.replace('__SINK_PORTS__', PARTIAL_SINK_PORTS)
    db_path, project_path, arch_paths, result = build_database(
        arch_yaml, expect_success=False)
    cleanup([project_path, db_path] + arch_paths)
    output = result.stdout + result.stderr
    assert "partial ports" in output.lower(), \
        f"expected a partial ports: diagnostic, got:\n{output}"
    assert "omits port 'pixfwd'" in output.lower(), \
        f"expected the diagnostic to name 'pixFwd', got:\n{output}"
    print("PASS")
    return True


def run_all_tests():
    passed = 0
    total = 2
    try:
        if _run_positive():
            passed += 1
    except Exception as e:
        print(f"FAIL: {e}")
    try:
        if _run_negative():
            passed += 1
    except Exception as e:
        print(f"FAIL: {e}")
    print(f"\n  Passed: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
