#!/usr/bin/env python3
"""Register bus reaching a single consumer through a router-less container.

A container with no `addressBlock:` router of its own may still sit between
a router and the one register consumer it holds: the container gets a
synthesised boundary port and `connectionMaps` row feeding that consumer,
and the outer router dispatches to the container's own instance exactly as
it would to a leaf.
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


def _run_boundary_key_distinct_from_leaf_register():
    label = ("top-down leaf behind an authored boundary 'regs' keeps its "
             "register 'cfgA' and bus port 'regs' distinct")
    print(label)
    ARCH_YAML = (
        APB_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container carrying the router"
        hasMdl: true
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + render_leaf('wrap')
        + render_plain_block('leaf')
        + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uLeaf:      { container: wrap, instanceType: leaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfgA, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
    )
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        leaf_key, _ = find_block(prj, 'leaf')
        leaf = prj.getBlockData(leaf_key)
        assert leaf['registerBusPort'] == 'regs', \
            f"leaf registerBusPort expected 'regs', got {leaf['registerBusPort']!r}"
        leaf_bus = leaf['ports']['connectionMaps']['regs']
        assert leaf_bus['connection']['interface'] == 'apbReg', \
            f"leaf bus port 'regs' expected interface 'apbReg', got {leaf_bus['connection']['interface']!r}"
        assert 'cfgA' not in leaf['ports']['connectionMaps'], \
            "the register name must not appear as a register-bus port on the leaf"

        handler_key, _ = find_block(prj, 'leaf_regs')
        handler = prj.getBlockData(handler_key)
        assert list(handler['ports']['connectionMaps']) == ['regs'], \
            f"handler bus ports expected ['regs'], got {list(handler['ports']['connectionMaps'])}"
        assert list(handler['ports']['registers']) == ['cfgA'], \
            f"handler register ports expected ['cfgA'], got {list(handler['ports']['registers'])}"
        print("PASS")
        return True
    finally:
        cleanup(paths)


def _run_authored_boundary_keeps_its_interface():
    label = ("authored passthrough boundary keeps its own interface over a "
             "compatible inner reusable IP interface")
    print(label)
    ARCH_YAML = (
        APB_PREAMBLE
        + """    ipReg:
        desc: "32-bit register bus of the inner IP"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }

blocks:
    top:
        desc: "Top container carrying the router"
        hasMdl: true
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + render_leaf('wrap')
        + render_leaf('leaf', interface='ipReg')
        + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uLeaf:      { container: wrap, instanceType: leaf }

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
        boundary_maps = find_connection_maps(prj, instance='uLeaf')
        assert len(boundary_maps) == 1, \
            f"expected 1 boundary connectionMap onto uLeaf, got {len(boundary_maps)}"
        assert boundary_maps[0]['interface'] == 'apbReg', \
            f"boundary connectionMap interface expected 'apbReg', got {boundary_maps[0]['interface']!r}"

        # The container's boundary port carries its authored interface and
        # bridges to the inner IP's own interface inside the container.
        wrap_key, _ = find_block(prj, 'wrap')
        wrap = prj.getBlockData(wrap_key)
        wrap_port = wrap['ports']['connections']['regs']
        assert wrap_port['connection']['interfaceKey'].startswith('apbReg/'), \
            f"wrap port 'regs' expected interface apbReg, got {wrap_port['connection']['interfaceKey']!r}"
        wrap_map = next(iter(wrap['connectionMaps'].values()))
        assert wrap_map['crossInterface']['parentInterface'] == 'apbReg', \
            f"wrap map parent side expected 'apbReg', got {wrap_map['crossInterface']['parentInterface']!r}"
        assert wrap_map['crossInterface']['childInterface'] == 'ipReg', \
            f"wrap map child side expected 'ipReg', got {wrap_map['crossInterface']['childInterface']!r}"

        # The inner IP keeps its own interface on its register-bus port.
        leaf_key, _ = find_block(prj, 'leaf')
        leaf = prj.getBlockData(leaf_key)
        leaf_port = leaf['ports']['connectionMaps']['regs']
        assert leaf_port['connection']['interface'] == 'ipReg', \
            f"leaf port 'regs' expected interface 'ipReg', got {leaf_port['connection']['interface']!r}"
        print("PASS")
        return True
    finally:
        cleanup(paths)


