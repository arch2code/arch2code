#!/usr/bin/env python3
"""Register bus reaching a single consumer through a router-less container.

A container with no `addressBlock:` router of its own may still sit between
a router and the one register consumer it holds: the container gets a
synthesised boundary port and `connectionMaps` row feeding that consumer,
and the outer router dispatches to the container's own instance exactly as
it would to a leaf. Four variants: a reusable-IP leaf fed this way, a
top-down leaf inferring its register bus through the same path, a two-level
chain of router-less containers, and a block reused both directly under a
router and through a passthrough container.
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
    iter_rows,
    projectOpen,
    render_leaf,
    render_plain_block,
    render_router,
)


def _run_single_consumer():
    label = "reusable-IP leaf fed through a router-less passthrough container"
    print(label)
    ARCH_YAML = (
        APB_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container carrying the router"
        hasMdl: true
    unservedContainer:
        desc: "Container with no local router"
        hasMdl: true
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + render_leaf('leaf')
        + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uIsolated:  { container: top, instanceType: unservedContainer, addressGroup: top }
    uLeafLost:  { container: unservedContainer, instanceType: leaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
    )
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # The router dispatches to the container's own instance, not to the
        # inner consumer directly.
        dispatch = find_connections(prj, src='uAPBDecode', dst='uIsolated')
        assert len(dispatch) == 1, \
            f"expected 1 uAPBDecode->uIsolated bind, got {len(dispatch)}"
        assert dispatch[0].get('dstport') == 'apbReg', \
            f"dispatch dstport expected 'apbReg', got {dispatch[0].get('dstport')}"
        assert dispatch[0].get('srcport') == 'apbReg_uIsolated', \
            f"dispatch srcport expected 'apbReg_uIsolated', got {dispatch[0].get('srcport')}"
        assert find_connections(prj, dst='uLeafLost') == [], \
            "the inner consumer must not receive a direct router dispatch"

        # Boundary connectionMap bridging the container's own port to the
        # inner consumer's registerPorts: port.
        boundary_maps = find_connection_maps(prj, instance='uLeafLost')
        assert len(boundary_maps) == 1, \
            f"expected 1 boundary connectionMap onto uLeafLost, got {len(boundary_maps)}"
        cm = boundary_maps[0]
        assert cm.get('block') == 'unservedContainer', \
            f"boundary connectionMap block expected 'unservedContainer', got {cm.get('block')}"
        assert cm.get('port') == 'apbReg', \
            f"boundary connectionMap port expected 'apbReg', got {cm.get('port')}"
        assert cm.get('instancePort') == 'regs', \
            f"boundary connectionMap instancePort expected 'regs', got {cm.get('instancePort')}"

        # Handler synthesis is unaffected by the passthrough.
        find_block(prj, 'leaf_regs')
        find_instance(prj, 'u_leaf_regs')
        assert find_connection_maps(prj, instance='u_leaf_regs'), \
            "expected a leaf-to-handler connectionMap"

        # INSTANCES_WITH_REGAPB names the routed slot (the container's own
        # instance), not the inner consumer.
        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        isolated_key, isolated_row = find_instance(prj, 'uIsolated')
        leaf_lost_key, _ = find_instance(prj, 'uLeafLost')
        assert isolated_key in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB missing '{isolated_key}'"
        assert leaf_lost_key not in instances_with_regapb, \
            "INSTANCES_WITH_REGAPB must not name the inner consumer"

        assert_no_global_register_binds(prj)

        # Address decode: the container's own instance carries the router's
        # addressGroup/addressID; the inner consumer carries neither.
        assert isolated_row.get('addressGroup') == 'top', \
            f"uIsolated addressGroup expected 'top', got {isolated_row.get('addressGroup')}"
        assert isinstance(isolated_row.get('addressID'), int), \
            f"uIsolated addressID expected an int, got {isolated_row.get('addressID')!r}"

        router_key, _ = find_block(prj, 'apbDecode')
        data = prj.getBlockData(router_key)
        from templates.systemc.constructor import addressDecoder
        rendered = "\n".join(addressDecoder(None, prj, data))
        assert '&apbReg_uIsolated' in rendered, \
            f"expected '&apbReg_uIsolated' in rendered decoder table:\n{rendered}"
        assert 'apbReg_uLeafLost' not in rendered, \
            f"the inner consumer must not appear in the decoder table:\n{rendered}"

        print("PASS")
        return True
    finally:
        cleanup(paths)


def _run_top_down_inner_leaf():
    label = "top-down leaf inferring its register bus through a passthrough container"
    print(label)
    ARCH_YAML = (
        APB_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container carrying the router"
        hasMdl: true
    wrapTD:
        desc: "Router-less container, top-down inner leaf"
        hasMdl: true
    innerLeaf:
        desc: "Top-down leaf owning a register, no registerPorts:"
        hasMdl: true
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + """
instances:
    uTop:        { container: top, instanceType: top }
    uCPU:        { container: top, instanceType: cpu }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uWrapTD:     { container: top, instanceType: wrapTD, addressGroup: top }
    uInnerLeaf:  { container: wrapTD, instanceType: innerLeaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfg, regType: rw, block: innerLeaf, structure: cfgRegSt, desc: "" }
