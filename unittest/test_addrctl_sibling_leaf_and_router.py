#!/usr/bin/env python3
"""T3.5: Sibling leaf and nested router under the same container.

The mid router's container holds both a leaf instance of a routed block
and a nested leaf-level router whose subtree contains another instance
of the same routed block. Verifies that mixed leaf-and-router siblings
under one container produce distinct bind sets and do not collapse —
the mid router emits a router-to-leaf bind to its sibling leaf AND a
router-to-router bind to the nested router's container.

Topology::

    uTop (top)
    +-- uAPBDecode .................. primary router
    +-- uMid (mid)
        +-- uMidDecode .............. mid router
        +-- uMyLeafMid (myLeaf, addressGroup=mid)   <- sibling leaf
        +-- uLeafLevel (leafLevel)                  <- nested subtree
            +-- uLeafDecode ......... leaf-level router
            +-- uMyLeafLeaf (myLeaf, addressGroup=leafLevel)

    uMidDecode emits two distinct binds:
        uMidDecode -> uMyLeafMid    (router-to-leaf, sibling)
        uMidDecode -> uLeafLevel    (router-to-router, container)
    The deepest leaf is dispatched only by uLeafDecode.
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
        desc: "Mid-level container (holds the sibling leaf and the nested router subtree)"
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
    print("T3.5: sibling leaf and nested router under one container")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # The mid router emits BOTH a router-to-leaf bind (sibling leaf
        # in its container) and a router-to-router bind (to the nested
        # leaf-level subtree's container). These must be distinct rows.
        mid_to_leaf = find_connections(prj, src='uMidDecode',
                                       dst='uMyLeafMid')
        mid_to_subtree = find_connections(prj, src='uMidDecode',
                                          dst='uLeafLevel')
        assert len(mid_to_leaf) == 1, \
            f"expected 1 uMidDecode->uMyLeafMid bind, got {len(mid_to_leaf)}"
        assert len(mid_to_subtree) == 1, \
            f"expected 1 uMidDecode->uLeafLevel bind, got {len(mid_to_subtree)}"
        assert mid_to_leaf[0] is not mid_to_subtree[0], \
            "sibling leaf bind and router-to-router bind must be distinct rows"

        # Deepest leaf is dispatched only by its enclosing leaf-level router.
        leaf_deep = find_connections(prj, src='uLeafDecode', dst='uMyLeafLeaf')
        assert len(leaf_deep) == 1, \
            f"expected 1 uLeafDecode->uMyLeafLeaf bind, got {len(leaf_deep)}"
        assert find_connections(prj, src='uMidDecode', dst='uMyLeafLeaf') == [], \
            "mid router must not dispatch to the deeper-level leaf instance"

        # Primary router dispatches to mid container; it must not skip
        # past mid to either the sibling leaf or the deeper subtree.
        assert len(find_connections(prj, src='uAPBDecode', dst='uMid')) == 1
        for dst in ('uMyLeafMid', 'uMyLeafLeaf', 'uLeafLevel'):
            assert find_connections(prj, src='uAPBDecode', dst=dst) == [], \
                f"primary must not skip past mid router to dispatch to '{dst}'"

        # Block-type-keyed handler: one row for the reused leaf.
        find_block(prj, 'myLeaf_regs')
        find_instance(prj, 'u_myLeaf_regs')
        handler_blocks = [
            row for _key, row in iter_rows(prj, 'blocks')
            if row.get('block') == 'myLeaf_regs'
        ]
        assert len(handler_blocks) == 1

        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uMyLeafMid', 'uMyLeafLeaf', 'uMid', 'uLeafLevel'):
            key, _ = find_instance(prj, simple)
            assert key in instances_with_regapb, \
                f"INSTANCES_WITH_REGAPB missing '{key}'"

        assert_no_global_register_binds(prj)
        print("PASS: T3.5")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
