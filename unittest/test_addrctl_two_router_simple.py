#!/usr/bin/env python3
"""Primary router, one nested router, one leaf under each.

Asserts the post-parse pass identifies the primary router by hierarchy
walk, emits a parent-to-child router connection, and emits
router-to-leaf binds for both leaves. The nested router lives inside a
container block whose own boundary carries the connectionMap into the
nested decoder.
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
        desc: "Primary router container"
        hasMdl: true
    sub:
        desc: "Nested router container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('subDecode', 'sub')
    + render_leaf('topLeaf')
    + render_leaf('subLeaf')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uSub:        { container: top, instanceType: sub }
    uSubDecode:  { container: sub, instanceType: subDecode }
    uTopLeaf:    { container: top, instanceType: topLeaf, addressGroup: top }
    uSubLeaf:    { container: sub, instanceType: subLeaf, addressGroup: sub }

registers:
    - { register: cfgT, regType: rw, block: topLeaf, structure: cfgRegSt, desc: "" }
    - { register: cfgS, regType: rw, block: subLeaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("primary + one nested router, one leaf under each")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Router-to-leaf binds, one per leaf, sourced by the leaf's parent router.
        top_to_leaf = find_connections(prj, src='uAPBDecode', dst='uTopLeaf')
        sub_to_leaf = find_connections(prj, src='uSubDecode', dst='uSubLeaf')
        assert len(top_to_leaf) == 1, \
            f"expected 1 uAPBDecode->uTopLeaf bind, got {len(top_to_leaf)}"
        assert len(sub_to_leaf) == 1, \
            f"expected 1 uSubDecode->uSubLeaf bind, got {len(sub_to_leaf)}"

        # Parent-to-child router connection: parent uAPBDecode dispatches
        # to the nested router's container sibling (uSub), not directly to
        # uSubDecode (see postParseRegisterPorts.py routing convention).
        router_to_router = find_connections(prj, src='uAPBDecode', dst='uSub')
        assert len(router_to_router) == 1, \
            f"expected 1 uAPBDecode->uSub bind, got {len(router_to_router)}"

        # Container boundary connectionMap routes the inherited upstream
        # interface into the nested decoder instance.
        cmaps = find_connection_maps(prj, instance='uSubDecode')
        assert any(cm.get('port') == 'apbReg' for cm in cmaps), \
            f"missing nested-router upstream connectionMap; got {cmaps}"

        # Synthesised handlers exist for both leaves.
        find_block(prj, 'topLeaf_regs')
        find_block(prj, 'subLeaf_regs')
        find_instance(prj, 'u_topLeaf_regs')
        find_instance(prj, 'u_subLeaf_regs')

        # INSTANCES_WITH_REGAPB lists both leaves and the nested router's
        # container sibling.
        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uTopLeaf', 'uSubLeaf', 'uSub'):
            key, _ = find_instance(prj, simple)
            assert key in instances_with_regapb, \
                f"INSTANCES_WITH_REGAPB missing '{key}'; got {instances_with_regapb}"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