"""
    )
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        dispatch = find_connections(prj, src='uAPBDecode', dst='uWrapTD')
        assert len(dispatch) == 1, \
            f"expected 1 uAPBDecode->uWrapTD bind, got {len(dispatch)}"
        assert find_connections(prj, dst='uInnerLeaf') == [], \
            "the top-down inner leaf must not receive a direct router dispatch"

        boundary_maps = find_connection_maps(prj, instance='uInnerLeaf')
        assert len(boundary_maps) == 1, \
            f"expected 1 boundary connectionMap onto uInnerLeaf, got {len(boundary_maps)}"
        cm = boundary_maps[0]
        assert cm.get('block') == 'wrapTD', \
            f"boundary connectionMap block expected 'wrapTD', got {cm.get('block')}"
        assert cm.get('port') == 'apbReg', \
            f"boundary connectionMap port expected 'apbReg', got {cm.get('port')}"
        assert cm.get('instancePort') == 'apbReg', \
            f"boundary connectionMap instancePort (top-down inferred) expected 'apbReg', got {cm.get('instancePort')}"

        find_block(prj, 'innerLeaf_regs')
        find_instance(prj, 'u_innerLeaf_regs')

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def _run_two_level_chain():
    label = "two-level chain of router-less containers (leaf -> C1 -> C2 -> router)"
    print(label)
    ARCH_YAML = (
        APB_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container carrying the router"
        hasMdl: true
    c2:
        desc: "Outer router-less container"
        hasMdl: true
    c1:
        desc: "Inner router-less container"
        hasMdl: true
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + render_leaf('chainLeaf')
        + """
instances:
    uTop:        { container: top, instanceType: top }
    uCPU:        { container: top, instanceType: cpu }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uC2:         { container: top, instanceType: c2, addressGroup: top }
    uC1:         { container: c2, instanceType: c1 }
    uChainLeaf:  { container: c1, instanceType: chainLeaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfg, regType: rw, block: chainLeaf, structure: cfgRegSt, desc: "" }
