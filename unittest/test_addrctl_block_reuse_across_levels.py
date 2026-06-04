#!/usr/bin/env python3
"""T3.4: One register-bearing block reused at three different depths.

The canonical multi-level reuse case. A single routed-leaf block
(`myLeaf`) is instantiated three times — once in the primary router's
container, once in the mid router's container, and once in the
leaf-level router's container. Asserts that handler-block / handler-
instance synthesis is keyed on the block type (one handler, not three)
while router-to-leaf dispatch is per-instance (three distinct binds,
each sourced by a different parent router).

Topology::

    uTop (top)
    +-- uAPBDecode .................... primary router
    +-- uMyLeafTop (myLeaf @ top) <----- dispatched by uAPBDecode
    +-- uMid (mid)
        +-- uMidDecode ................ mid router
        +-- uMyLeafMid (myLeaf @ mid) <- dispatched by uMidDecode
        +-- uLeafLevel (leafLevel)
            +-- uLeafDecode ........... leaf-level router
            +-- uMyLeafLeaf (myLeaf @ leafLevel) <- dispatched
                                                    by uLeafDecode

    Single block 'myLeaf' -> one handler block (myLeaf_regs)
    and one handler instance (u_myLeaf_regs), shared by all three
    leaf instances. Each leaf still receives its own router-to-leaf
    bind from its nearest enclosing router.
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
    iter_rows,
    projectOpen,
    render_leaf,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Primary-level container"
        hasMdl: true
    mid:
        desc: "Mid-level container"
        hasMdl: true
    leafLevel:
        desc: "Leaf-level container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('midDecode', 'mid')
    + render_router('leafDecode', 'leafLevel')
    + render_leaf('myLeaf')
    + """
instances:
    uTop:           { container: top, instanceType: top }
    uAPBDecode:     { container: top, instanceType: apbDecode }
    uMid:           { container: top, instanceType: mid }
    uMyLeafTop:     { container: top, instanceType: myLeaf, addressGroup: top }
    uMidDecode:     { container: mid, instanceType: midDecode }
    uLeafLevel:     { container: mid, instanceType: leafLevel }
    uMyLeafMid:     { container: mid, instanceType: myLeaf, addressGroup: mid }
    uLeafDecode:    { container: leafLevel, instanceType: leafDecode }
    uMyLeafLeaf:    { container: leafLevel, instanceType: myLeaf, addressGroup: leafLevel }

registers:
    - { register: cfg, regType: rw, block: myLeaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("T3.4: register-bearing block reused at three depths")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Handler block / instance is keyed by the block type, not per
        # instance: exactly one myLeaf_regs across the whole database.
        handler_blocks = [
            row for _key, row in iter_rows(prj, 'blocks')
            if row.get('block') == 'myLeaf_regs'
        ]
        assert len(handler_blocks) == 1, \
            f"expected exactly one myLeaf_regs handler block, got {len(handler_blocks)}"
        handler_instances = [
            row for _key, row in iter_rows(prj, 'instances')
            if row.get('instance') == 'u_myLeaf_regs'
        ]
        assert len(handler_instances) == 1, (
            f"expected exactly one u_myLeaf_regs handler instance, "
            f"got {len(handler_instances)}"
        )

        # Three distinct router-to-leaf binds: one per leaf instance,
        # each sourced by the leaf's nearest enclosing router.
        primary_bind = find_connections(prj, src='uAPBDecode', dst='uMyLeafTop')
        mid_bind = find_connections(prj, src='uMidDecode', dst='uMyLeafMid')
        leaf_bind = find_connections(prj, src='uLeafDecode', dst='uMyLeafLeaf')
        assert len(primary_bind) == 1, \
            f"expected 1 uAPBDecode->uMyLeafTop bind, got {len(primary_bind)}"
        assert len(mid_bind) == 1, \
            f"expected 1 uMidDecode->uMyLeafMid bind, got {len(mid_bind)}"
        assert len(leaf_bind) == 1, \
            f"expected 1 uLeafDecode->uMyLeafLeaf bind, got {len(leaf_bind)}"

        # No router skips past the nearest enclosing router to dispatch
        # to a deeper-level leaf.
        for src, dst in (
            ('uAPBDecode', 'uMyLeafMid'),
            ('uAPBDecode', 'uMyLeafLeaf'),
            ('uMidDecode', 'uMyLeafLeaf'),
            ('uMidDecode', 'uMyLeafTop'),
            ('uLeafDecode', 'uMyLeafTop'),
            ('uLeafDecode', 'uMyLeafMid'),
        ):
            assert find_connections(prj, src=src, dst=dst) == [], \
                f"unexpected cross-level bind {src}->{dst}"

        # All three handler block / instance lookups resolve to the same
        # synthesised row (sanity check that the lookup helper agrees).
        find_block(prj, 'myLeaf_regs')
        find_instance(prj, 'u_myLeaf_regs')

        # Per-instance INSTANCES_WITH_REGAPB membership: all three leaf
        # instances appear plus the router-to-router container siblings.
        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uMyLeafTop', 'uMyLeafMid', 'uMyLeafLeaf',
                       'uMid', 'uLeafLevel'):
            key, _ = find_instance(prj, simple)
            assert key in instances_with_regapb, \
                f"INSTANCES_WITH_REGAPB missing '{key}'"

        assert_no_global_register_binds(prj)
        print("PASS: T3.4")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
