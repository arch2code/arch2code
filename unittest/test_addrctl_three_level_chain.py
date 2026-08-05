#!/usr/bin/env python3
"""Primary -> mid-level nested router -> leaf-level nested router -> leaves.

Exercises the recursive parent walk in `_findRouterParent` across two
router-to-router hops. Asserts a router-to-router connection at each
hop, router-to-leaf binds at the deepest level, and that the parent of
the leaf-level router resolves to the mid-level router rather than the
primary.

Topology::

    uTop (top)
    +-- uAPBDecode ........... primary router
    +-- uMid (mid)
        +-- uMidDecode ....... mid router
        +-- uLeafLevel (leafLevel)
            +-- uLeafDecode .. leaf-level router
            +-- uLeafA (leafA, addressGroup=leafLevel)
            +-- uLeafB (leafB, addressGroup=leafLevel)

    Router-to-router binds (one per hop):
        uAPBDecode  -> uMid
        uMidDecode  -> uLeafLevel
    Router-to-leaf binds emitted only by the deepest router:
        uLeafDecode -> uLeafA, uLeafDecode -> uLeafB
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_block,
    find_connection_maps,
    find_connections,
    find_instance,
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
        desc: "Mid-level container (hosts mid router + leaf-level subtree)"
        hasMdl: true
    leafLevel:
        desc: "Leaf-level container (hosts leaf router + routed leaves)"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('midDecode', 'mid')
    + render_router('leafDecode', 'leafLevel')
    + render_leaf('leafA')
    + render_leaf('leafB')
    + """
instances:
    uTop:         { container: top, instanceType: top }
    uAPBDecode:   { container: top, instanceType: apbDecode }
    uMid:         { container: top, instanceType: mid }
    uMidDecode:   { container: mid, instanceType: midDecode }
    uLeafLevel:   { container: mid, instanceType: leafLevel }
    uLeafDecode:  { container: leafLevel, instanceType: leafDecode }
    uLeafA:       { container: leafLevel, instanceType: leafA, addressGroup: leafLevel }
    uLeafB:       { container: leafLevel, instanceType: leafB, addressGroup: leafLevel }

registers:
    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "" }
    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("three-level chain (primary -> mid -> leaf-level)")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Router-to-router connection at each hop. The parent dispatches
        # to the *container sibling* (uMid, uLeafLevel), not directly to
        # the nested decoder.
        top_to_mid = find_connections(prj, src='uAPBDecode', dst='uMid')
        mid_to_leaf = find_connections(prj, src='uMidDecode', dst='uLeafLevel')
        assert len(top_to_mid) == 1, \
            f"expected 1 uAPBDecode->uMid bind, got {len(top_to_mid)}"
        assert len(mid_to_leaf) == 1, \
            f"expected 1 uMidDecode->uLeafLevel bind, got {len(mid_to_leaf)}"

        # The leaf-level router must NOT be parented by the primary;
        # the recursive walk picks the nearest enclosing router (mid).
        primary_to_leaf_router = find_connections(prj, src='uAPBDecode',
                                                  dst='uLeafLevel')
        assert primary_to_leaf_router == [], (
            "primary router must not dispatch directly to the leaf-level "
            f"router's container; got {primary_to_leaf_router}"
        )

        # Router-to-leaf binds emitted by the leaf-level router only.
        leaf_a = find_connections(prj, src='uLeafDecode', dst='uLeafA')
        leaf_b = find_connections(prj, src='uLeafDecode', dst='uLeafB')
        assert len(leaf_a) == 1, \
            f"expected 1 uLeafDecode->uLeafA bind, got {len(leaf_a)}"
        assert len(leaf_b) == 1, \
            f"expected 1 uLeafDecode->uLeafB bind, got {len(leaf_b)}"

        # Neither leaf is dispatched from the primary or the mid router.
        for src in ('uAPBDecode', 'uMidDecode'):
            for dst in ('uLeafA', 'uLeafB'):
                assert find_connections(prj, src=src, dst=dst) == [], (
                    f"unexpected {src}->{dst} bind; routing must terminate "
                    "at the nearest enclosing router"
                )

        # Container-boundary connectionMaps for each nested router.
        assert any(cm.get('port') == 'apbReg'
                   for cm in find_connection_maps(prj, instance='uMidDecode'))
        assert any(cm.get('port') == 'apbReg'
                   for cm in find_connection_maps(prj, instance='uLeafDecode'))

        # Handler synthesis: one per leaf block.
        find_block(prj, 'leafA_regs')
        find_block(prj, 'leafB_regs')
        find_instance(prj, 'u_leafA_regs')
        find_instance(prj, 'u_leafB_regs')

        # INSTANCES_WITH_REGAPB includes the two leaves plus both
        # container siblings the parent routers dispatch to.
        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uMid', 'uLeafLevel', 'uLeafA', 'uLeafB'):
            key, _ = find_instance(prj, simple)
            assert key in instances_with_regapb, \
                f"INSTANCES_WITH_REGAPB missing '{key}'"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