"""
    )
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Only the outermost container is dispatched to directly.
        dispatch = find_connections(prj, src='uAPBDecode', dst='uC2')
        assert len(dispatch) == 1, \
            f"expected 1 uAPBDecode->uC2 bind, got {len(dispatch)}"
        for dst in ('uC1', 'uChainLeaf'):
            assert find_connections(prj, dst=dst) == [], \
                f"'{dst}' must not receive a direct router dispatch"

        # A boundary connectionMap at each passthrough level.
        c2_maps = find_connection_maps(prj, instance='uC1')
        assert len(c2_maps) == 1, \
            f"expected 1 boundary connectionMap onto uC1, got {len(c2_maps)}"
        assert c2_maps[0].get('block') == 'c2', \
            f"uC1's boundary connectionMap block expected 'c2', got {c2_maps[0].get('block')}"

        c1_maps = find_connection_maps(prj, instance='uChainLeaf')
        assert len(c1_maps) == 1, \
            f"expected 1 boundary connectionMap onto uChainLeaf, got {len(c1_maps)}"
        assert c1_maps[0].get('block') == 'c1', \
            f"uChainLeaf's boundary connectionMap block expected 'c1', got {c1_maps[0].get('block')}"
        assert c1_maps[0].get('instancePort') == 'regs', \
            f"uChainLeaf's boundary connectionMap instancePort expected 'regs', got {c1_maps[0].get('instancePort')}"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def _run_block_reuse():
    label = "block reused both directly under a router and through a passthrough container"
    print(label)
    ARCH_YAML = (
        APB_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container carrying the router"
        hasMdl: true
    wrapD:
        desc: "Router-less container holding the reused leaf's second instance"
        hasMdl: true
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + render_leaf('reusedLeaf')
        + """
instances:
    uTop:          { container: top, instanceType: top }
    uCPU:          { container: top, instanceType: cpu }
    uAPBDecode:    { container: top, instanceType: apbDecode }
    uLeafDirect:   { container: top, instanceType: reusedLeaf, addressGroup: top }
    uWrapD:        { container: top, instanceType: wrapD, addressGroup: top }
    uLeafViaWrap:  { container: wrapD, instanceType: reusedLeaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfg, regType: rw, block: reusedLeaf, structure: cfgRegSt, desc: "" }
"""
    )
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # One handler block/instance shared by both leaf instances.
        handler_blocks = [
            row for _key, row in iter_rows(prj, 'blocks')
            if row.get('block') == 'reusedLeaf_regs'
        ]
        assert len(handler_blocks) == 1, \
            f"expected exactly one reusedLeaf_regs handler block, got {len(handler_blocks)}"
        handler_instances = [
            row for _key, row in iter_rows(prj, 'instances')
            if row.get('instance') == 'u_reusedLeaf_regs'
        ]
        assert len(handler_instances) == 1, \
            f"expected exactly one u_reusedLeaf_regs handler instance, got {len(handler_instances)}"

        # Direct dispatch to the co-located instance, passthrough dispatch
        # to the container holding the other.
        assert len(find_connections(prj, src='uAPBDecode', dst='uLeafDirect')) == 1, \
            "expected uAPBDecode->uLeafDirect direct dispatch"
        assert len(find_connections(prj, src='uAPBDecode', dst='uWrapD')) == 1, \
            "expected uAPBDecode->uWrapD passthrough dispatch"
        assert find_connections(prj, dst='uLeafViaWrap') == [], \
            "the instance behind the passthrough container must not be dispatched to directly"

        boundary_maps = find_connection_maps(prj, instance='uLeafViaWrap')
        assert len(boundary_maps) == 1, \
            f"expected 1 boundary connectionMap onto uLeafViaWrap, got {len(boundary_maps)}"

        instances_with_regapb = prj.config.getConfig(
            'INSTANCES_WITH_REGAPB', failOk=True)
        direct_key, _ = find_instance(prj, 'uLeafDirect')
        wrap_key, _ = find_instance(prj, 'uWrapD')
        via_wrap_key, _ = find_instance(prj, 'uLeafViaWrap')
        assert direct_key in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB missing '{direct_key}'"
        assert wrap_key in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB missing '{wrap_key}'"
        assert via_wrap_key not in instances_with_regapb, \
            "INSTANCES_WITH_REGAPB must not name the instance behind the passthrough container"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    results = [
        _run_single_consumer(),
        _run_top_down_inner_leaf(),
        _run_two_level_chain(),
        _run_block_reuse(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