def _run_inferring_container_bridges_compatible_ip():
    label = ("passthrough container with no registerPorts: carries the "
             "router's interface over a compatible inner IP interface")
    print(label)
    ARCH_YAML = (
        APB_PREAMBLE
        + """    ipReg:
        desc: "32-bit register bus of the inner IP"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }

blocks:
    top:
        desc: "Top container carrying the router"
        hasMdl: true
    wrap:
        desc: "Router-less container, no registerPorts:"
        hasMdl: true
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + render_leaf('leaf', interface='ipReg')
        + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uLeaf:      { container: wrap, instanceType: leaf }

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
        boundary_maps = find_connection_maps(prj, instance='uLeaf')
        assert len(boundary_maps) == 1 and boundary_maps[0]['interface'] == 'apbReg', \
            f"expected one boundary connectionMap on apbReg, got {boundary_maps}"
        wrap_key, _ = find_block(prj, 'wrap')
        wrap = prj.getBlockData(wrap_key)
        wrap_port = wrap['ports']['connections']['apbReg']
        assert wrap_port['connection']['interfaceKey'].startswith('apbReg/'), \
            f"wrap port expected interface apbReg, got {wrap_port['connection']['interfaceKey']!r}"
        wrap_map = next(iter(wrap['connectionMaps'].values()))
        assert wrap_map['crossInterface']['childInterface'] == 'ipReg', \
            f"wrap map child side expected 'ipReg', got {wrap_map['crossInterface']['childInterface']!r}"
        leaf_key, _ = find_block(prj, 'leaf')
        leaf = prj.getBlockData(leaf_key)
        leaf_port = leaf['ports']['connectionMaps']['regs']
        assert leaf_port['connection']['interface'] == 'ipReg', \
            f"leaf port expected interface 'ipReg', got {leaf_port['connection']['interface']!r}"
        print("PASS")
        return True
    finally:
        cleanup(paths)


def _register_port_only_leaf_design(preamble, wrap, leaf, uwrap):
    return (
        preamble
        + """
blocks:
    top:
        desc: "Top container carrying the router"
        hasMdl: true
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + wrap
        + leaf
        + f"""
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    {uwrap}
    uLeaf:      {{ container: wrap, instanceType: leaf }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}
"""
    )


def _run_register_port_only_leaf_keeps_its_interface():
    label = ("registerPorts:-only inner IP, with no registers or memories, "
             "keeps its own interface behind an authored boundary")
    print(label)
    ARCH_YAML = _register_port_only_leaf_design(
        APB_PREAMBLE + """    ipReg:
        desc: "32-bit register bus of the inner IP"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
""",
        render_leaf('wrap'), render_leaf('leaf', interface='ipReg'),
        "uWrap:      { container: top, instanceType: wrap, addressGroup: top }")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        wrap_key, _ = find_block(prj, 'wrap')
        wrap = prj.getBlockData(wrap_key)
        wrap_map = next(iter(wrap['connectionMaps'].values()))
        assert wrap_map['crossInterface']['parentInterface'] == 'apbReg' \
            and wrap_map['crossInterface']['childInterface'] == 'ipReg', \
            f"expected an apbReg-to-ipReg thunker in wrap, got {wrap_map.get('crossInterface')}"
        leaf_key, _ = find_block(prj, 'leaf')
        leaf = prj.getBlockData(leaf_key)
        leaf_port = leaf['ports']['connectionMaps']['regs']
        assert leaf_port['connection']['interface'] == 'ipReg', \
            f"leaf port expected interface 'ipReg', got {leaf_port['connection']['interface']!r}"
        print("PASS")
        return True
    finally:
        cleanup(paths)


