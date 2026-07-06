#!/usr/bin/env python3
"""Leaf declares registerPorts: but owns no registers / memories.

A leaf with `registerPorts:` and no register / memory rows still
receives a router-to-leaf dispatch connection (the post-parse pass
treats `registerPorts:` as the contract). No handler block is
synthesised because there is nothing to handle.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_connections,
    projectOpen,
    render_leaf,
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
    + render_leaf('emptyLeaf')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uEmptyLeaf:  { container: top, instanceType: emptyLeaf, addressGroup: top }
"""
)


def _run():
    print("leaf with registerPorts: but no registers / memories")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Router-to-leaf bind is still emitted.
        conns = find_connections(prj, src='uAPBDecode', dst='uEmptyLeaf')
        assert len(conns) == 1, \
            f"expected exactly one uAPBDecode->uEmptyLeaf bind, got {len(conns)}"

        # No handler block was synthesised — there are no registers /
        # memories to route to one.
        offenders = [
            row.get('block') for row in prj.data['blocks'].values()
            if isinstance(row, dict) and row.get('block', '').endswith('_regs')
        ]
        assert offenders == [], \
            f"empty leaf must not produce a handler block; got {offenders}"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
