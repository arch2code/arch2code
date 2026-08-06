#!/usr/bin/env python3
"""`registerPorts:` is independent of `ports:`.

A routed leaf may declare a `ports:` map for its non-register interfaces
*and* a `registerPorts:` map for its register-bus ingress. The
partial-`ports:` completeness check in
`processYaml.py::validateDeclaredPorts` must not treat the
register-bus dispatch port (inferred from the synthesised router-to-leaf
bind) as a missing `ports:` entry. The leaf must build without a
"partial ports: declaration ... omits port 'regs'" diagnostic, even
though 'regs' is never named in the `ports:` map.

This pins the `registerPortNames` skip
(`processYaml.py::validateDeclaredPorts`, the
`if portName in registerPortNames: continue` branch). Removing that
skip turns this positive build into a failure, so the test guards the
independence contract rather than restating it.

The leaf deliberately owns **no** registers or memories, so no
`<block>_regs` handler and no leaf-to-handler `connectionMap` are
synthesised. The register-bus port 'regs' therefore reaches the
partial-`ports:` check only through the router-to-leaf connection, and
only the `registerPortNames` skip can clear it — the sibling
`connectionMapPortNames` skip is not in play. This isolates the
contract under test.
"""

import sys

from _addrctl_helpers import (
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_block,
    find_connections,
    projectOpen,
    render_leaf,
    render_router,
)


# Self-contained preamble: the APB register bus (addressBus: true) plus
# a plain rdy_vld data bus used only to give the leaf a non-empty
# `ports:` map. The partial-`ports:` check only engages once a block
# declares at least one `ports:` entry, so the data port is required to
# reach the skip under test.
PREAMBLE = """constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Register bus data width" }
    REG_WIDTH:  { value: 16, desc: "Register payload width" }

types:
    apbAddrT: { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT: { width: DATA_WIDTH, desc: "APB data" }
    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }
    pixT:     { width: DATA_WIDTH, desc: "Pixel sample" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }
    pixSt:
        pixel: { varType: pixT, generator: data }

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


# The routed leaf declares both surfaces: a data-in `ports:` entry and a
# register-bus `registerPorts:` entry. 'regs' is deliberately absent
# from `ports:`.
LEAF_PORTS = (
    "        ports:\n"
    "            pixIn: { interface: pixIf, direction: dst }\n"
)


ARCH_YAML = (
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
"""
    + render_router('apbDecode', 'top')
    + render_leaf('sink', extra_block_lines=LEAF_PORTS)
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uProducer:  { container: top, instanceType: producer }
    uSink:      { container: top, instanceType: sink, addressGroup: top }

connections:
    - { interface: pixIf, src: uProducer, srcport: pixOut, dst: uSink, dstport: pixIn }
"""
)


def _run():
    print("registerPorts: is independent of a partial ports: map")
    # build_database raises if arch2code.py exits non-zero, so a fired
    # partial-ports: diagnostic is itself the failure signal.
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # The leaf's authored ports: map carries only the data port; the
        # register-bus port is owned by registerPorts:, not ports:.
        _sink_key, sink_row = find_block(prj, 'sink')
        declared_ports = set((sink_row.get('ports') or {}).keys())
        assert declared_ports == {'pixIn'}, \
            f"sink ports: expected just data port 'pixIn', got {declared_ports}"
        register_ports = set((sink_row.get('registerPorts') or {}).keys())
        assert register_ports == {'regs'}, \
            f"sink registerPorts: expected 'regs', got {register_ports}"

        # The router-to-leaf register dispatch bind exists and targets the
        # registerPorts: name, so 'regs' was inferred for the leaf yet did
        # not trip the partial-ports: completeness check.
        reg_conns = find_connections(prj, src='uAPBDecode', dst='uSink')
        assert len(reg_conns) == 1, \
            f"expected one uAPBDecode->uSink register bind, got {len(reg_conns)}"
        assert reg_conns[0].get('dstport') == 'regs', \
            f"register bind dstport expected 'regs', got {reg_conns[0].get('dstport')}"
        assert reg_conns[0].get('interface') == 'apbReg', \
            f"register bind interface expected 'apbReg', got {reg_conns[0].get('interface')}"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
