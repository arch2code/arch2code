#!/usr/bin/env python3
"""T5.1: Router declared but no leaves under it.

A router with `addressBlock:` declared but no routed leaves (and no
register-bearing leaves) is legal: the pass synthesises no handler
blocks or instances and emits no router-to-leaf binds.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_connections,
    projectOpen,
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
    + render_plain_block('inert')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uInert:      { container: top, instanceType: inert }
"""
)


def _run():
    print("T5.1: router with no leaves to dispatch to")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # No router-to-leaf binds were emitted.
        outbound = find_connections(prj, src='uAPBDecode')
        assert outbound == [], \
            f"expected no router-to-leaf binds, got {outbound}"

        # No handler block / instance was synthesised. Iterate every
        # block looking for the _regs suffix the helper would emit.
        offenders = [
            row.get('block') for row in prj.data['blocks'].values()
            if isinstance(row, dict) and row.get('block', '').endswith('_regs')
        ]
        assert offenders == [], \
            f"router with no leaves must not produce _regs handler blocks; got {offenders}"

        # INSTANCES_WITH_REGAPB exists but is empty.
        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        assert instances_with_regapb == [], \
            f"INSTANCES_WITH_REGAPB expected empty list, got {instances_with_regapb}"

        assert_no_global_register_binds(prj)
        print("PASS: T5.1")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