# A register bus stays fixed-width, so a parameterised container carries its
# parameter on a non-bus port. Its bus, wrapReg, is fixed-width but named
# apart from the leaf's apbReg, so the leaf keeping its own interface is
# still observable.
PARAMETERISED_WRAP_PREAMBLE = (
    """ipParameters:
    constants:
        SAMPLE_WIDTH: { value: 16, maxValue: 32, desc: "Sample payload width" }
    types:
        samplePixelT: { width: SAMPLE_WIDTH, maxBitwidth: 32, desc: "Parameterised sample word" }

"""
    + APB_PREAMBLE
    .replace("types:\n", "types:\n"
             "    sampleTagT: { width: 8, desc: \"Sample tag\" }\n", 1)
    .replace("structures:\n", "structures:\n"
             "    sampleSt:\n"
             "        tag:  { varType: sampleTagT, desc: \"Sample tag\" }\n"
             "        data: { varType: samplePixelT, desc: \"Parameterised payload\" }\n", 1)
    + """    wrapReg:
        desc: "The container's own fixed-width register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    sampleIf:
        desc: "Parameterised sample stream, not a register bus"
        interfaceType: push_ack
        structures:
            - { structure: sampleSt, structureType: data_t }
"""
)


def _run_register_port_only_leaf_behind_parameterised_container():
    label = ("registerPorts:-only inner IP behind a parameterised container "
             "keeps its own non-parameterised interface")
    print(label)
    # _register_port_only_leaf_design's topology plus a sink for wrap's sample
    # port, bound at the same variant so the channel between them agrees.
    ARCH_YAML = (
        PARAMETERISED_WRAP_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container carrying the router; model-only, so its unparameterised module never names the sample payload"
        hasMdl: true
        hasRtl: false
    wrap:
        desc: "Parameterised router-less container"
        hasMdl: true
        params: [SAMPLE_WIDTH]
        registerPorts:
            regs: { interface: wrapReg }
        ports:
            sample: { interface: sampleIf, direction: src }
    snk:
        desc: "Consumer of wrap's parameterised sample port"
        hasMdl: true
        params: [SAMPLE_WIDTH]
        ports:
            sample: { interface: sampleIf, direction: dst }
"""
        + render_plain_block('cpu')
        + render_router('apbDecode', 'top')
        + render_leaf('leaf')
        + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top, variant: v32 }
    uSnk:       { container: top, instanceType: snk, variant: v32 }
    uLeaf:      { container: wrap, instanceType: leaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }
    - { interface: sampleIf, src: uWrap, srcport: sample, dst: uSnk, dstport: sample }

parameters:
    wrap:
        v32:
            SAMPLE_WIDTH: 32
    snk:
        v32:
            SAMPLE_WIDTH: 32
"""
    )
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        _wrap_key, wrap_row = find_block(prj, 'wrap')
        assert wrap_row['isParameterizable'], "wrap must be parameterizable"
        leaf_key, leaf_row = find_block(prj, 'leaf')
        assert not leaf_row['isParameterizable'], \
            "leaf must not be parameterizable: its surface is its own apbReg"
        leaf = prj.getBlockData(leaf_key)
        leaf_port = leaf['ports']['connectionMaps']['regs']
        assert leaf_port['connection']['interface'] == 'apbReg', \
            f"leaf port expected interface 'apbReg', got {leaf_port['connection']['interface']!r}"
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
        _run_boundary_key_distinct_from_leaf_register(),
        _run_authored_boundary_keeps_its_interface(),
        _run_inferring_container_bridges_compatible_ip(),
        _run_register_port_only_leaf_keeps_its_interface(),
        _run_register_port_only_leaf_behind_parameterised_container(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
