#!/usr/bin/env python3
"""T3.2: Primary router with two nested routers at the same level.

Fan-out shape: a single primary dispatches to two independent nested
subtrees, each carrying its own router and routed leaf. Asserts that
neither nested router is parented by the other (each is a direct child
of the primary) and that leaf binds terminate at the nearest nested
router.

Topology::

    uTop (top)
    +-- uAPBDecode ........... primary router
    +-- uSubA (subA)                         +-- uSubB (subB)
    |   +-- uSubADecode ...... subA router   |   +-- uSubBDecode ... subB router
    |   +-- uLeafA           (addressGroup=  |   +-- uLeafB        (addressGroup=
    |                          subA)         |                       subB)

    Primary dispatches to both subtree containers:
        uAPBDecode -> uSubA
        uAPBDecode -> uSubB
    No cross-subtree binds (uSubADecode never reaches uLeafB / uSubB,
    and vice versa); leaf binds come from the local nested router only.
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
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Primary container"
        hasMdl: true
    subA:
        desc: "First nested subtree container"
        hasMdl: true
    subB:
        desc: "Second nested subtree container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('subADecode', 'subA')
    + render_router('subBDecode', 'subB')
    + render_leaf('leafA')
    + render_leaf('leafB')
    + """
instances:
    uTop:         { container: top, instanceType: top }
    uAPBDecode:   { container: top, instanceType: apbDecode }
    uSubA:        { container: top, instanceType: subA }
    uSubB:        { container: top, instanceType: subB }
    uSubADecode:  { container: subA, instanceType: subADecode }
    uSubBDecode:  { container: subB, instanceType: subBDecode }
    uLeafA:       { container: subA, instanceType: leafA, addressGroup: subA }
    uLeafB:       { container: subB, instanceType: leafB, addressGroup: subB }

registers:
    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "" }
    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("T3.2: primary router with two nested routers (fan-out)")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Primary dispatches to both nested subtree containers.
        assert len(find_connections(prj, src='uAPBDecode', dst='uSubA')) == 1, \
            "expected uAPBDecode->uSubA dispatch"
        assert len(find_connections(prj, src='uAPBDecode', dst='uSubB')) == 1, \
            "expected uAPBDecode->uSubB dispatch"

        # Nested routers must not dispatch to each other (no cross-link
        # between sibling subtrees).
        for src, dst in (
            ('uSubADecode', 'uSubB'),
            ('uSubBDecode', 'uSubA'),
            ('uSubADecode', 'uLeafB'),
            ('uSubBDecode', 'uLeafA'),
        ):
            assert find_connections(prj, src=src, dst=dst) == [], \
                f"unexpected cross-subtree bind {src}->{dst}"

        # Router-to-leaf bind from the leaf's local nested router only.
        assert len(find_connections(prj, src='uSubADecode', dst='uLeafA')) == 1
        assert len(find_connections(prj, src='uSubBDecode', dst='uLeafB')) == 1

        # Primary must not skip past the nested router to the leaves.
        for dst in ('uLeafA', 'uLeafB'):
            assert find_connections(prj, src='uAPBDecode', dst=dst) == [], \
                f"primary must not dispatch directly to {dst}"

        # Handler blocks for both leaves.
        find_block(prj, 'leafA_regs')
        find_block(prj, 'leafB_regs')
        find_instance(prj, 'u_leafA_regs')
        find_instance(prj, 'u_leafB_regs')

        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        for simple in ('uSubA', 'uSubB', 'uLeafA', 'uLeafB'):
            key, _ = find_instance(prj, simple)
            assert key in instances_with_regapb, \
                f"INSTANCES_WITH_REGAPB missing '{key}'"

        assert_no_global_register_binds(prj)
        print("PASS: T3.2")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
