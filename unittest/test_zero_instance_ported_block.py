#!/usr/bin/env python3
"""Zero-instance exported-leaf boundary-port render view.

A `hasMdl` block that declares explicit `ports:` but is never instantiated
in its owning project (an exported / library leaf a definitions-only project
publishes for other projects to instantiate) must still render its boundary
ports. projectOpen's `getBlockData` view synthesises those ports from the
block definition (`getBDDefinitionPorts`) so the emitted module is NOT
portless. This test opens such a block's view and asserts the declared
connection port is present, typed, and directed exactly as an instance-driven
port would be.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    find_block,
    projectOpen,
)


# `cpu` declares one connection port (`cpu_main`, apbReg src) but is never
# instantiated. `top` is the only instantiated block (the project's root).
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (only instantiated block)"
        hasMdl: true
    cpu:
        desc: "Exported APB master leaf: declared ports:, never instantiated"
        hasMdl: true
        ports:
            cpu_main: { interface: apbReg, direction: src }

instances:
    uTop: { container: top, instanceType: top }
"""
)


def _run():
    print("zero-instance exported leaf renders its declared boundary port")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        cpu_key, _ = find_block(prj, 'cpu')
        data = prj.getBlockData(cpu_key)

        assert data['instances'] == {}, \
            f"expected zero instances of cpu, got {data['instances']!r}"

        conn_ports = data['ports']['connections']
        assert 'cpu_main' in conn_ports, \
            f"declared port 'cpu_main' missing from rendered ports; got {list(conn_ports)}"
        print("PASS: uninstantiated block renders its declared port")

        port = conn_ports['cpu_main']
        assert port['direction'] == 'src', \
            f"cpu_main direction expected 'src', got {port['direction']!r}"
        assert port['name'] == 'cpu_main', \
            f"cpu_main name expected 'cpu_main', got {port['name']!r}"
        print("PASS: port name and direction match declaration")

        interface_key = port['connection']['interfaceKey']
        interface_type = prj.data['interfaces'][interface_key]['interfaceType']
        assert interface_type == 'apb', \
            f"cpu_main interfaceType expected 'apb', got {interface_type!r}"
        assert data['interfaceTypes'].get('apb') is not None, \
            "apb interface type not registered on the view (structs would be unresolved)"
        print("PASS: port interface resolves to apb with structs registered")

        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
