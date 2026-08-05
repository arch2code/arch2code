#!/usr/bin/env python3
"""Primary router has no direct leaves; all leaves under nested router.

Asserts the primary router emits a parent-to-child router bind but no
router-to-leaf binds, and that the nested router emits binds to its own
leaves only.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
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
        desc: "Primary container"
        hasMdl: true
    sub:
        desc: "Nested router container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('subDecode', 'sub')
    + render_leaf('subLeafA')
    + render_leaf('subLeafB')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uSub:        { container: top, instanceType: sub }
    uSubDecode:  { container: sub, instanceType: subDecode }
    uSubLeafA:   { container: sub, instanceType: subLeafA, addressGroup: sub }
    uSubLeafB:   { container: sub, instanceType: subLeafB, addressGroup: sub }

registers:
    - { register: cfgA, regType: rw, block: subLeafA, structure: cfgRegSt, desc: "" }
    - { register: cfgB, regType: rw, block: subLeafB, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("primary router with no direct leaves")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # The primary router's only emitted bind is to the nested
        # router's container sibling (uSub). No router-to-leaf binds at
        # the primary level.
        primary_outbound = find_connections(prj, src='uAPBDecode')
        for c in primary_outbound:
            assert c.get('dst') == 'uSub', \
                f"uAPBDecode must only dispatch to uSub; got dst='{c.get('dst')}'"
        assert any(c.get('dst') == 'uSub' for c in primary_outbound), \
            "expected uAPBDecode->uSub bind"

        # The nested router fans out to both leaves under it.
        nested_outbound = find_connections(prj, src='uSubDecode')
        nested_dsts = sorted(c.get('dst') for c in nested_outbound)
        assert nested_dsts == ['uSubLeafA', 'uSubLeafB'], \
            f"nested router must dispatch to both leaves; got {nested_dsts}"

        # INSTANCES_WITH_REGAPB excludes uTop (the container) but
        # includes uSub (router-to-router target) and both leaves.
        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uSub', 'uSubLeafA', 'uSubLeafB'):
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
