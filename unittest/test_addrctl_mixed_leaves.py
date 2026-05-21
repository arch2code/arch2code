#!/usr/bin/env python3
"""T1.5: One router, mixed leaves — one routed leaf and one plain leaf.

Asserts that the plain leaf receives no synthesised router-to-leaf
dispatch connection, while the routed leaf does. This pins
`postParseRegisterPorts.py`'s `registerPorts:` gate on connection
emission.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_block,
    find_connections,
    find_instance,
    projectOpen,
    render_leaf,
    render_plain_block,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + render_plain_block('plain')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top }
    uPlain:     { container: top, instanceType: plain }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("T1.5: single router, one routed leaf plus one plain leaf")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Routed leaf receives a dispatch bind.
        routed = find_connections(prj, src='uAPBDecode', dst='uLeaf')
        assert len(routed) == 1, \
            f"expected 1 uAPBDecode->uLeaf bind, got {len(routed)}"

        # Plain leaf receives none.
        plain = find_connections(prj, src='uAPBDecode', dst='uPlain')
        assert len(plain) == 0, \
            f"plain leaf must not receive a dispatch bind, got {plain}"

        # No handler block for the plain leaf.
        try:
            find_block(prj, 'plain_regs')
            raise AssertionError(
                "plain block must not produce a synthesised handler block"
            )
        except AssertionError as exc:
            if str(exc).startswith("No block with simple name"):
                pass
            else:
                raise

        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        plain_inst, _ = find_instance(prj, 'uPlain')
        assert plain_inst not in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB must not list plain leaf '{plain_inst}'"

        assert_no_global_register_binds(prj)
        print("PASS: T1.5")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
